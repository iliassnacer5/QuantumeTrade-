"""Service d'exécution broker (M8, Phase 4) — orchestration + garde-fous.

Collections (via store.records) :
- broker_conn : connexions broker (clés API CHIFFRÉES, mode paper/live)
- order       : ordres passés (paper ou réel)
- kyc         : statut KYC/AML par tenant

Garde-fous appliqués ici :
- les clés ne sont jamais stockées en clair (crypto.encrypt) ni renvoyées (mask) ;
- l'exécution réelle exige mode 'live' + KYC vérifié ; sinon on force/refuse le papier.
"""

from __future__ import annotations

import logging
import uuid

from app.core import crypto
from app.execution.alpaca import AlpacaBroker
from app.execution.base import OrderResult
from app.execution.paper import PaperBroker
from app.repositories.store import AppStore

logger = logging.getLogger(__name__)

CONN = "broker_conn"
ORDER = "order"
KYC = "kyc"

_SUPPORTED = {"paper", "alpaca"}


class ExecutionError(RuntimeError):
    """Erreur métier d'exécution (garde-fou non satisfait, connexion absente…)."""


# ---------------- KYC ----------------
def kyc_status(store: AppStore, tenant_id: str) -> dict:
    return store.records.get(KYC, tenant_id) or {"status": "none"}


def submit_kyc(store: AppStore, tenant_id: str, *, legal_name: str, country: str, doc_id: str) -> dict:
    # Démo : vérification automatique si les champs requis sont fournis (en prod : fournisseur KYC/AML).
    complete = bool(legal_name.strip() and country.strip() and doc_id.strip())
    status = "verified" if complete else "pending"
    return store.records.put(
        KYC, tenant_id,
        {"status": status, "legal_name": legal_name, "country": country},
        tenant_id=tenant_id,
    )


def is_kyc_verified(store: AppStore, tenant_id: str) -> bool:
    return kyc_status(store, tenant_id).get("status") == "verified"


# ---------------- Connexions broker ----------------
def connect_broker(
    store: AppStore, tenant_id: str, *, broker: str, api_key: str, api_secret: str, mode: str
) -> dict:
    if broker not in _SUPPORTED:
        raise ExecutionError(f"broker non supporté : {broker}")
    mode = "live" if mode == "live" else "paper"
    if mode == "live" and not is_kyc_verified(store, tenant_id):
        raise ExecutionError("KYC non vérifié : connexion réelle interdite (mode papier autorisé)")
    conn_id = str(uuid.uuid4())
    store.records.put(
        CONN, conn_id,
        {
            "broker": broker,
            "mode": mode,
            "api_key_enc": crypto.encrypt(api_key) if api_key else "",
            "api_secret_enc": crypto.encrypt(api_secret) if api_secret else "",
            "key_hint": crypto.mask(api_key),
        },
        tenant_id=tenant_id,
    )
    return public_connection(store.records.get(CONN, conn_id))


def public_connection(rec: dict) -> dict:
    """Vue sans secrets (pour l'API)."""
    return {
        "id": rec["id"],
        "broker": rec.get("broker"),
        "mode": rec.get("mode"),
        "key_hint": rec.get("key_hint", ""),
        "created_at": rec.get("created_at"),
    }


def list_connections(store: AppStore, tenant_id: str) -> list[dict]:
    return [public_connection(r) for r in store.records.list(CONN, tenant_id)]


def revoke_connection(store: AppStore, tenant_id: str, conn_id: str) -> bool:
    rec = store.records.get(CONN, conn_id)
    if rec is None or rec.get("tenant_id") != tenant_id:
        return False
    return store.records.delete(CONN, conn_id)


def _build_broker(rec: dict):
    broker = rec.get("broker")
    mode = rec.get("mode", "paper")
    if broker == "paper" or mode == "paper":
        return PaperBroker()
    if broker == "alpaca":
        return AlpacaBroker(
            crypto.decrypt(rec["api_key_enc"]) if rec.get("api_key_enc") else "",
            crypto.decrypt(rec["api_secret_enc"]) if rec.get("api_secret_enc") else "",
            mode="live",
        )
    raise ExecutionError(f"broker non supporté : {broker}")


# ---------------- Ordres ----------------
async def place_order(
    store: AppStore, tenant_id: str, *, conn_id: str, symbol: str, side: str, qty: float,
    stop_loss: float | None = None, take_profit: float | None = None,
) -> dict:
    if side not in {"buy", "sell"}:
        raise ExecutionError("side invalide (buy|sell)")
    if qty <= 0:
        raise ExecutionError("quantité invalide")
    rec = store.records.get(CONN, conn_id)
    if rec is None or rec.get("tenant_id") != tenant_id:
        raise ExecutionError("connexion broker introuvable")

    # Garde-fou réel : KYC obligatoire pour live ; sinon on rétrograde en papier.
    if rec.get("mode") == "live" and not is_kyc_verified(store, tenant_id):
        raise ExecutionError("KYC requis pour l'exécution réelle")

    # Garde-fou qualité des données : on refuse de trader sur des données synthétiques (démo).
    from app.core.config import get_settings
    from app.data import markets

    if get_settings().block_synthetic_orders:
        await markets.load_candles(symbol, interval="1h", limit=60)  # rafraîchit la source
        if not markets.is_real(symbol):
            raise ExecutionError(
                f"Données indisponibles ou synthétiques pour {symbol} — trade refusé. "
                "Configure une source réelle (clé broker/data) avant de trader ce marché."
            )

    broker = _build_broker(rec)
    result: OrderResult = await broker.place_order(symbol, side, qty)
    # Garde-fou portefeuille (paper) : limite le nombre de positions et l'exposition totale.
    _portfolio_check(store, tenant_id, result)
    levels = _trade_levels(result, side, stop_loss, take_profit)  # valide + calcule R/R, risque, gain
    return _persist_order(store, tenant_id, conn_id, result, levels)


def _portfolio_check(store: AppStore, tenant_id: str, result: OrderResult) -> None:
    """Refuse l'ordre si trop de positions ouvertes ou exposition totale dépassée (protection capital)."""
    from app.core.config import get_settings

    s = get_settings()
    if not s.paper_portfolio_guard:
        return
    open_orders = [
        o for o in store.records.list(ORDER, tenant_id)
        if o.get("mode") == "paper" and o.get("outcome") not in ("won", "lost")
    ]
    if len(open_orders) >= s.paper_max_positions:
        raise ExecutionError(
            f"Limite de {s.paper_max_positions} positions ouvertes atteinte — clôture-en une avant d'en ouvrir une nouvelle."
        )
    users = store.users.list_by_tenant(tenant_id)
    capital = users[0].capital if users else 0.0
    # Plafond d'exposition = celui choisi par l'utilisateur (Paramètres), sinon le défaut global.
    max_exposure = getattr(users[0], "max_exposure_pct", None) if users else None
    max_exposure = max_exposure or s.paper_max_exposure_pct
    if capital > 0:
        # Exposition = RISQUE total ouvert (ce qu'on perdrait si tous les stops sautaient), PAS le
        # notionnel. Une position dimensionnée à 1% de risque ne pèse que ~1% ici (vs un gros
        # notionnel dû au levier implicite d'un stop serré). Définition professionnelle du risque.
        open_risk = sum(float(o.get("risk_amount") or 0) for o in open_orders)
        risk_pct = open_risk / capital * 100
        if risk_pct > max_exposure:
            raise ExecutionError(
                f"Risque total ouvert {risk_pct:.0f}% > ton plafond {max_exposure:.0f}% du capital — "
                f"clôture une position ou relève le plafond dans Paramètres."
            )


def _trade_levels(result: OrderResult, side: str, stop_loss: float | None, take_profit: float | None) -> dict:
    """Valide la cohérence SL/TP vs entrée et calcule les infos du trade (R/R, risque, gain potentiel)."""
    entry = result.filled_price or 0.0
    info: dict = {
        "entry": entry, "stop_loss": stop_loss, "take_profit": take_profit,
        "risk_reward": None, "risk_amount": None, "potential_profit": None,
    }
    if not entry:
        return info
    # Cohérence directionnelle (comme un vrai bracket order).
    if side == "buy":
        if stop_loss is not None and stop_loss >= entry:
            raise ExecutionError(f"Achat : le stop loss ({stop_loss}) doit être SOUS l'entrée ({entry}).")
        if take_profit is not None and take_profit <= entry:
            raise ExecutionError(f"Achat : le take profit ({take_profit}) doit être AU-DESSUS de l'entrée ({entry}).")
    else:  # sell
        if stop_loss is not None and stop_loss <= entry:
            raise ExecutionError(f"Vente : le stop loss ({stop_loss}) doit être AU-DESSUS de l'entrée ({entry}).")
        if take_profit is not None and take_profit >= entry:
            raise ExecutionError(f"Vente : le take profit ({take_profit}) doit être SOUS l'entrée ({entry}).")

    risk_per_unit = abs(entry - stop_loss) if stop_loss is not None else None
    reward_per_unit = abs(take_profit - entry) if take_profit is not None else None
    if risk_per_unit:
        info["risk_amount"] = round(risk_per_unit * result.qty, 2)
    if reward_per_unit:
        info["potential_profit"] = round(reward_per_unit * result.qty, 2)
    if risk_per_unit and reward_per_unit:
        info["risk_reward"] = round(reward_per_unit / risk_per_unit, 2)
    return info


def _persist_order(store: AppStore, tenant_id: str, conn_id: str, result: OrderResult, levels: dict | None = None) -> dict:
    from app.core import metrics
    metrics.inc("orders_placed_total", mode=result.mode, side=result.side)
    order_id = str(uuid.uuid4())
    return store.records.put(
        ORDER, order_id,
        {
            "conn_id": conn_id,
            "broker": result.broker,
            "mode": result.mode,
            "symbol": result.symbol,
            "side": result.side,
            "qty": result.qty,
            "status": result.status,
            "filled_price": result.filled_price,
            **(levels or {}),
        },
        tenant_id=tenant_id,
    )


def list_orders(store: AppStore, tenant_id: str, limit: int = 100) -> list[dict]:
    return store.records.list(ORDER, tenant_id)[:limit]


async def check_order_outcome(store: AppStore, tenant_id: str, order_id: str) -> dict:
    """Vérifie si un trade papier a touché son TP (gagné) ou son SL (perdu) depuis l'entrée.

    Rejoue l'action du prix (cf. data/replay.py) : TP -> ``won``, SL -> ``lost``, sinon ``open``
    (P&L latent). Le résultat clôturé est PERSISTÉ sur l'ordre (statut/issue/P&L réalisé)."""
    from datetime import UTC, datetime

    from app.data import replay

    rec = store.records.get(ORDER, order_id)
    if rec is None or rec.get("tenant_id") != tenant_id:
        raise ExecutionError("ordre introuvable")
    if rec.get("outcome") in {"won", "lost"}:
        return rec  # déjà clôturé

    entry = rec.get("entry") if rec.get("entry") is not None else rec.get("filled_price")
    sl, tp = rec.get("stop_loss"), rec.get("take_profit")
    side, qty = rec.get("side"), rec.get("qty") or 0.0
    if entry is None or (sl is None and tp is None):
        return {**rec, "outcome": "open", "note": "Aucun SL/TP : vérification automatique impossible."}

    outcome, exit_price, closed_ts = await replay.replay_outcome(
        rec["symbol"], side, entry, sl, tp, rec.get("created_at"),
    )
    if outcome == "open":
        unrealized = (exit_price - entry) * qty if side == "buy" else (entry - exit_price) * qty
        return {**rec, "outcome": "open", "current_price": round(exit_price, 8), "unrealized_pnl": round(unrealized, 2)}

    realized = (exit_price - entry) * qty if side == "buy" else (entry - exit_price) * qty
    updated = {
        **rec, "outcome": outcome, "status": "closed", "exit_price": exit_price,
        "realized_pnl": round(realized, 2),
        "closed_at": datetime.fromtimestamp(closed_ts, UTC).isoformat() if closed_ts else None,
    }
    from app.core import metrics
    metrics.inc("paper_orders_closed_total", outcome=outcome)
    return store.records.put(ORDER, order_id, updated, tenant_id=tenant_id)


async def close_order_manual(store: AppStore, tenant_id: str, order_id: str) -> dict:
    """Clôture MANUELLE d'une position papier au prix du marché courant (P&L réalisé immédiat)."""
    from datetime import UTC, datetime

    from app.data import markets

    rec = store.records.get(ORDER, order_id)
    if rec is None or rec.get("tenant_id") != tenant_id:
        raise ExecutionError("ordre introuvable")
    if rec.get("outcome") in {"won", "lost"}:
        return rec  # déjà clôturé

    entry = rec.get("entry") if rec.get("entry") is not None else rec.get("filled_price")
    qty = rec.get("qty") or 0.0
    side = rec.get("side")
    candles = await markets.load_candles(rec["symbol"], interval="1h", limit=2)
    price = candles[-1].close if candles else (entry or 0.0)
    pnl = ((price - entry) if side == "buy" else (entry - price)) * qty
    outcome = "won" if pnl >= 0 else "lost"
    updated = {
        **rec, "outcome": outcome, "status": "closed", "exit_price": round(price, 8),
        "realized_pnl": round(pnl, 2), "closed_at": datetime.now(UTC).isoformat(), "closed_manually": True,
    }
    from app.core import metrics
    metrics.inc("paper_orders_closed_total", outcome=outcome)
    return store.records.put(ORDER, order_id, updated, tenant_id=tenant_id)


async def monitor_positions(store: AppStore) -> int:
    """Parcourt tous les ordres papier OUVERTS avec SL/TP et clôture ceux dont le niveau est atteint.

    Diffuse un événement temps réel + notifie l'utilisateur à chaque clôture automatique.
    Retourne le nombre d'ordres clôturés sur ce passage."""
    closed = 0
    for rec in store.records.list(ORDER):  # tous tenants
        if rec.get("mode") != "paper" or rec.get("outcome") in {"won", "lost"}:
            continue
        if rec.get("stop_loss") is None and rec.get("take_profit") is None:
            continue
        tenant_id = rec.get("tenant_id")
        try:
            res = await check_order_outcome(store, tenant_id, rec["id"])
        except Exception as exc:  # noqa: BLE001 — un ordre ne doit pas bloquer les autres
            logger.warning("Monitor position %s échoué (%s)", rec.get("id"), exc)
            continue
        if res.get("outcome") in {"won", "lost"}:
            closed += 1
            await _notify_close(store, tenant_id, res)
    return closed


async def _notify_close(store: AppStore, tenant_id: str, order: dict) -> None:
    """Diffuse la clôture auto sur le bus temps réel + push best-effort."""
    from app.realtime import bus

    verdict = "GAGNÉ ✅" if order["outcome"] == "won" else "PERDU 🔴"
    msg = f"Position {order['symbol']} clôturée auto : {verdict} (P&L {order.get('realized_pnl')})"
    try:
        await bus.publish(tenant_id, {"type": "order_closed", "data": order})
    except Exception as exc:  # noqa: BLE001
        logger.warning("Diffusion clôture échouée (%s)", exc)
    try:
        from app.alerts import notifier

        user = next((u for u in store.users.list_by_tenant(tenant_id)), None)
        if user and getattr(user, "push_token", None):
            await notifier.send_push(user.push_token, msg)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Notification clôture échouée (%s)", exc)
