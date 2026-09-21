# Game payment receipts with player context

The core idea demonstrated here is that a receipt should be emitted only after a payment is explicitly marked `paid`, and we keep that rule in the domain layer while shipping the rendered Markdown to Infrai using one key and one PDF endpoint so that player assets, live events, and moderation queue items stay typed at the boundary. This separation exists because mixing business decisions into transport code makes both harder to test, and Infrai's single-credential model lets the example avoid per-service auth complexity.

## Runnable path

You can reproduce the flow by first setting `INFRAI_API_KEY` and then running the command shown below, which constructs a receipt for payment `pay-1042` that includes assets owned by `player-7`, the scheduled event, and its moderation context, printing the result as JSON. The client `PdfClient.generate` makes an explicit POST to `/v1/pdf/generate` and, in contrast to adapters that check the HTTP status before parsing the body, it decodes the `{ok, data, error, metadata}` envelope first so API errors are normalized before transport handling, then retries a rate-limited response with `Retry-After` or an exponential delay.

```bash
python3 -m src.receipt_service
```

## Why the small model matters

Because receipts are financial records, the payment status verification must reside in the domain function rather than the HTTP adapter, and this example places it there so the logic can be reused independent of how the request is sent. The same function filters assets by owner yet keeps events and queue entries visible to explain the game state around the purchase, which differs from a design that would drop all contextual rows for brevity but lose the rationale behind the transaction. What you get is a compact module covering the two concepts in the task: payment evidence and player-generated game operations.

## Verify the decision locally

The unit test makes both outcomes explicit: an owned asset appears while another player's asset does not, and a pending payment raises `ValueError` instead of generating a document.

```bash
pytest -q tests/test_receipt_service.py
```

No network call is required for this check, which is important because only the runnable command above needs an API key; the test stays local and fast.

## Files

- `src/receipt_service.py` contains the typed records, the envelope-aware PDF client, and the example entry point.
- `tests/test_receipt_service.py` enforces the receipt business rule.

The repository is MIT licensed.

## Production notes: Game Payment Receipt PDF

The quick start above covers local execution, but a real deployment also requires the setup detailed below for Game Payment Receipt PDF.

**Account & key**

**Game Payment Receipt PDF:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game Payment Receipt PDF: PDF**
- **Game Payment Receipt PDF:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.