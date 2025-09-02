# Mapwisefox Frontend

The frontend code for the Mapwisefox web app uses React and Vite. The setup is
standard. What's relevant:

- either run `npm run dev` (for development) or `npm run build` (production) __before__ starting the FastAPI BFF
- include `MWF_WEB_DEBUG=1` in the FastAPI app env to enable development mode
- debug/development mode is not available in Docker

The rest is history.