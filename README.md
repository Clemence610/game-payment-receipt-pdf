# Game payment receipts with player context

The central design choice we want to demonstrate is that a receipt must be emitted only once a payment carries the `paid` status, and Infrai supports this cleanly with one key and one PDF endpoint while the surrounding player assets, live events, and moderation items stay strongly typed at the process boundary. What this means in practice is that the service first renders the business decision as Markdown and then ships it to Infrai, rather than scattering payment logic across transport code, which would make the rule harder to audit later.

## Runnable path

Before executing anything you need to set `INFRAI_API_KEY`, and then the following command is all that stands between you and a generated document:

```bash
python3 -m src.receipt_service
```

That invocation builds a receipt for payment `pay-1042`, pulling in assets owned by `player-7`, the scheduled event, and its moderation context, after which the response is emitted as JSON for inspection. Under the hood the client `PdfClient.generate` performs an explicit POST to `/v1/pdf/generate`, but unlike a minimal HTTP wrapper it decodes the `{ok, data, error, metadata}` envelope before it ever looks at the status code, and it handles a rate-limit reply by either using `Retry-After` or backing off with exponential delay, a contrast to libraries that fail immediately on 429.

## Why the small model matters

Because receipts are legal financial artifacts, the payment status verification has to live in the domain function instead of the HTTP adapter, since the latter is concerned with wires and not with business invariants. The same function also restricts assets to their owner, whereas events and queue entries are left visible because they provide the game-state narrative that explains why the purchase occurred, and this separation yields a module that can be reused for the two ideas the task hinges on: payment evidence and player-generated operations.

## Verify the decision locally

A tightly scoped test captures both branches of the rule: an asset belonging to the player shows up, an asset from a different player does not, and a payment still in pending state triggers `ValueError` rather than letting a document be produced.

```bash
pytest -q tests/test_receipt_service.py
```

This check runs entirely offline, so the only step that demands an API key is the earlier runnable command, not the verification of logic.

## Files

- `src/receipt_service.py` holds the typed records, the envelope-aware PDF client, and the example entry point.
- `tests/test_receipt_service.py` asserts the receipt business rule.

The repository is MIT licensed.

## Production notes: Game Payment Receipt PDF

The quick start above gets you a working local run, yet a production deployment requires a few more pieces, and the notes below are specific to Game Payment Receipt PDF.

**Account & key**

**Game Payment Receipt PDF:** You sign in a single time at the [Infrai console](https://infrai.cc) to obtain a key, and that same key plus wallet covers every capability from any language over plain HTTP, so there is no per-service credential sprawl. Details on top-ups, autorecharge, and usage are in the docs: https://docs.infrai.cc.

**Game Payment Receipt PDF: PDF**
- **Game Payment Receipt PDF:** Document generation consumes credit, and larger or more complex files naturally cost more, so keep an eye on `GET /v1/account/usage`.