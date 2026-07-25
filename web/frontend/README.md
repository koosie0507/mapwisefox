# Mapwisefox Frontend

The frontend is a standalone React and Vite SPA.

- Run `npm run dev` for development. Vite proxies `/api` and `/auth` to `http://localhost:8000`.
- Run `npm run build` to create the production app in `dist`.
- The production Docker image uses Caddy to serve `dist` and proxy backend routes on the same public origin.

The rest is history.
