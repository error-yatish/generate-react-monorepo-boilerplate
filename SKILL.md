---
name: generate-react-monorepo-boilerplate
description: Create a production-ready React monorepo boilerplate from scratch with TypeScript, React 18, MobX, TanStack React Query, TanStack Router, Vite, Vitest, Cypress, OpenAPI client scaffolding, workspace packages, docs, git hooks, and CI. Use when the user asks to generate, scaffold, bootstrap, or set up a React monorepo, a service-vm-ui-style frontend workspace, a multi-package SPA, or a large-scale TypeScript React project with shared common/tooling packages.
---

# Generate React Monorepo Boilerplate

## Quick Start

Use `scripts/scaffold_react_monorepo.py` for deterministic project creation, then adjust generated files to the user's exact requirements.

```bash
python scripts/scaffold_react_monorepo.py my-project --output-dir . --description "My React workspace" --package-manager npm --examples --federated --docker --backends qa-develop,qa-staging,production --api-format openapi3
```

Prefer running the script from the skill directory or by absolute path. After generation, inspect the output and make targeted edits instead of regenerating over user changes.

## Inputs

Collect or infer these values before generating:

- Project name: kebab-case, used for folder and package names.
- Description: one sentence for README and package metadata.
- Package manager: `npm`, or `yarn`; default to `npm`.
- Example pages: include when the user wants a working starter UI.
- Federated module support: include only for micro frontend or module federation use cases.
- Backend environments: default to `qa-develop,qa-staging,production`.
- API format: `openapi3` or `swagger2`; default to `openapi3`.
- Docker: include only when requested or useful for local/CI parity.

If only the project name is provided, generate with conservative defaults: `npm`, examples enabled, no federation, no Docker, and OpenAPI 3.

## Workflow

1. Validate the destination does not overwrite important user files.
2. Run the scaffold script with the selected inputs.
3. Install dependencies only if the user asked for installation or validation requires it.
4. If dependencies are installed, run the package-manager equivalent of `run :c`.
5. Update generated docs and environment URLs to match the user's product and deployment target.
6. Report the project path, commands to run, and any validation that was skipped.

## Generated Architecture

Create a workspace with:

- `client`: React 18 SPA with Vite, TanStack Router, React Query, MobX stores, Cypress component testing, and Vitest.
- `common`: shared types, helpers, domain entities, feature flag constants, OpenAPI specs, and API generation placeholders.
- `tooling`: dev proxy and workspace utilities.
- `.github/workflows`: lint, test, build, and optional deploy workflow stubs.
- `docs`: Docsify landing page, getting-started guide, and architecture decision records.
- `.husky`: pre-commit and pre-push hooks.

## Conventions

- Use strict TypeScript from the start.
- Keep MobX for local/client state and React Query for server/cache state.
- Use hash routing by default for static hosting compatibility.
- Use `@/` for `client/src` and `@common/` for `common/src`.
- Prefer OxLint and OxFmt-style commands for fast local checks.
- Keep OpenAPI specs in `common/src/specs/`; generated clients belong under `common/src/openapi-new/`.

## Validation

Generated projects should satisfy these checks after dependencies are installed:

```bash
npm run check:code
npm run lint:code
npm run test:client
npm run build:prod
```

Use the selected package manager when it is not `npm`.
