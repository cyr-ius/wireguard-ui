# AGENTS.md

Instructions pour les agents IA opérant dans ce dépôt.

## Objectif

Préparer rapidement un environnement local pour **analyser le code**, exécuter les contrôles de base et éviter les erreurs courantes liées aux dépendances.

## Arborescence utile

- `backend/` : API FastAPI (Python, `uv`)
- `frontend/` : UI Angular (Node + npm + @angular/cli)

## Prérequis système

- Python `>= 3.14`
- `uv` installé (https://docs.astral.sh/uv/)
- Node.js `>= 22`
- npm

## Installation des dépendances

### Backend

```bash
cd backend
uv sync --extra dev
```

### Frontend

```bash
cd frontend
npm install @angular/cli@21
npm ci
```

## Commandes de vérification (analyse)

### Backend

```bash
cd backend
uv run ruff check src
uv run mypy src
```

### Frontend

```bash
cd frontend
npm run build
```

## Lancement en mode développement

### Backend

```bash
cd backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm start
```

## Notes importantes

- Ne pas utiliser `pip install -r requirements.txt` : le projet Python est géré via `pyproject.toml` + `uv.lock`.
- Préférer `npm ci` à `npm install` pour respecter le verrouillage de `package-lock.json`.
- Si un outil manque (ex: `uv`, `node`), signaler clairement la limitation d’environnement dans le compte-rendu.
