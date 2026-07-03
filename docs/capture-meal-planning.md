# Capturing Meal Planning & Recipe Endpoints

> **Unofficial reference.** Use only with your own Skylight account. This procedure captures
> `/api/...` request/response *bodies* only — it intentionally never reads the `Authorization`
> header, so your token is not collected. Still redact names, emails, and real IDs before committing.

The goal is to map Skylight's **meal planning / recipe** surface, which is currently undocumented
in `openapi/openapi.yaml` (no Recipes, Meals, MealPlan, or Menu tags exist yet).

---

## Method: in-page network interceptor (works with Claude-in-Chrome)

Rather than hunt through the DevTools Network tab, install a monkeypatch that records every
`/api/` call into a global array. Then walk the UI. Then dump the array as JSON.

### Step 1 — Install the interceptor

Open `https://app.ourskylight.com` (logged in). In the DevTools **Console** (or via the browser
agent's JS execution), paste and run:

```js
(() => {
  if (window.__skyCap) return 'already installed (' + window.__skyCap.length + ' entries)';
  window.__skyCap = [];
  const keep = u => typeof u === 'string' && u.includes('/api/');

  const origFetch = window.fetch;
  window.fetch = async function (...args) {
    const res = await origFetch.apply(this, args);
    try {
      const url = typeof args[0] === 'string' ? args[0] : args[0].url;
      if (keep(url)) {
        const method = (args[1] && args[1].method) || 'GET';
        const reqBody = (args[1] && args[1].body) || null;
        const text = await res.clone().text();
        let body; try { body = JSON.parse(text); } catch { body = text; }
        window.__skyCap.push({ method, url, reqBody, status: res.status, body });
      }
    } catch (e) {}
    return res;
  };

  const open = XMLHttpRequest.prototype.open;
  const send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__cap = { method, url };
    return open.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function (reqBody) {
    this.addEventListener('load', () => {
      try {
        if (this.__cap && keep(this.__cap.url)) {
          let body; try { body = JSON.parse(this.responseText); } catch { body = this.responseText; }
          window.__skyCap.push({ method: this.__cap.method, url: this.__cap.url, reqBody: reqBody || null, status: this.status, body });
        }
      } catch (e) {}
    });
    return send.apply(this, arguments);
  };
  return 'installed';
})();
```

### Step 2 — Walk the meal-planning UI (one action per pause)

Do each of these deliberately so requests are easy to attribute:

1. Open the **Meals / Meal Plan** view → captures the list/read call.
2. Open a **single recipe** → detail call (this reveals the recipe schema).
3. **Add a recipe** to a day / meal slot → the create/assign call (**most important for automation**).
4. **Edit** a planned meal (change date, servings, notes) → update call.
5. **Remove** a planned meal → delete call.
6. If there's a **recipe library or search**, run one search.
7. If **"add ingredients to shopping list"** exists, use it → likely bridges recipes → the
   already-documented Lists API.
8. Open the **week/next-week** view → shows how meal plans are keyed by date (and any pagination).

### Step 3 — Dump the capture

```js
copy(JSON.stringify(window.__skyCap, null, 2));   // copies to clipboard
// or, to view: JSON.stringify(window.__skyCap, null, 2)
```

### Step 4 — Redact before sharing

In the dumped JSON, replace:
- Any real frame ID in URLs → `FRAME_REDACTED`
- Household member names / emails → `REDACTED`
- Real recipe/meal/list IDs → stable placeholders (`RECIPE_1`, `MEAL_1`) **only if** the structure
  (relationships between IDs) matters; otherwise `REDACTED`.
- Photo/asset URLs that embed account identifiers → `REDACTED`

Do **not** redact field *names*, enums, date formats, or structure — those are the whole point.

---

## What to bring back

For each distinct endpoint, one redacted request/response pair is enough to draft its schema.
Note especially:
- The exact path (`/api/frames/{frameId}/...`)
- HTTP method + which query params appeared
- The JSON:API `type` string for each resource (e.g. `recipe`, `meal`, `meal_plan`)
- Any `relationships` (recipe → ingredients, meal → recipe, meal → date/category)

Drop the redacted JSON into `examples/` (e.g. `get-meals-redacted.json`) or paste it back into the
documentation session, and the schemas + `openapi.yaml` paths get generated from it.

---

## Working with recipe text

Recipes are **not structured** — a `meal_recipe`'s ingredients and instructions live as free text
inside its `description` attribute (see the `meal_recipe` schema notes in `openapi/openapi.yaml`).
To turn that blob into `{ingredients: [...], instructions: [...]}` for automation, use the reference
parser:

```bash
# from a captured example, an API response, or a raw resource
python3 scripts/parse_recipe.py examples/get-meals-recipe-redacted.json

# or from raw description text on stdin
printf 'Ingredients:\n1 egg\n\nInstructions:\n1. Fry it' | python3 scripts/parse_recipe.py --text -
```

It handles the observed `Ingredients:` / `Instructions:` convention (plus common header synonyms),
strips step numbering and bullets, and preserves anything unrecognised under `other` rather than
dropping it. Tests: `python3 tests/test_parse_recipe.py`.

