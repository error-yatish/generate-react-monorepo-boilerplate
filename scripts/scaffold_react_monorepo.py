#!/usr/bin/env python3
"""Scaffold a TypeScript React monorepo boilerplate."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def kebab(value: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    if not name or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise SystemExit("Project name must be kebab-case letters, digits, and hyphens.")
    return name


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def workspace_run(pm: str, package_name: str, script: str) -> str:
    if pm == "yarn":
        return f"yarn workspace {package_name} {script}"
    return f"npm --workspace {package_name} run {script}"


def install_command(pm: str) -> str:
    return {"npm": "npm install", "yarn": "yarn install"}[pm]


def create_project(args: argparse.Namespace) -> Path:
    project_name = kebab(args.project_name)
    root = Path(args.output_dir).resolve() / project_name
    if root.exists() and any(root.iterdir()) and not args.force:
        raise SystemExit(f"Refusing to write into non-empty directory: {root}")

    backends = [item.strip() for item in args.backends.split(",") if item.strip()]
    pm = args.package_manager
    client_package = f"@{project_name}/client"
    common_package = f"@{project_name}/common"

    dirs = [
        "client/src/app/home",
        "client/src/app/explore",
        "client/src/app/settings",
        "client/src/components",
        "client/src/configuration",
        "client/src/contexts",
        "client/src/hooks",
        "client/src/libs",
        "client/src/queries",
        "client/src/root",
        "client/src/routes",
        "client/src/stores/StoreRoot",
        "client/src/styles",
        "client/src/types",
        "common/src/configuration",
        "common/src/entities",
        "common/src/helpers",
        "common/src/libs/featureFlags",
        "common/src/openapi-new",
        "common/src/specs",
        "common/src/types",
        "tooling/src",
        ".github/workflows",
        ".husky",
        ".vscode",
        "docs/getting-started",
        "docs/decisions",
    ]
    for directory in dirs:
        (root / directory).mkdir(parents=True, exist_ok=True)

    write_json(root / "package.json", {
        "name": project_name,
        "private": True,
        "description": args.description,
        "workspaces": ["client", "common", "tooling"],
        "scripts": {
            ":d": workspace_run(pm, client_package, "dev"),
            ":qa": f"{workspace_run(pm, client_package, 'dev')} -- --mode qa",
            ":cloud": f"{workspace_run(pm, client_package, 'dev')} -- --mode production",
            ":c": f"{pm} run lint:code && {pm} run check:code && {pm} run test:client && {pm} run build:prod",
            ":v": f"{pm} run format && {pm} run :c",
            "format": "oxlint --fix .",
            "lint": "oxlint .",
            "lint:code": "oxlint .",
            "check:code": "tsc -b --pretty",
            "test": f"{pm} run test:client",
            "test:client": workspace_run(pm, client_package, "test"),
            "test:cy": workspace_run(pm, client_package, "test:cy"),
            "test:coverage": workspace_run(pm, client_package, "test:coverage"),
            "build:prod": workspace_run(pm, client_package, "build"),
            "build:openapi": workspace_run(pm, common_package, "build:openapi")
        },
        "devDependencies": {
            "@types/node": "^20.14.0",
            "concurrently": "^8.2.2",
            "husky": "^9.0.11",
            "oxlint": "^0.16.0",
            "typescript": "^5.4.5",
            "vite": "^5.2.0",
            "vitest": "^1.6.0"
        }
    })

    write_json(root / "client/package.json", {
        "name": f"@{project_name}/client",
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "vite --config ../vite.config.ts --host 0.0.0.0",
            "build": "vite build --config ../vite.config.ts",
            "preview": "vite preview",
            "test": "vitest run --config ../vitest.config.ts",
            "test:coverage": "vitest run --config ../vitest.config.ts --coverage",
            "test:cy": "cypress run --component --config-file ../cypress.config.ts"
        },
        "dependencies": {
            "@emotion/react": "^11.11.4",
            "@tanstack/react-query": "^5.40.0",
            "@tanstack/react-router": "^1.35.0",
            "luxon": "^3.4.4",
            "mobx": "^6.12.3",
            "mobx-react-lite": "^4.0.7",
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "zod": "^3.23.8"
        },
        "devDependencies": {
            "@types/react": "^18.3.3",
            "@types/react-dom": "^18.3.0",
            "@vitejs/plugin-react": "^4.2.1",
            "cypress": "^13.9.0",
            "vite": "^5.2.0",
            "vitest": "^1.6.0"
        }
    })

    write_json(root / "common/package.json", {
        "name": f"@{project_name}/common",
        "private": True,
        "type": "module",
        "scripts": {
            "build": "tsc -p tsconfig.json",
            "build:openapi": "echo \"Add specs to common/src/specs before generating clients\""
        },
        "dependencies": {
            "@kubb/core": "^2.23.0",
            "@kubb/openapi": "^2.23.0",
            "zod": "^3.23.8"
        },
        "devDependencies": {"typescript": "^5.4.5"}
    })

    write_json(root / "tooling/package.json", {
        "name": f"@{project_name}/tooling",
        "private": True,
        "type": "module",
        "scripts": {"proxy": "tsx src/proxy.ts"},
        "devDependencies": {"tsx": "^4.11.0", "typescript": "^5.4.5"}
    })

    write(root / "tsconfig.json", """
{
  "files": [],
  "references": [
    { "path": "./client" },
    { "path": "./common" },
    { "path": "./tooling" }
  ],
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true
  }
}
""")

    write(root / "client/tsconfig.json", """
{
  "extends": "../tsconfig.json",
  "compilerOptions": {
    "composite": true,
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@common/*": ["../common/src/*"]
    }
  },
  "include": ["src", "vite-env.d.ts"]
}
""")

    write(root / "common/tsconfig.json", """
{
  "extends": "../tsconfig.json",
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "declaration": true,
    "outDir": "dist"
  },
  "include": ["src"]
}
""")

    write(root / "tooling/tsconfig.json", """
{
  "extends": "../tsconfig.json",
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Bundler"
  },
  "include": ["src"]
}
""")

    backend_lines = ",\n".join(f"  '{name}': '{url_for_backend(name)}'" for name in backends)
    write(root / "client/src/configuration/getAppConfig.ts", f"""
import {{ z }} from 'zod';

const backendUrls = {{
{backend_lines}
}} as const;

const appConfigSchema = z.object({{
  appName: z.string(),
  backendUrls: z.record(z.string()),
  apiFormat: z.literal('{args.api_format}'),
}});

export type AppConfig = z.infer<typeof appConfigSchema>;

export function getAppConfig(): AppConfig {{
  return appConfigSchema.parse({{
    appName: '{project_name}',
    backendUrls,
    apiFormat: '{args.api_format}',
  }});
}}
""")

    write(root / "client/src/queries/query-client.ts", """
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
});
""")

    write(root / "client/src/stores/StoreBase.ts", """
import { makeAutoObservable } from 'mobx';

export abstract class StoreBase {
  protected constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }
}
""")

    write(root / "client/src/stores/StoreRoot/index.ts", """
import { StoreFlags } from '../StoreFlags';

export class StoreRoot {
  readonly flags = new StoreFlags();
}

export const storeRoot = new StoreRoot();
""")

    write(root / "client/src/stores/StoreFlags.ts", """
import { StoreBase } from './StoreBase';

export class StoreFlags extends StoreBase {
  isReady = false;

  constructor() {
    super();
  }

  markReady(): void {
    this.isReady = true;
  }
}
""")

    write(root / "client/src/app/home/HomePage.tsx", """
export function HomePage() {
  return (
    <main>
      <h1>React monorepo starter</h1>
      <p>Replace this page with product-specific content.</p>
    </main>
  );
}
""")

    if args.examples:
        write(root / "client/src/app/explore/ExplorePage.tsx", """
const rows = [
  { id: 'vm-001', name: 'Exposure overview', severity: 'High' },
  { id: 'vm-002', name: 'Asset inventory', severity: 'Medium' },
  { id: 'vm-003', name: 'Remediation plan', severity: 'Low' },
];

export function ExplorePage() {
  return (
    <main>
      <h1>Explore</h1>
      <table>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.name}</td>
              <td>{row.severity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
""")
        write(root / "client/src/app/settings/SettingsPage.tsx", """
export function SettingsPage() {
  return (
    <main>
      <h1>Settings</h1>
      <label>
        <input type="checkbox" defaultChecked />
        Enable example feature flag
      </label>
    </main>
  );
}
""")

    write(root / "client/src/root/App.tsx", """
import { HomePage } from '@/app/home/HomePage';

export function App() {
  return <HomePage />;
}
""")

    write(root / "client/src/app/createApp.tsx", """
import { QueryClientProvider } from '@tanstack/react-query';
import { App } from '@/root/App';
import { queryClient } from '@/queries/query-client';

export function createApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );
}
""")

    write(root / "client/src/main.tsx", """
import React from 'react';
import { createRoot } from 'react-dom/client';
import { createApp } from '@/app/createApp';
import '@/styles/global.css';

createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>{createApp()}</React.StrictMode>,
);
""")

    write(root / "client/src/styles/global.css", """
:root {
  color: #1f2937;
  background: #f8fafc;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body {
  margin: 0;
}

main {
  margin: 0 auto;
  max-width: 960px;
  padding: 48px 24px;
}
""")

    write(root / "client/index.html", """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>React Monorepo</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""")

    write(root / "vite.config.ts", """
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'client/src'),
      '@common': path.resolve(__dirname, 'common/src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'https://localhost:8443',
    },
  },
});
""")

    write(root / "vitest.config.ts", """
import { defineConfig } from 'vitest/config';
import viteConfig from './vite.config';

export default defineConfig({
  ...viteConfig,
  test: {
    environment: 'jsdom',
    globals: true,
    coverage: {
      reporter: ['text', 'html'],
    },
  },
});
""")

    write(root / "cypress.config.ts", """
import { defineConfig } from 'cypress';

export default defineConfig({
  component: {
    devServer: {
      framework: 'react',
      bundler: 'vite',
    },
  },
});
""")

    write(root / "common/src/types/index.ts", "export type EntityId = string;")
    write(root / "common/src/libs/featureFlags/index.ts", "export const featureFlags = ['example-feature'] as const;")
    write(root / "common/src/specs/.gitkeep", "")
    write(root / "common/src/openapi-new/.gitkeep", "")
    write(root / "tooling/src/proxy.ts", "console.log('Add local backend proxy configuration here.');")

    write(root / ".gitignore", """
node_modules/
dist/
coverage/
.env
.DS_Store
""")
    write(root / ".editorconfig", """
root = true

[*]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 2
insert_final_newline = true
trim_trailing_whitespace = true
""")
    write(root / ".env.example", "VITE_APP_ENV=local")
    write(root / ".vscode/settings.json", '{\n  "typescript.tsdk": "node_modules/typescript/lib"\n}')
    write(root / ".husky/pre-commit", f"{pm} run lint:code")
    write(root / ".husky/pre-push", f"{pm} run :c")

    write_workflows(root, pm)
    write_docs(root, project_name, args.description, pm)

    if args.docker:
        write(root / "Dockerfile", """
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
COPY client/package*.json client/
COPY common/package*.json common/
COPY tooling/package*.json tooling/
RUN npm install
COPY . .
RUN npm run build:prod
""")

    if args.federated:
        write(root / "client/src/configuration/federation.ts", """
export const federationConfig = {
  name: 'host',
  remotes: {},
  exposes: {},
} as const;
""")

    write(root / "README.md", f"""
# {project_name}

{args.description}

## Getting started

```bash
{pm} install
{pm} run :d
```

## Quality

```bash
{pm} run :c
```

Add OpenAPI specs to `common/src/specs/`, then run `{pm} run build:openapi`.
""")

    write(root / "CLAUDE.md", """
# Agent Guidance

Work with the existing monorepo boundaries:

- Put app-specific UI in `client/src`.
- Put shared types, helpers, API clients, and feature flags in `common/src`.
- Put local development automation in `tooling/src`.
- Keep server state in React Query and local UI state in MobX stores.
- Preserve strict TypeScript settings and avoid broad casts.
""")

    return root


def url_for_backend(name: str) -> str:
    normalized = name.replace("_", "-").lower()
    if normalized in {"production", "prod", "cloud"}:
        return "https://api.example.com"
    return f"https://api.{normalized}.example.com"


def write_workflows(root: Path, pm: str) -> None:
    for name, command in {
        "lint": "lint:code",
        "test": "test",
        "build": "build:prod",
    }.items():
        write(root / f".github/workflows/{name}.yml", f"""
name: {name}

on:
  pull_request:
  push:
    branches: [main]

jobs:
  {name}:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: {install_command(pm)}
      - run: {pm} run {command}
""")


def write_docs(root: Path, project_name: str, description: str, pm: str) -> None:
    write(root / "docs/index.html", """
<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Docs</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  </head>
  <body>
    <div id="app"></div>
    <script>
      window.$docsify = { name: 'Project Docs', repo: '' };
    </script>
    <script src="//cdn.jsdelivr.net/npm/docsify@4"></script>
  </body>
</html>
""")
    write(root / "docs/README.md", f"# {project_name}\n\n{description}")
    write(root / "docs/getting-started/local-development.md", f"""
# Local Development

1. Install dependencies with `{pm} install`.
2. Start the app with `{pm} run :d`.
3. Run verification with `{pm} run :c`.
""")
    write(root / "docs/decisions/0001-architecture.md", """
# 0001 Architecture

Use a workspace monorepo with `client`, `common`, and `tooling` packages. Keep UI, shared contracts, and developer automation separated so each package has a clear owner.
""")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_name")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--description", default="Production-ready React monorepo.")
    parser.add_argument("--package-manager", choices=["npm", "yarn"], default="npm")
    parser.add_argument("--examples", action="store_true")
    parser.add_argument("--federated", action="store_true")
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--backends", default="qa-develop,production")
    parser.add_argument("--api-format", choices=["openapi3", "swagger2"], default="openapi3")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    created = create_project(parse_args())
    print(f"Created React monorepo boilerplate at {created}")
