"""Métriques applicatives au format Prometheus — Phase 5 (observabilité).

Registry minimaliste 100% stdlib (cohérent avec le projet : aucune dépendance native). Expose des
compteurs et histogrammes au format d'exposition Prometheus, scrapables par Prometheus/Grafana via
`GET /metrics`. Thread-safe (verrou) pour un process Uvicorn multi-tâches.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from contextlib import contextmanager

_LOCK = threading.Lock()

# Compteurs : (name, frozenset(labels)) -> valeur
_counters: dict[tuple[str, frozenset], float] = defaultdict(float)
# Histogrammes : name -> {"buckets": {le: count}, "sum": x, "count": n}
_HIST_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_hist_sum: dict[tuple[str, frozenset], float] = defaultdict(float)
_hist_count: dict[tuple[str, frozenset], int] = defaultdict(int)
_hist_buckets: dict[tuple[str, frozenset, float], int] = defaultdict(int)

_HELP: dict[str, tuple[str, str]] = {}  # name -> (type, help)


def _key(labels: dict | None) -> frozenset:
    return frozenset((labels or {}).items())


def register(name: str, kind: str, help_text: str) -> None:
    _HELP[name] = (kind, help_text)


def inc(name: str, value: float = 1.0, **labels: str) -> None:
    with _LOCK:
        _counters[(name, _key(labels))] += value
        _HELP.setdefault(name, ("counter", name))


def observe(name: str, value: float, **labels: str) -> None:
    k = (name, _key(labels))
    with _LOCK:
        _hist_sum[k] += value
        _hist_count[k] += 1
        for b in _HIST_BUCKETS:
            if value <= b:
                _hist_buckets[(name, _key(labels), b)] += 1
        _HELP.setdefault(name, ("histogram", name))


@contextmanager
def timer(name: str, **labels: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        observe(name, time.perf_counter() - start, **labels)


def _fmt_labels(items: frozenset, extra: dict | None = None) -> str:
    d = dict(items)
    if extra:
        d.update(extra)
    if not d:
        return ""
    inner = ",".join(f'{k}="{v}"' for k, v in sorted(d.items()))
    return "{" + inner + "}"


def render() -> str:
    """Sérialise toutes les métriques au format d'exposition Prometheus."""
    lines: list[str] = []
    with _LOCK:
        emitted: set[str] = set()

        def header(name: str) -> None:
            if name in emitted:
                return
            kind, help_text = _HELP.get(name, ("untyped", name))
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {kind}")
            emitted.add(name)

        for (name, labels), value in sorted(_counters.items()):
            header(name)
            lines.append(f"{name}{_fmt_labels(labels)} {value}")

        hist_names = {name for (name, _) in _hist_count}
        for name in sorted(hist_names):
            header(name)
            for (n, labels), _ in sorted(_hist_count.items()):
                if n != name:
                    continue
                cumulative = 0
                for b in _HIST_BUCKETS:
                    cumulative = _hist_buckets.get((name, labels, b), 0)
                    lines.append(f'{name}_bucket{_fmt_labels(labels, {"le": str(b)})} {cumulative}')
                total = _hist_count[(name, labels)]
                lines.append(f'{name}_bucket{_fmt_labels(labels, {"le": "+Inf"})} {total}')
                lines.append(f"{name}_sum{_fmt_labels(labels)} {_hist_sum[(name, labels)]}")
                lines.append(f"{name}_count{_fmt_labels(labels)} {total}")
    return "\n".join(lines) + "\n"


def reset() -> None:
    """Réinitialise (tests)."""
    with _LOCK:
        _counters.clear()
        _hist_sum.clear()
        _hist_count.clear()
        _hist_buckets.clear()
