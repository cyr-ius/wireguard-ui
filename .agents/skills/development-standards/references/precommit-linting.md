# 🔧 Pre-commit, Linting & Conventions

Tous les changements doivent respecter `.pre-commit-config.yaml`.

## Hooks disponibles

### 1. Ruff — Python linting & formatting

Remplace Black, Flake8, isort.

```bash
ruff check backend/ --fix        # Auto-fix linting
ruff format backend/             # Format code
```

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "C4", "UP"]
ignore = ["E501"]  # géré par le formatter
```

### 2. python-typing-update — Modernisation des type hints

```bash
pre-commit run --hook-stage manual python-typing-update --all-files
```

Python 3.14+ : `str | None` au lieu de `Optional[str]`, `list[int]` au lieu de `List[int]`.

### 3. Prettier — Formatting frontend (HTML, JSON, YAML, Markdown, TS)

```bash
npm run prettier
cd frontend && npx prettier --write "src/**/*.{ts,html,scss}"
```

```json
// .prettierrc
{
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "arrowParens": "avoid"
}
```

### 4. Codespell — Orthographe

```bash
codespell                  # check
codespell --write-changes  # auto-fix
```

```
# .codespellrc
skip = ./.git,*.json,*.csv,.devcontainer,.vscode
ignore-words-list = te
```

### 5. Hooks pre-commit standard

`check-json`, `check-yaml` (`--unsafe`), `check-toml`, `check-added-large-files`, `end-of-file-fixer`, `trailing-whitespace`, `mixed-line-ending`. Les fichiers doivent finir par un saut de ligne, sans espaces de fin.

### 6. yamllint

```yaml
# .yamllint
extends: default
rules:
  line-length: disable
  indentation: { spaces: 2 }
```

## Exécution manuelle

```bash
pre-commit run --all-files            # tous les hooks
pre-commit run ruff-format --all-files
pre-commit install                    # auto-run au commit
pre-commit autoupdate                 # MAJ versions
git commit --no-verify                # désactiver (déconseillé)
```

## Workflow recommandé avant commit

```bash
cd backend && ruff format . && cd ..
cd frontend && npm run prettier && cd ..
pre-commit run --all-files            # doit passer sans modification
cd backend && python -m pytest && cd ..
cd frontend && npm run test && cd ..
git add . && git commit -m "feat(scope): description"
```

## ⚠️ Commit sûr — lancer les hooks AVANT `git commit`

Au `git commit`, `prek`/`pre-commit` relance les hooks. Si un hook **auto-corrige**
un fichier à ce moment-là, le commit échoue (le fichier a été modifié après le staging).
Pour éviter cette surprise, on relance les correcteurs **avant** de committer, puis on
re-stage, de sorte que la passe au commit ne trouve plus rien à modifier :

```bash
# 1. Auto-fix uniquement sur les fichiers concernés (rapide)
prek run --files <fichiers…>          # ou: pre-commit run --files <fichiers…>
# 2. Re-stager ce que les hooks ont corrigé
git add <fichiers…>
# 3. Committer — la passe pre-commit est alors un no-op
git commit -m "feat(scope): description"
```

### Piège du staging partiel (le plus fréquent)

Si on n'indexe qu'**une partie** des changements d'un fichier (staging par hunks, ou
mélange « mes lignes + lignes d'une autre feature » dans le même fichier), `prek` met
de côté (stash) la partie non indexée, lance les hooks sur le snapshot indexé, puis
tente de ré-appliquer le stash. Si un hook a modifié le fichier entre-temps, la
ré-application **entre en conflit** → les corrections sont annulées et le commit avorte.

Pour un commit qui ne mélange que des fichiers **partiellement** indexés :

```bash
# Option A — pré-corriger tout le fichier puis re-stager le sous-ensemble voulu
prek run --files <fichiers…>
git add -p <fichiers…>                 # ou git apply --cached <patch> pour un sous-ensemble

# Option B — isoler les changements non liés le temps du commit
git stash push --keep-index            # met de côté ce qui n'est PAS indexé
git commit -m "…"                      # working tree == index : plus de conflit possible
git stash pop                          # restaure les changements non liés
```

> Règle : **relancer un commit qui a échoué sur un hook** est souvent suffisant (les
> auto-fix ont déjà été appliqués au 1er essai) ; mais pré-lancer les hooks reste la
> façon fiable d'éviter l'aller-retour, surtout en staging partiel.

## Config IDE (auto-format)

`.vscode/settings.json` : `formatOnSave: true` partout ; formatter Python = `charliermarsh.ruff` (avec `source.fixAll` + `source.organizeImports`), reste = `esbenp.prettier-vscode`.

---

## 📋 Conventions communes

### Noms de fichiers

```
# Angular                          # FastAPI
my-component.component.{ts,html,css}  user_service.py    # Service
my.service.ts                        user_models.py     # Modèles Pydantic
my.pipe.ts / my.directive.ts         user_routes.py     # Routes
my.guard.ts                          config.py / exceptions.py
```

### Nommage

- **TypeScript** : `MAX_RETRY` (const), `currentUser` (var), `getUserById()` (fn), `UserService` (classe), `IUser` (interface), `Status` (enum). HTML : `data-testid`, `aria-label`, `(click)`, `(keydown.enter)`, `[attr.aria-expanded]`.
- **Python** : `MAX_RETRIES` (const), `current_user` (var), `get_user_by_id()` (fn), `UserService` (classe), `async def fetch_data()`.

---

## ✅ Checklist avant commit

**Angular :**

- [ ] `@if`/`@for`/`@switch` (pas `*ngIf`/`*ngFor`/`*ngSwitch`)
- [ ] Template `.html` et styles `.css` séparés
- [ ] `inject()` pour la DI ; état avec `signal()`/`computed()` ; formulaires en Signal Forms
- [ ] Pas d'imports circulaires ; fichiers finissant par un saut de ligne

**FastAPI :**

- [ ] Routes `async` ; modèles Pydantic pour la validation
- [ ] `HTTPException` pour les erreurs ; `logging` (pas `print()`)
- [ ] Type hints + docstrings ; config via `Settings`
- [ ] Fichiers `.py` finissant par un saut de ligne

**Documentation :** markdown standard, extension `.md`, fichiers finissant par un saut de ligne.

## Ressources

- [Pre-commit](https://pre-commit.com/) · [Ruff](https://docs.astral.sh/ruff/) · [Prettier](https://prettier.io/) · [Docker](https://docs.docker.com/) · [Docker Compose](https://docs.docker.com/compose/)
