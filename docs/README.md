# Docs Site

Two static viewers are included, both in this `docs/` folder:
- `swagger.html` (Swagger UI)
- `redoc.html` (Redoc)
- `index.html` (landing page)

They load the spec from `openapi/openapi.yaml` (i.e. `docs/openapi/openapi.yaml`).

## GitHub Pages

There is no Actions workflow in this repo; Pages is served directly from the folder:

1. Push to `main`.
2. In repo **Settings → Pages**, set **Source** to **Deploy from a branch**,
   branch **`main`**, folder **`/docs`**.
3. Visit:
   - `https://datagen24.github.io/Skylight/swagger.html`
   - `https://datagen24.github.io/Skylight/redoc.html`

Because Pages serves the `/docs` folder as the site root, the spec resolves at
`https://datagen24.github.io/Skylight/openapi/openapi.yaml` (the absolute URL
the viewers reference).

## Local (no build tools)

Serve this `docs/` folder over HTTP:
```bash
# from repo root
python3 -m http.server 8080 --directory docs
# then browse http://localhost:8080/swagger.html
```
