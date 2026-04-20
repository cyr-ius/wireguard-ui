# WireGuard UI

Interface web pour administrer un serveur WireGuard sans manipuler directement les fichiers de configuration.

## ✨ Fonctionnalités

- Gestion des pairs (création, édition, révocation).
- Génération de configuration client.
- Export via QR code et fichier.
- Authentification administrateur.
- Healthcheck API intégré (`/api/health`).
- Déploiement simple avec Docker / Docker Compose.
- Envoie de mail pour l'enrollement

<img width="1295" height="948" alt="image" src="https://github.com/user-attachments/assets/f147aeed-9d02-43c4-b686-aa400d06942c" />
<img width="1033" height="461" alt="image" src="https://github.com/user-attachments/assets/7beb9fea-089c-4ff4-a275-907674390f1c" />
<img width="1033" height="947" alt="image" src="https://github.com/user-attachments/assets/6bc9e2f8-0380-44e5-b1db-19aa5304cb44" />

## 🧱 Stack technique

| Layer          | Technology                                                          |
| -------------- | ------------------------------------------------------------------- |
| **Frontend**   | Angular 21 — Signals, Signal Forms, Zoneless, standalone components |
| **Styling**    | Bootstrap 5 + Bootstrap Icons                                       |
| **Backend**    | FastAPI + Python 3.14 (fully async)                                 |
| **Validation** | Pydantic v2                                                         |
| **Container**  | Single image — supervisord orchestrates all processes               |
| **Platforms**  | `linux/amd64`, `linux/arm64` (Raspberry Pi, Apple Silicon)          |

## 🚀 Démarrage rapide

### Docker CLI

```bash
docker run -d \
  --name wireguard-ui \
  --cap-add NET_ADMIN \
  --sysctl net.ipv4.ip_forward=1 \
  --sysctl net.ipv4.conf.all.src_valid_mark=1 \
  -p 8000:8000 \
  -p 51820:51820/udp \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=yourpassword \
  -e SECRET_KEY=your-secret-key \
  -v wg_config:/etc/wireguard \
  -v wireguard-ui_data:/var/lib/wireguard-ui \
  cyrius44/wireguard-ui:latest
```

Open **http://localhost:8000** and log in with your admin credentials.

### Docker Compose

```yaml
services:
  wireguard-ui:
    image: cyrius44/wireguard-ui:latest
    container_name: wireguard-ui
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv4.conf.all.src_valid_mark=1
    ports:
      - "8000:8000"
      - "51820:51820/udp"
    environment:
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=changeme
      - SECRET_KEY=your-secret-key
    volumes:
      - wg_config:/etc/wireguard
      - wireguard-ui_data:/var/lib/wireguard-ui

volumes:
  wg_config:
  wireguard-ui_data:
```

### Lancer l’application

```bash
docker compose up -d --build
```

---

## 🌐 Ports

- `8000` — Wireguard UI + API
- `51820` — Wireguard port for clients

## 🩺 Santé de service

`GET /api/health` returns a JSON status payload.

## 🔐 Security Notes

- `SECRET_KEY` must be set to a non-default value or the app will refuse to start.
- Always change `ADMIN_PASSWORD` on first launch.
- If you expose the UI publicly, enable HTTPS at the reverse proxy level.

## 🔐 Variables d’environnement importantes

### Sécurité / Auth

- `ADMIN_USERNAME` : identifiant admin initial.
- `ADMIN_PASSWORD` : mot de passe admin initial.
- `ADMIN_EMAIL` : email admin initial.
- `SECRET_KEY` : clé de signature JWT (**obligatoire en production**).
- `ACCESS_TOKEN_EXPIRE_MINUTES` : durée de vie des tokens.
- `BCRYPT_ROUNDS` : coût de hash des mots de passe.

### API / Application

- `LOG_LEVEL` : niveau de logs (`INFO`, `DEBUG`, etc.).
- `APP_VERSION` : version exposée par l’application.

### Base de données

- `DB_PATH` : URL de connexion SQLAlchemy.
  - Par défaut : `sqlite+aiosqlite:////var/lib/wireguard-ui/wireguard_ui.db`

### WireGuard

- `WIREGUARD_AUTOSTART` : active le démarrage automatique WireGuard au lancement.

### Email (envoi de configuration / notifications)

- `MAIL_FROM` : adresse expéditrice.
- `MAIL_NAME` : nom expéditeur.

### Systctl

- `net.ipv4.ip_forward=1` : nécessaire pour forwwarder les appels vers la carte principale
- `net.ipv4.conf.all.src_valid_mark=1` : nécessaire pour l'identification des sources

> D’autres réglages SMTP sont configurables depuis l’interface d’administration.

---

## 📦 Persistance des données

Deux volumes sont nécessaires :

| Volume | Point de montage | Contenu |
|---|---|---|
| `wg_config` | `/etc/wireguard` | Configuration WireGuard (`wg0.conf`, clés) |
| `wireguard-ui_data` | `/var/lib/wireguard-ui` | Base SQLite, données applicatives |

## 🛡️ Recommandations production

- Remplacer `SECRET_KEY` par une valeur longue et aléatoire.
- Changer immédiatement les identifiants admin par défaut.
- Utiliser un reverse proxy TLS (Traefik, Nginx, Caddy).
- Sauvegarder régulièrement les volumes `/etc/wireguard` et `/var/lib/wireguard-ui`.

---

## 📋 Development

### 1) Cloner le dépôt

```bash
git clone https://github.com/cyr-ius/wireguard-ui.git
cd wireguard-ui
```

### 2) (Optionnel) Créer un fichier `.env`

Le `docker-compose.yaml` fournit déjà des valeurs par défaut, mais il est recommandé de les surcharger en production :

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me-now
SECRET_KEY=replace-with-a-long-random-secret
LOG_LEVEL=INFO
```

## 🧪 Développement local (sans Docker)

Le projet est découpé en deux applications :

- `backend/` (API FastAPI)
- `frontend/` (Angular)

### Prérequis

- Python **3.14+**
- [uv](https://docs.astral.sh/uv/) (gestion des dépendances Python)
- Node.js **22+** et npm

### 1) Installer les dépendances backend

Depuis la racine du dépôt :

```bash
cd backend
uv sync --extra dev
```

### 2) Lancer le backend

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Installer les dépendances frontend

Dans un autre terminal :

```bash
cd frontend
npm ci
```

### 4) Lancer le frontend

```bash
npm start
```

Par défaut, le frontend est accessible sur `http://localhost:4200`.

## 🤝 Contribuer

Les contributions sont bienvenues : bugfix, amélioration UX, sécurité, documentation.

### Workflow recommandé

1. Forker le dépôt et créer une branche :
   ```bash
   git checkout -b feat/ma-feature
   ```
2. Développer avec des commits atomiques et des messages explicites.
3. Vérifier localement avant PR :

   ```bash
   # Backend
   cd backend
   uv run ruff check src
   uv run mypy src

   # Frontend
   cd ../frontend
   npm run build
   ```

4. Ouvrir une Pull Request avec :
   - le contexte / problème,
   - la solution proposée,
   - les tests effectués,
   - les éventuels impacts (migration, compatibilité, sécurité).

### Bonnes pratiques

- Éviter les changements hors-sujet dans une même PR.
- Préférer les PR petites et faciles à relire.
- Mettre à jour la documentation si comportement fonctionnel modifié.

## 🤖 Instructions pour agents IA

Un fichier `AGENTS.md` est fourni à la racine pour aider les agents (Codex, assistants IA, etc.) à installer les dépendances et lancer les vérifications nécessaires à l’analyse du projet.

## 📄 Licence

MIT — voir [LICENSE](LICENSE).
