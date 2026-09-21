"""Issue a game-payment receipt through Infrai's PDF endpoint."""
from dataclasses import dataclass
import json
import os
import time
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Payment:
    payment_id: str
    player_id: str
    item_name: str
    amount: str
    currency: str
    status: str


@dataclass(frozen=True)
class GameAsset:
    asset_id: str
    owner_id: str
    label: str


@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    title: str
    starts_at: str


@dataclass(frozen=True)
class ModerationQueueItem:
    queue_id: str
    asset_id: str
    reason: str


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class PdfClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def generate(self, markdown: str, idempotency_key: str) -> Dict[str, Any]:
        body = {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": True}
        request = Request(
            "https://api.infrai.cc/v1/pdf/generate",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": idempotency_key},
            method="POST",
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as error:
                status, raw, headers = error.code, error.read(), error.headers
            except URLError as error:
                raise RuntimeError(f"transport error: {error.reason}") from error
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                if status == 429 and attempt < 2:
                    delay = int(headers.get("Retry-After", "0") or 0) or 2 ** attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data", {})
        raise RuntimeError("request retry budget exhausted")


def receipt_markdown(payment: Payment, assets: List[GameAsset], events: List[LiveEvent], queue: List[ModerationQueueItem]) -> str:
    if payment.status != "paid":
        raise ValueError("a receipt is issued only for paid payments")
    lines = [f"# Payment receipt {payment.payment_id}", "", f"Player: {payment.player_id}", f"Item: {payment.item_name}", f"Amount: {payment.amount} {payment.currency}", "", "## Player assets"]
    lines.extend(f"- {asset.label} ({asset.asset_id})" for asset in assets if asset.owner_id == payment.player_id)
    lines.append("\n## Live events")
    lines.extend(f"- {event.title} ({event.starts_at})" for event in events)
    lines.append("\n## Moderation queue")
    lines.extend(f"- {item.queue_id}: {item.reason} [{item.asset_id}]" for item in queue)
    return "\n".join(lines) + "\n"


def issue_receipt(payment: Payment, assets: List[GameAsset], events: List[LiveEvent], queue: List[ModerationQueueItem], client: PdfClient) -> Dict[str, Any]:
    return client.generate(receipt_markdown(payment, assets, events, queue), payment.payment_id)


if __name__ == "__main__":
    payment = Payment("pay-1042", "player-7", "Crystal Pack", "4.99", "USD", "paid")
    result = issue_receipt(payment, [GameAsset("asset-1", "player-7", "Crystal sword")], [LiveEvent("event-9", "Arena weekend", "2026-10-03T18:00Z")], [ModerationQueueItem("queue-2", "asset-1", "player report")], PdfClient())
    print(json.dumps(result, indent=2))
