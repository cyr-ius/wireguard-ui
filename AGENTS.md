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
3. Get the development standards of the technologies you touch from the `security-review`
   MCP server (see [Coding conventions](#coding-conventions)) and apply them.
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

## Coding conventions

The development standards are provided by the `security-review` MCP server, and the
documentation of the frameworks (FastAPI, SQLModel, Angular...) by the `context7` MCP server;
both are declared in your local `.mcp.json`, ignored by git (`context7`:
`https://mcp.context7.com/mcp`; `security-review`: the URL of your server, with its OAuth
login, without any token in the file), and no skill is needed. Read the standards before writing
code:

- tool `get_development_standards`, by technology (`python`, `angular`...) or by file
  (`pyproject.toml`, `angular.json`...);
- tool `list_development_standards` to see the catalog;
- resource `standard://<slug>` to read one standard.

Do not copy them here. This file only keeps the rules specific to this repository; in case of
conflict, it wins. A standard never weakens security: keep the safe behavior and report the
conflict. If the server is not connected, say so, and follow the existing code.

## Security review

When the `security-review` MCP server is connected (its prompts and tools appear in the
session), a security review of the changes is **systematic** before declaring a task done or
opening a pull request, whatever the size of the change:

1. Run the `security-review` prompt (or `api-security-review` for the API,
   `configuration-review` for the Dockerfile, workflows and YAML, `dependency-review` when the
   dependency files change) on the modified files, with the diff as context.
2. Use `scan_code` and `get_review_checklist` during the review.
3. Save the result **once** with `save_security_report` (`project`: the repository name, plus
   `branch` and `commit_sha` when known).
4. Fix the `critical` and `high` findings before finishing, with a test covering the fix. Fix
   or justify the others and propose their status with `propose_finding_status`: an agent never
   changes a status, a person validates the proposal in the web interface.
5. Summarize the review (report identifier, findings and what was done) in the answer and in
   the pull request description.

If the server is not connected or does not answer, say so explicitly: never claim a review
that was not made.

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
