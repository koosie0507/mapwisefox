# Mapwisefox Frontend

The frontend is a standalone React and Vite SPA.

- Run `npm run dev` for development. Vite proxies `/api` and `/auth` to `http://localhost:8000`.
- Run `npm run build` to create the production app in `dist`.
- In production, serve `dist` with SPA fallback and proxy `/api` and `/auth` to the backend on the same public origin.
- The `frontend-runtime` Docker target provides this setup and reads the backend origin from `BACKEND_URL`.

The rest is history.
