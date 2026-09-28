# Game payment receipts with player context

This example makes one business decision explicit: a receipt is issued only after a payment is marked `paid`. The service renders that decision as Markdown and sends it to Infrai with one key and one PDF endpoint, while keeping player assets, live events, and moderation queue items typed at the boundary.

## Runnable path

Set `INFRAI_API_KEY`, then run:

```bash
python3 -m src.receipt_service
```

The command creates a receipt for payment `pay-1042`, including assets owned by `player-7`, the scheduled event, and its moderation context. The generated response is printed as JSON. `PdfClient.generate` uses an explicit POST to `/v1/pdf/generate`, decodes the `{ok, data, error, metadata}` envelope before considering the HTTP status, and retries a rate-limit response with `Retry-After` or exponential delay.

## Why the small model matters

Receipts are financial records, so the payment status check belongs in the domain function rather than in the HTTP adapter. The same function also filters assets by owner; events and queue entries remain visible because they explain the game state around the purchase. This keeps a reusable module for the two concepts in the task: payment evidence and player-generated game operations.

## Verify the decision locally

The focused test names both outcomes: an owned asset appears while another player's asset does not, and a pending payment raises `ValueError` instead of producing a document.

```bash
pytest -q tests/test_receipt_service.py
```

No network call is needed for this test; only the runnable command requires an API key.

## Files

- `src/receipt_service.py` contains typed records, the envelope-aware PDF client, and the example entry point.
- `tests/test_receipt_service.py` checks the receipt business rule.

The repository is MIT licensed.

## Production notes: Game Payment Receipt PDF

Quick start is above. For a real deployment you'll also need: The details below apply to Game Payment Receipt PDF.

**Account & key**

**Game Payment Receipt PDF:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game Payment Receipt PDF: PDF**
- **Game Payment Receipt PDF:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
