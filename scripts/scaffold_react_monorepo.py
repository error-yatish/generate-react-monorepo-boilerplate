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
        "client/src/components/layout",
        "client/src/configuration",
        "client/src/contexts",
        "client/src/hooks",
        "client/src/libs",
        "client/src/queries",
        "client/src/root",
        "client/src/routes",
        "client/src/router",
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
            "@base-ui/react": "^1.5.0",
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
            "@kubb/cli": "^2.23.0",
            "@kubb/core": "^2.23.0",
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

    write(root / "client/src/components/layout/Header.tsx", """
import { Button } from '@base-ui/react/button';
import { Link } from '@tanstack/react-router';

export function Header() {
  return (
    <header className="app-header">
      <Link className="brand-link" to="/">
        React Monorepo
      </Link>
      <div className="header-actions">
        <Button className="ghost-button">Docs</Button>
        <Button className="primary-button">Deploy</Button>
      </div>
    </header>
  );
}
""")

    write(root / "client/src/components/layout/Sidebar.tsx", """
import { Link } from '@tanstack/react-router';

const items = [
  { to: '/', label: 'Home' },
  { to: '/explore', label: 'Explore' },
  { to: '/settings', label: 'Settings' },
] as const;

export function Sidebar() {
  return (
    <aside className="app-sidebar">
      <nav aria-label="Main navigation">
        {items.map((item) => (
          <Link
            activeProps={{ className: 'sidebar-link active' }}
            className="sidebar-link"
            key={item.to}
            to={item.to}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
""")

    write(root / "client/src/components/layout/Page.tsx", """
import type { ReactNode } from 'react';

type PageProps = {
  actions?: ReactNode;
  children: ReactNode;
  eyebrow?: string;
  title: string;
};

export function Page({ actions, children, eyebrow, title }: PageProps) {
  return (
    <main className="page">
      <div className="page-heading">
        <div>
          {eyebrow ? <p className="page-eyebrow">{eyebrow}</p> : null}
          <h1>{title}</h1>
        </div>
        {actions ? <div className="page-actions">{actions}</div> : null}
      </div>
      {children}
    </main>
  );
}
""")

    write(root / "client/src/components/layout/AppFrame.tsx", """
import { Outlet } from '@tanstack/react-router';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export function AppFrame() {
  return (
    <div className="app-frame">
      <Header />
      <div className="app-body">
        <Sidebar />
        <Outlet />
      </div>
    </div>
  );
}
""")

    write(root / "client/src/router/root.tsx", """
import { createRootRoute } from '@tanstack/react-router';
import { AppFrame } from '@/components/layout/AppFrame';

export const rootRoute = createRootRoute({
  component: AppFrame,
});
""")

    write(root / "client/src/router/router.ts", """
import { createHashHistory, createRouter } from '@tanstack/react-router';
import { exploreRoute } from '@/routes/explore';
import { homeRoute } from '@/routes/home';
import { settingsRoute } from '@/routes/settings';
import { rootRoute } from './root';

const routeTree = rootRoute.addChildren([homeRoute, exploreRoute, settingsRoute]);

export const router = createRouter({
  history: createHashHistory(),
  routeTree,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
""")

    write(root / "client/src/routes/home.tsx", """
import { createRoute } from '@tanstack/react-router';
import { HomePage } from '@/app/home/HomePage';
import { rootRoute } from '@/router/root';

export const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: HomePage,
});
""")

    write(root / "client/src/routes/explore.tsx", """
import { createRoute } from '@tanstack/react-router';
import { ExplorePage } from '@/app/explore/ExplorePage';
import { rootRoute } from '@/router/root';

export const exploreRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/explore',
  component: ExplorePage,
});
""")

    write(root / "client/src/routes/settings.tsx", """
import { createRoute } from '@tanstack/react-router';
import { SettingsPage } from '@/app/settings/SettingsPage';
import { rootRoute } from '@/router/root';

export const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
});
""")

    write(root / "client/src/app/home/HomePage.tsx", """
import { Button } from '@base-ui/react/button';
import { Link } from '@tanstack/react-router';
import { Page } from '@/components/layout/Page';

export function HomePage() {
  return (
    <Page
      actions={
        <Link className="primary-button" to="/explore">
          Explore routes
        </Link>
      }
      eyebrow="Workspace"
      title="React monorepo starter"
    >
      <section className="panel-grid">
        <article className="panel">
          <h2>Routing</h2>
          <p>TanStack Router provides typed routes with hash history for static hosting.</p>
        </article>
        <article className="panel">
          <h2>State</h2>
          <p>React Query owns server cache while MobX stores handle local UI state.</p>
          <Button className="ghost-button">Base UI action</Button>
        </article>
      </section>
    </Page>
  );
}
""")

    write(root / "client/src/app/explore/ExplorePage.tsx", """
import { Page } from '@/components/layout/Page';

const rows = [
  { id: 'vm-001', name: 'Exposure overview', severity: 'High' },
  { id: 'vm-002', name: 'Asset inventory', severity: 'Medium' },
  { id: 'vm-003', name: 'Remediation plan', severity: 'Low' },
];

export function ExplorePage() {
  return (
    <Page eyebrow="Examples" title="Explore">
      <table className="data-table">
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.name}</td>
              <td>{row.severity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Page>
  );
}
""")
    write(root / "client/src/app/settings/SettingsPage.tsx", """
import { Button } from '@base-ui/react/button';
import { Page } from '@/components/layout/Page';

export function SettingsPage() {
  return (
    <Page
      actions={<Button className="ghost-button">Save changes</Button>}
      eyebrow="Configuration"
      title="Settings"
    >
      <section className="settings-panel">
        <label>
          <input type="checkbox" defaultChecked />
          Enable example feature flag
        </label>
      </section>
    </Page>
  );
}
""")

    write(root / "client/src/root/App.tsx", """
import { RouterProvider } from '@tanstack/react-router';
import { router } from '@/router/router';

export function App() {
  return <RouterProvider router={router} />;
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
  color: #172033;
  background: #eef2f6;
  font-family: "IBM Plex Sans", "Segoe UI", ui-sans-serif, system-ui, sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

a {
  color: inherit;
  text-decoration: none;
}

.app-frame {
  min-height: 100vh;
}

.app-header {
  align-items: center;
  background: #ffffff;
  border-bottom: 1px solid #d8dee8;
  display: flex;
  height: 64px;
  justify-content: space-between;
  padding: 0 24px;
}

.brand-link {
  font-size: 1.05rem;
  font-weight: 700;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.app-body {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  min-height: calc(100vh - 64px);
}

.app-sidebar {
  background: #172033;
  color: #dce5f2;
  padding: 20px 16px;
}

.app-sidebar nav {
  display: grid;
  gap: 8px;
}

.sidebar-link {
  border-radius: 8px;
  color: #bac7d8;
  display: block;
  padding: 10px 12px;
}

.sidebar-link.active,
.sidebar-link:hover {
  background: #243149;
  color: #ffffff;
}

.page {
  margin: 0 auto;
  max-width: 1120px;
  padding: 40px 32px;
  width: 100%;
}

.page-heading {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-eyebrow {
  color: #5f6f87;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0;
  margin: 0 0 6px;
  text-transform: uppercase;
}

.page h1 {
  font-size: 2rem;
  line-height: 1.15;
  margin: 0;
}

.page-actions {
  display: flex;
  gap: 10px;
}

.primary-button,
.ghost-button {
  border-radius: 8px;
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 9px 14px;
}

.primary-button {
  background: #166534;
  border: 1px solid #166534;
  color: #ffffff;
}

.ghost-button {
  background: #ffffff;
  border: 1px solid #b8c3d3;
  color: #172033;
}

.panel-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.panel,
.settings-panel {
  background: #ffffff;
  border: 1px solid #d8dee8;
  border-radius: 8px;
  padding: 20px;
}

.panel h2 {
  font-size: 1rem;
  margin: 0 0 8px;
}

.panel p {
  color: #5f6f87;
  line-height: 1.6;
}

.data-table {
  background: #ffffff;
  border: 1px solid #d8dee8;
  border-collapse: collapse;
  border-radius: 8px;
  overflow: hidden;
  width: 100%;
}

.data-table td {
  border-bottom: 1px solid #e5e9f0;
  padding: 14px 16px;
}

@media (max-width: 760px) {
  .app-header {
    height: auto;
    padding: 16px;
  }

  .app-body {
    grid-template-columns: 1fr;
  }

  .app-sidebar {
    padding: 12px 16px;
  }

  .app-sidebar nav,
  .header-actions,
  .page-heading {
    flex-wrap: wrap;
  }

  .app-sidebar nav,
  .panel-grid {
    grid-template-columns: 1fr;
  }

  .page {
    padding: 28px 16px;
  }
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
