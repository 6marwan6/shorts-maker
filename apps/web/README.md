# apps/web

Next.js 16.3 App Router frontend (impl plan §1.2). Strict TypeScript, Tailwind CSS 4, Zod,
TanStack Query. Part of the `shorts-maker` pnpm workspace -- run all commands from the repo
root (`pnpm --filter web <script>`), not from inside this directory, so the workspace lockfile
stays authoritative.

No video-processing logic lives here (impl plan §1.2): this app only talks to the FastAPI
backend (`apps/api`) and to R2 via presigned URLs issued by that backend.
