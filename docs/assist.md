# Skylight "Assist" (AI-Assisted Creation)

> **Unofficial reference.** Everything here is reverse-engineered from a single
> user's own web-app traffic. Sections are marked **Confirmed** (observed in
> captured requests/responses) vs **Hypothesis** (inferred, not yet verified).

"Assist" is Skylight's AI/import-assisted creation feature. In the **mobile app**
it is surfaced as a first-class tool ("Assist") and can additionally be fed by
**email** (send it a message and it parses the content into Skylight items). The
web app does not expose an "Assist" UI, but it uses the same backend for AI
generation (e.g. "generate a recipe"), which is how we captured the mechanism.

The backend resource is **`auto_creation_intents`**.

---

## The flow (Confirmed)

Assist is an **async, engine-driven, three-stage** pipeline. Records are created
server-side automatically once the intent is approved — there is **no** separate
confirm/commit call.

```
1. POST /api/frames/{frameId}/auto_creation_intents
       body: { engine, text, engine_inputs, meal_category_id?, created_via, draft_first, ext }
   → 200 { data: { id, attributes: { status: "processing", result: null, ... } } }

2. GET  /api/frames/{frameId}/auto_creation_intents/{id}       (poll)
   → status stays "processing" … then flips to "approved"
   → on approval, attributes.result carries the engine output
     (for meal_sittings_generator: result.new_recipes = [ { title, description } ])

3. GET  /api/frames/{frameId}/auto_creation_intents/{id}/created_items
   → [ { type: "auto_created_item", id, attributes: { class_name, label, sub_label, ... } } ]
     class_name values seen: "Meal::Recipe", "Meal::Sitting"
     each item's `id` is the real record id (usable with /meals/recipes/{id} etc.)
```

See `examples/assist-auto-creation-intent-flow-redacted.json` for a full captured
sequence, and the `Assist` tag in `openapi/openapi.yaml` for schemas.

### Intent lifecycle states (Partially confirmed)
- `processing` — **Confirmed** (initial + during generation).
- `approved` — **Confirmed** (terminal success; `result` populated).
- Failure/rejection states — **Hypothesis**: some terminal error status (e.g.
  `failed`/`rejected`) almost certainly exists but was not captured. Automation
  should treat "not approved after N polls / unknown status" as a stop condition.

---

## Engines (Partially confirmed)

The `engine` field selects what gets generated. `engine_inputs` is an
engine-specific object.

| engine | Confirmed? | Produces | engine_inputs observed |
|---|---|---|---|
| `meal_sittings_generator` | ✅ Confirmed | recipe(s) + meal sitting(s) | `meal_sitting_dates` (YYYY-MM-DD[]), `meal_recipe_source` (`generate`), `meal_mouths_to_feed` (int), `add_to_grocery_list` (bool) |
| (events / lists / chores generators) | ❓ Hypothesis | calendar events, list items, chores | unknown |

There are very likely other engines for the non-meal Assist features (calendar,
lists, to-dos) seen in the mobile app and email ingestion, but their names and
`engine_inputs` shapes have not been captured.

---

## Attachments & the mobile/email path (Hypothesis)

The intent resource includes two fields that were **null** in every captured
(text-prompt) call but strongly imply an attachment-driven variant:

- `attachment_put_url` — almost certainly a **presigned PUT URL**. The client
  would `PUT` a file (photo, PDF, emailed content) to it, then the engine parses
  that attachment instead of a `text` prompt.
- `external_result_url` — possibly where a large/external result is fetched from.

**Working hypothesis**: mobile "Assist" (photo capture) and the email-to-Assist
path funnel through this **same `auto_creation_intents` endpoint**, differing by
(a) a different `engine` and (b) providing an attachment via `attachment_put_url`
rather than a `text` field. If true, Assist is reachable from a web-session token
without intercepting mobile-app traffic.

**Not yet verified.** Confirming this requires either:
- capturing a mobile Assist request (harder — iOS TLS interception), or
- a token-based probe: `POST /auto_creation_intents` with an attachment-oriented
  engine and observing whether a usable `attachment_put_url` is returned, then
  PUTting a test file. Do this only against your own account, gently.

---

## Automation guidance

- **Deterministic recipe creation** → use **`POST /meals/recipes`** directly
  (flat body, synchronous, returns the id). Do **not** emulate the AI intent flow
  for this — it's async and non-deterministic.
- **AI generation** (recipe/meal from a prompt) → use the intent flow above, with
  a bounded poll loop and a timeout. Read the created ids from `created_items`
  rather than parsing `result` if you need to then edit the records.
- The generated recipe `description` follows the same unstructured
  `Ingredients:` / `Instructions:` convention — parse it with
  `scripts/parse_recipe.py` if you need the parts.

---

## Open questions / next captures

1. Terminal failure status value(s) and shape.
2. Other `engine` names + their `engine_inputs` (events, lists, chores).
3. The attachment flow: does `attachment_put_url` populate for some engine, and
   what content types does the parser accept?
4. Relationship between **email-to-Assist** and `auto_creation_intents` (does an
   inbound email create an intent server-side that then shows up here?).
5. `created_via` values other than `app_form` (e.g. an `email`/`mobile` value
   would corroborate the shared-backend hypothesis).
