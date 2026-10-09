import pytest
from hares.workers.tasks import process_incoming_webhook


def test_process_incoming_webhook_success():
    """Verifies synchronous execution of Celery worker task processing a WhatsApp payload."""
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "id": "wamid.HBgLM...",
                                    "from": "+971-50-123-4567",
                                    "type": "text",
                                    "text": {"body": "Traffic fine payment link: https://dubai-police.scam"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    # Execute task synchronously via Celery .apply()
    result = process_incoming_webhook.apply(args=[payload]).get()
    assert result["status"] == "processed"
    assert result["messages_handled"] == 1


def test_process_incoming_webhook_empty_payload():
    """Verifies handling of empty webhook entries without failure."""
    payload = {"entry": []}
    result = process_incoming_webhook.apply(args=[payload]).get()
    assert result["status"] == "processed"
    assert result["messages_handled"] == 0
