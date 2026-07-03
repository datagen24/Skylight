# Unofficial Skylight API (Community Reference)

> **Purpose**: A community-maintained reference for documenting the network endpoints used by the Skylight apps, based on observed traffic.  
> **Scope**: Reverse-engineered, incomplete, and **unofficial**. Not affiliated with Skylight. For research, interoperability, and educational use only.

---

## Disclaimers

- Respect the app’s Terms of Service and privacy laws. Only capture traffic from your own account/devices.
- Redact personal data and secrets (tokens, emails, IDs tied to real people) before committing.
- This repository **does not** encourage abusing the service or bypassing protections.

## How this repo is organized

- `docs/openapi/openapi.yaml` — A living OpenAPI 3.0 spec for discovered endpoints.
- `examples/` — Example requests/responses (redacted).
- `docs/` — How-to guides (capturing traffic, auth notes, etc.).
- `CONTRIBUTING.md` — How to add endpoints, schemas, and examples safely.
- `SECURITY.md` — Responsible redaction guidelines.
- `LICENSE` — Default: CC BY-NC 4.0 (adjust as you prefer).

## Base URL

```
https://app.ourskylight.com
```

Most endpoints appear to be under `/api/...` and follow a **JSON:API** style structure (`type`, `id`, `attributes`, `relationships`). Note some write endpoints (e.g. creating a meal sitting) use a **flat** request body instead — see the spec for per-endpoint details.

## Authentication

Observed requests use one of two `Authorization` header styles:

```
Authorization: Bearer <REDACTED>    # standard bearer token (likely JWT)
Authorization: Basic <REDACTED>     # opaque token, NOT username:password
```

Tokens typically rotate; treat them as secrets and never commit real values.

See **[docs/auth.md](docs/auth.md)** for how to capture and use your own token safely.

## Documented coverage

Endpoints are grouped by tag in the OpenAPI spec. Current areas:

- **Frames** — household/device frames.
- **Chores** — list (by date range) and create; categories and reward points.
- **Categories** · **Devices** · **Lists** (+ list items) · **Task Box**.
- **Calendars** — source calendars and calendar events (schemas partial).
- **Rewards** — rewards and reward points.
- **Meals** / **Recipes** — meal categories, the recipe box, and the meal plan
  (`meal_sitting` create + per-date instance edit/delete), plus the recipe→grocery
  bridge (`add_to_grocery_list`). See [docs/capture-meal-planning.md](docs/capture-meal-planning.md).

Coverage is partial and evolving; the spec marks placeholder/uncaptured fields inline.

## Tools & Workflow

- **Capture**: Charles/Proxyman/mitmproxy (with SSL cert installed), or the in-browser
  network logger in [docs/capture-meal-planning.md](docs/capture-meal-planning.md).
- **Inspect**: Confirm hostnames and query params; export sanitized samples to `examples/`.
- **Document**: Update `docs/openapi/openapi.yaml` and add any new schemas/components.
- **Test**: Use Postman/Insomnia to verify requests (with your own credentials).

## Interactive Docs

Explore the API spec in your browser:

- [Swagger UI](https://datagen24.github.io/Skylight/swagger.html) — interactive “try it” interface
- [Redoc](https://datagen24.github.io/Skylight/redoc.html) — clean reference-style docs

> On GitHub Pages (source = the `/docs` folder) these are served at:  
> https://datagen24.github.io/Skylight/swagger.html  
> https://datagen24.github.io/Skylight/redoc.html

## Roadmap

- Add auth/login flow (if observable).
- Fill remaining placeholder schemas: calendar events, source calendars, devices.
- Capture `POST /meals/recipes` (create-recipe), instance `PATCH` bodies, and the
  `add_to_grocery_list` response.
- Note rate limits and error shapes; add shared error/response components.

---

Maintainers: add yourself to `docs/maintainers.md` if you contribute regularly.

## Changelog

### v0.4.0
- Added **Meals** and **Recipes** coverage from captured web-app traffic:
  meal categories, recipes (list/get/update, add-to-grocery-list), and the meal
  plan (`meal_sitting` create + per-date instance edit/delete), plus
  `auto_creation_intents`.
- Documented meal-plan quirks: flat (non-JSON:API) create body, date-range
  (infinite-scroll) pagination, and client-side recipe search.
- Added redacted examples: `get-meals-categories`, `post-meals-sitting`,
  `get-meals-sitting-instances`, `get-meals-recipe`.
- Added `docs/capture-meal-planning.md` (repeatable in-browser capture guide).
- **Recipe shape confirmed**: recipes are **not structured** — ingredients and
  instructions live as free text inside `description` (under "Ingredients:" /
  "Instructions:" headers). No ingredients array, servings, time, or image field
  in the observed payload. Consumers must parse `description` to extract items.
- **Still uncaptured**: `POST /meals/recipes` (create-recipe flow), the
  `PATCH .../instances/{date}` request body, and the `add_to_grocery_list`
  response body.

### v0.3.0
- Added Frames, Source Calendars, Calendar Events, Rewards, Reward Points paths.
- Expanded `list_item` schema; corrected color fields to accept `#RRGGBB`.
- Ensured `chore.status` captured explicitly.

### v0.2.0
- Added Categories, Devices, Lists, Task Box endpoints and schemas.
- Added Basic token auth scheme in addition to Bearer.
