# WireGuard UI

Interface web moderne pour administrer un serveur WireGuard sans manipuler directement les fichiers de configuration.

## ✨ Fonctionnalités

- Gestion des pairs (création, édition, révocation).
- Génération de configuration client.
- Export via QR code et fichier.
- Authentification administrateur.
- Healthcheck API intégré (`/api/health`).
- Déploiement simple avec Docker / Docker Compose.

## 🧱 Stack technique

- **Backend** : FastAPI (Python)
- **Frontend** : Angular
- **Base de données** : SQLite (par défaut, persistée dans `/data`)
- **Conteneurisation** : Docker multi-stage (Node + Python + WireGuard tools)

## 🚀 Démarrage rapide (Docker Compose)

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

### 3) Lancer l’application

```bash
docker compose up -d --build
```

### 4) Accéder à l’interface

- UI / API : `http://localhost:8000`
- Port WireGuard : `51820/udp`

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
- `ALLOWED_ORIGINS` : origines CORS autorisées (séparées par des virgules).
- `FRONTEND_DIST` : chemin du build frontend servi en statique.

### Base de données

- `DATABASE_URL` : URL de connexion SQLAlchemy.
  - Par défaut : `sqlite+aiosqlite:////data/wireguard_ui.db`

### WireGuard

- `WIREGUARD_AUTOSTART` : active le démarrage automatique WireGuard au lancement.

### Email (envoi de configuration / notifications)

- `MAIL_FROM` : adresse expéditrice.
- `MAIL_NAME` : nom expéditeur.

> D’autres réglages SMTP sont configurables depuis l’interface d’administration.

## 🩺 Santé de service

Le conteneur expose un healthcheck sur :

```text
GET /api/health
```

Exemple :

```bash
curl -f http://localhost:8000/api/health
```

## 📦 Persistance des données

Le volume `wireguard-ui_data` est monté sur `/data` dans le conteneur.

- Base SQLite
- État applicatif persistant

## 🛡️ Recommandations production

- Remplacer `SECRET_KEY` par une valeur longue et aléatoire.
- Changer immédiatement les identifiants admin par défaut.
- Restreindre `ALLOWED_ORIGINS` à vos domaines.
- Utiliser un reverse proxy TLS (Traefik, Nginx, Caddy).
- Sauvegarder régulièrement le volume `/data`.

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
