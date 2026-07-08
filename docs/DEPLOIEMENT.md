# Déploiement gratuit 24/7 — Oracle Cloud « Always Free »

> Guide clic par clic pour héberger Quantum Trade AI gratuitement à vie sur une VM ARM
> Oracle (4 CPU / 24 Go RAM). Durée totale : ~1h. Aucun débit sur la carte (vérification seule).

---

## PHASE 1 — Créer le compte Oracle (~15 min)

1. Va sur **https://www.oracle.com/cloud/free/** → bouton **« Start for free »**.
2. Remplis : email, pays (**France/Maroc/etc. — réfléchis bien, voir note région**), nom → **Verify my email** → clique le lien reçu par email.
3. Choisis un **mot de passe** et un **Cloud Account Name** (ex. `quantumtrade`) — note-les.
4. **Home Region** ⚠️ IMPORTANT : choisis une région avec de la capacité ARM disponible —
   recommandé : **France Central (Paris)**, **Germany Central (Frankfurt)** ou **UK South (London)**.
   La home region est DÉFINITIVE (les ressources Always Free y vivent).
5. Adresse + numéro de téléphone (vérification SMS).
6. **Carte bancaire** : vérification uniquement (~1€ bloqué puis rendu, jamais débité). Les
   ressources « Always Free » ne peuvent PAS générer de facture tant que tu ne « upgrade » pas.
7. Accepte les conditions → **Start my free trial** → attends l'email « Your account is ready » (5-30 min).

## PHASE 2 — Créer la VM ARM (~10 min)

1. Connecte-toi sur **https://cloud.oracle.com** (Cloud Account Name → identifiants).
2. Menu ☰ (en haut à gauche) → **Compute** → **Instances** → bouton **Create instance**.
3. **Name** : `quantum-trade`.
4. Section **Image and shape** → **Edit** :
   - **Change image** → **Ubuntu** → coche **Canonical Ubuntu 22.04** (l'image aarch64 sera choisie avec le shape ARM) → Select image.
   - **Change shape** → **Ampere** → coche **VM.Standard.A1.Flex** → règle **OCPUs = 4** et **Memory = 24 GB** (c'est TOUT le quota gratuit, autant le prendre) → Select shape.
5. Section **Networking** : laisse « Create new virtual cloud network » par défaut ;
   vérifie que **« Assign a public IPv4 address »** = **Yes**.
6. Section **Add SSH keys** : choisis **Generate a key pair for me** → clique
   **⬇ Save private key** (fichier `ssh-key-….key`) ⚠️ GARDE-LE précieusement (impossible à retélécharger).
7. Section **Boot volume** : coche « Specify a custom boot volume size » → **100 GB** (le quota gratuit total est 200 GB).
8. **Create**. Attendre l'état **Running** (~1 min).
   - ⚠️ Si erreur **« Out of capacity »** : c'est fréquent sur ARM. Réessaie à un autre moment
     (tôt le matin marche souvent), ou change l'Availability Domain (AD-1/2/3) en haut du formulaire.
9. Note l'**adresse IP publique** affichée sur la page de l'instance → appelons-la `IP_VM`.

## PHASE 3 — Ouvrir les ports (~5 min)

**Côté Oracle (pare-feu réseau) :**
1. Sur la page de l'instance → clique le lien de la **subnet** (section Instance details).
2. **Security Lists** → clique **Default Security List** → **Add Ingress Rules** :
   - Règle 1 : Source CIDR `0.0.0.0/0` · IP Protocol **TCP** · Destination Port Range **3000** → Add.
   - Refais **Add Ingress Rules** pour le port **8080**.

## PHASE 4 — Se connecter en SSH (depuis ton PC Windows)

Dans PowerShell (adapte le chemin de la clé téléchargée) :
```powershell
ssh -i "C:\Users\ilias\Downloads\ssh-key-XXXX.key" ubuntu@IP_VM
```
(Si « permissions too open » : clic droit sur le fichier → Propriétés → Sécurité → n'autoriser que ton utilisateur.)

## PHASE 5 — Installer Docker + ouvrir le pare-feu Ubuntu (~5 min)

Copie-colle ces blocs dans la session SSH :
```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu

# ⚠️ Pare-feu INTERNE d'Ubuntu Oracle (bloque tout sauf SSH par défaut) :
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 3000 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8080 -j ACCEPT
sudo apt-get update && sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save

# Recharge le groupe docker
exit
```
Puis **reconnecte-toi en SSH** (même commande qu'en Phase 4).

## PHASE 6 — Récupérer le projet

**Option recommandée : GitHub privé** (sur ton PC, une fois) :
```powershell
cd c:\Users\ilias\.gemini\antigravity-ide\scratch\QuantumTradingPlateforme
# crée un repo PRIVÉ "quantum-trade" sur github.com puis :
git add -A ; git commit -m "deploy"
git remote add origin https://github.com/TON_USER/quantum-trade.git
git push -u origin main   # (ou signal-quality selon ta branche)
```
Sur la VM :
```bash
git clone https://github.com/TON_USER/quantum-trade.git
cd quantum-trade
```
*(Alternative sans GitHub : `scp -i cle.key -r ...` du dossier, plus lent.)*

## PHASE 7 — Configurer le `.env` sur la VM

Le `.env` n'est PAS dans git (normal, il contient tes clés). Copie-le depuis ton PC :
```powershell
scp -i "C:\...\ssh-key-XXXX.key" c:\Users\ilias\.gemini\antigravity-ide\scratch\QuantumTradingPlateforme\.env ubuntu@IP_VM:~/quantum-trade/.env
```
Puis sur la VM, adapte pour la prod (`nano .env`) — remplace/ajoute (avec TON IP) :
```
SECRET_KEY=bd30294bf35d4772e6dd13a7638bab91c48fe4a06d515e3e7cb626d5e2ecdc29
ACCESS_TOKEN_EXPIRE_MINUTES=60
PUBLIC_API_URL=http://IP_VM:8080
PUBLIC_WS_URL=ws://IP_VM:8080/ws
CORS_ORIGINS=http://IP_VM:3000
```

## PHASE 8 — Lancer 🚀

```bash
cd ~/quantum-trade
docker compose --env-file .env -f infra/docker-compose.yml up -d --build
```
Premier build ARM : ~5-10 min. Vérifier :
```bash
curl -s localhost:8080/health
docker compose -f infra/docker-compose.yml ps
```

## PHASE 9 — Tester et partager

- Ouvre **http://IP_VM:3000** dans ton navigateur → crée ton compte (le 1er).
- Partage simplement **http://IP_VM:3000** au trader → il s'inscrit et essaie gratuitement.
- Active 🤖 Trading auto papier + ta stratégie : le forward test tourne désormais **24/7**.

## Maintenance
- Mettre à jour : `git pull && docker compose --env-file .env -f infra/docker-compose.yml up -d --build`
- Logs : `docker compose -f infra/docker-compose.yml logs backend --tail 50`
- La VM Always Free n'expire pas ; ne « upgrade » jamais le compte si tu veux la garantie 0 €.

## Limites assumées de ce déploiement gratuit
- **HTTP simple (pas HTTPS)** : suffisant pour un essai ; pour du public sérieux, ajouter un
  nom de domaine + Caddy/Traefik (je peux le faire ensuite).
- Rappel : disclaimers en place, mais l'avis juridique reste nécessaire avant un usage large.
