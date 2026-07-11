# AGENTS.md

Instructions for AI agents operating in this repository.

## Purpose

This document defines the rules and workflow that AI agents must follow when analyzing, modifying, testing, or deploying this repository.

The objective is to:

- quickly understand the project structure;
- prepare a consistent local development environment;
- apply the required development standards;
- run the appropriate validation checks;
- avoid common dependency and implementation mistakes.

## Agent behavior

Before making any change, AI agents must:

1. Read and understand the relevant source files.
2. Identify existing architectural patterns and conventions.
3. Read and apply the `development-standards` skill.
4. Make the smallest possible change required.
5. Run the appropriate verification commands.
6. Clearly report performed changes and validation results.

AI agents must not:

- introduce new dependencies without justification;
- replace existing technologies or patterns without approval;
- manually modify generated files;
- ignore existing conventions;
- bypass failing validation checks;
- create duplicated implementations when an existing component can be extended.

## Development standards

All coding conventions, architectural rules, security practices, and development guidelines are defined in the `development-standards` skill.

AI agents **must read and follow the `development-standards` skill before making any code changes**.

The rules defined in this skill are mandatory and apply to:

- code style and formatting;
- naming conventions;
- project architecture;
- framework usage;
- error handling;
- security requirements;
- testing practices;
- dependency management;
- documentation standards.

Any implementation, modification, or code review performed in this repository must comply with the `development-standards` skill.

## Technology stack

### Backend

- Python `>= 3.14`
- FastAPI
- Pydantic 2
- Managed with `uv`

### Frontend

- Angular
- TypeScript
- Node.js `>= 22`
- npm
- Angular CLI

## Project structure

```
.
├── backend/          # FastAPI backend
├── frontend/         # Angular frontend
├── scripts/          # Automation and deployment scripts
└── AGENTS.md         # AI agent instructions
```

## System requirements

The development environment requires:

- Python `>= 3.14`
- `uv` installed: https://docs.astral.sh/uv/
- Node.js `>= 22`
- npm

## Dependency installation

### Backend

```bash
cd backend
uv sync
```

Do not use `pip install -r requirements.txt`.

The Python project is managed through:

- `pyproject.toml`
- `uv.lock`

### Frontend

```bash
cd frontend
npm ci
```

Prefer `npm ci` over `npm install` to respect `package-lock.json`.

## Verification commands

### Backend

```bash
cd backend
uv run ruff check app
uv run ruff format --check app
uv run mypy app
```

### Frontend

```bash
cd frontend
npm run build
```

## Running in development mode

### Backend

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm start
```

## Error reporting

If a required tool is missing:

- clearly report the environment limitation;
- do not use unsupported workarounds.

If a command fails:

- report the failing command;
- explain the cause when identifiable;
- do not hide validation failures.

## Deployment

Production releases must use:

```bash
scripts/release.sh
```

## References

For consistent development practices, use the following GitHub repositories as inspiration:

- cyr-ius/powerdns-ui
- cyr-ius/portalcrane
- cyr-ius/wireguard-ui
- cyr-ius/verifid
