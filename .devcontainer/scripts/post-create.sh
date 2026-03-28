#!/usr/bin/env bash
# ─── Post-Create Setup Script ───────────────────────────────────────────────
# Exécuté une seule fois par VS Code après la création du container.
# À ce stade le bind mount /workspace est actif — le code source est présent.

set -euo pipefail

WORKSPACE="/workspace"
BACKEND_DIR="$WORKSPACE/backend"
FRONTEND_DIR="$WORKSPACE/frontend"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀  Post-Create Setup — FastAPI + Angular DevContainer  "
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Python / FastAPI ──────────────────────────────────────────────────────
if [ ! -f "$BACKEND_DIR/pyproject.toml" ]; then
  cp "$WORKSPACE/.devcontainer/pyproject.toml" "$BACKEND_DIR"
fi
if [ -f "$BACKEND_DIR/pyproject.toml" ]; then
  echo ""
  echo "📦  Synchronisation des dépendances Python (backend/pyproject.toml)..."
  cd "$BACKEND_DIR"
  if [ -f "uv.lock" ]; then
    uv sync --frozen --all-extras
  else
    echo "  ℹ️  uv.lock absent — génération en cours (commit-le ensuite dans git)"
    uv sync --all-extras
  fi
else
  echo "  ℹ️  backend/pyproject.toml absent — packages du bootstrap actifs"
  echo "       Crée backend/ puis relance : uv sync --all-extras"
fi

# ── 2. Angular / Node ────────────────────────────────────────────────────────
if [ -f "$FRONTEND_DIR/package.json" ]; then
  echo ""
  echo "📦  Installation des dépendances Node (frontend/package.json)..."
  cd "$FRONTEND_DIR" && npm install --silent
else
  echo "  ℹ️  frontend/package.json absent — création du projet Angular..."
  cd /workspace && ng new frontend --style 'css' --zoneless --standalone --defaults
fi

# ── 3. Git repository ────────────────────────────────────────────────────────
if [ ! -d "$WORKSPACE/.git" ]; then
  echo ""
  echo "🏁  Create git local repository..."
  cd "$WORKSPACE"
  git init
  git config --global --add safe.directory "$WORKSPACE"
else
 echo "  ✅  Git repository — déjà créé..."
fi

# ── 4. Pre-commit hooks ──────────────────────────────────────────────────────
if [ -f "$WORKSPACE/.pre-commit-config.yaml" ]; then
  echo ""
  echo "🪝  Installation des hooks pre-commit..."
  cd "$WORKSPACE"
  pre-commit install --install-hooks
else
  echo "  ℹ️  .pre-commit-config.yaml absent — hooks non installés"
fi

# ── 5. Migrations Alembic ────────────────────────────────────────────────────
if [ -f "$BACKEND_DIR/alembic.ini" ]; then
  echo ""
  echo "🗄️   Application des migrations Alembic..."
  cd "$BACKEND_DIR"
  for i in {1..10}; do
    alembic upgrade head && break || {
      echo "  Attente de la base de données... ($i/10)"
      sleep 3
    }
  done
fi

# ── 5. Fichiers .env ─────────────────────────────────────────────────────────
for dir in "$BACKEND_DIR" "$FRONTEND_DIR"; do
  if [ -f "$dir/.env.example" ] && [ ! -f "$dir/.env" ]; then
    echo ""
    echo "📄  Création de $dir/.env depuis .env.example..."
    cp "$dir/.env.example" "$dir/.env"
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅  Setup terminé !"
echo ""
echo "  Backend  → cd backend && uvicorn app.main:app --reload --host 0.0.0.0"
echo "  Frontend → cd frontend && ng serve --host 0.0.0.0"
echo "  API docs → http://localhost:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
