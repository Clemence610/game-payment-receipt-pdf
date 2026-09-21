import pytest
from src.receipt_service import Payment, GameAsset, LiveEvent, ModerationQueueItem, receipt_markdown


def test_receipt_includes_owned_assets_and_game_context():
    payment = Payment("p1", "player-a", "Starter", "2.00", "USD", "paid")
    markdown = receipt_markdown(payment, [GameAsset("a1", "player-a", "Sword"), GameAsset("a2", "player-b", "Shield")], [LiveEvent("e1", "Launch", "tomorrow")], [ModerationQueueItem("q1", "a1", "review")])
    assert "Sword" in markdown and "Shield" not in markdown
    assert "Launch" in markdown and "review" in markdown


def test_unpaid_payment_is_not_issued():
    with pytest.raises(ValueError):
        receipt_markdown(Payment("p2", "player-a", "Starter", "2.00", "USD", "pending"), [], [], [])
