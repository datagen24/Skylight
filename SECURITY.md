# Security & Redaction Guidelines

This repository contains **unofficial** and **reverse‑engineered** documentation.

- Do **not** commit secrets: tokens, cookies, API keys, private emails, phone numbers.
- Redact IDs that can be tied to real people. Use placeholders like `REDACTED`.
- Avoid including full timestamps if unnecessary; consider truncation.
- If you believe something sensitive slipped in, open a removal PR immediately.

## Field-specific redaction notes

Some fields look like harmless identifiers but are actually secrets or PII:

- **`calendar_event.calendar_id`** — a live `webcal://` **subscription URL** that
  functions like a bearer credential for that calendar feed. Treat as a secret,
  not an id. Redact to e.g. `CALENDAR_SUBSCRIPTION_URL_REDACTED`.
- **`calendar_event`**: `summary`, `description`, `location`, `owner_email`,
  `invited_emails` are personal — redact values, keep field names/types.
- **`calendar_account.email`** and **`active_calendars[].id` / `.name`** — the id
  is often the account's email address; redact to `REDACTED_EMAIL` / `REDACTED`.
- **`calendar_event.uid`** — usually opaque, but some sync sources encode
  email-shaped values here; redact if it looks like an address.

If you represent Skylight and want something removed, open an issue or PR and we’ll comply.
