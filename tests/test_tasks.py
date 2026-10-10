import pytest
from hares.workers.tasks import process_incoming_webhook


def test_process_incoming_webhook_green_verdict():
    """Verifies that an official allowlisted domain yields a GREEN verdict."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid.TEST_GREEN_01",
                                    "from": "+971-50-111-2222",
                                    "type": "text",
                                    "text": {"body": "Check report status at https://ecrime.ae/report"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    result = process_incoming_webhook.apply(args=[payload]).get()
    assert result["status"] == "processed"
    assert result["messages_handled"] == 1
    assert len(result["verdicts"]) == 1
    assert result["verdicts"][0]["verdict"] == "GREEN"
    assert result["verdicts"][0]["rule_triggered"] == "allowlist_exact_match"


def test_process_incoming_webhook_red_spoof_verdict():
    """Verifies that a spoofed lookalike domain yields a RED verdict."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid.TEST_RED_01",
                                    "from": "+971-50-333-4444",
                                    "type": "text",
                                    "text": {"body": "Urgent DEWA bill payment overdue: http://dewaa.ae/pay"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    result = process_incoming_webhook.apply(args=[payload]).get()
    assert result["status"] == "processed"
    assert result["messages_handled"] == 1
    assert len(result["verdicts"]) == 1
    assert result["verdicts"][0]["verdict"] == "RED"


def test_process_incoming_webhook_amber_unverified_verdict():
    """Verifies that an unlisted external link defaults to an AMBER caution verdict."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid.TEST_AMBER_01",
                                    "from": "+971-50-555-6666",
                                    "type": "text",
                                    "text": {"body": "Special gift card offer at https://unknown-shopping-outlet.xyz"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    result = process_incoming_webhook.apply(args=[payload]).get()
    assert result["status"] == "processed"
    assert result["messages_handled"] == 1
    assert len(result["verdicts"]) == 1
    assert result["verdicts"][0]["verdict"] == "AMBER"


def test_process_incoming_webhook_empty_payload():
    """Verifies handling of empty webhook entries without failure."""
    payload = {"entry": []}
    result = process_incoming_webhook.apply(args=[payload]).get()
    assert result["status"] == "processed"
    assert result["messages_handled"] == 0

