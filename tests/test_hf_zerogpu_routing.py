import json
from unittest.mock import MagicMock, patch
import pytest

from hares.ai.schemas import TextTriageInferenceResult
from hares.ai.slm_client import LocalSLMClient


class TestHuggingFaceZeroGPURouting:
    """Test suite for Hugging Face ZeroGPU neural engine routing and resilience."""

    def test_init_hf_zerogpu_defaults(self):
        """Validates that LocalSLMClient correctly loads HF ZeroGPU configuration."""
        client = LocalSLMClient(mock_mode=True)
        assert client.hf_space_url == "https://abdullahashraf122-hares-neural-engine.hf.space"
        assert client.hf_space_api_name == "/triage"
        assert client.enable_hf_zerogpu is True

    def test_query_hf_zerogpu_parsing(self):
        """Verifies structured output parsing from Gradio 3-element tuple into TextTriageInferenceResult."""
        client = LocalSLMClient(mock_mode=False)

        mock_payload = {
            "verdict": "RED",
            "risk_score": 0.98,
            "analysis": {
                "is_impersonation": True,
                "impersonated_entity": "Dubai Police",
                "detected_tactics": ["traffic_fine_lure"],
                "confidence_score": 0.98,
                "urgency_or_coercion": True,
                "financial_or_credential_demand": True,
                "reasoning_summary": "Fake traffic fine notice impersonating Dubai Police with urgent demand.",
            },
            "pii_masked": True,
            "sanitized_input": "...",
            "latency_ms": 2400.0,
            "escalation": "https://www.ecrime.ae",
        }
        mock_tuple = (
            "### 🔴 HIGH RISK DETECTED",
            json.dumps(mock_payload),
            "Official advisory in Arabic and English",
        )

        mock_gradio_client = MagicMock()
        mock_gradio_client.predict.return_value = mock_tuple

        with patch.object(client, "_get_hf_client", return_value=mock_gradio_client):
            result = client._query_hf_zerogpu("Urgent fine notice")

        assert isinstance(result, TextTriageInferenceResult)
        assert result.is_impersonation is True
        assert result.impersonated_entity == "Dubai Police"
        assert result.confidence_score == 0.98
        assert "traffic_fine_lure" in result.detected_tactics
        assert result.urgency_or_coercion is True
        assert result.financial_or_credential_demand is True
        assert "Fake traffic fine" in result.reasoning_summary

    def test_tactics_normalization(self):
        """Verifies that non-standard tactics from SLM are mapped to valid TacticType literals."""
        client = LocalSLMClient(mock_mode=False)

        mock_payload = {
            "verdict": "RED",
            "risk_score": 0.92,
            "analysis": {
                "is_impersonation": True,
                "impersonated_entity": "Emirates Post",
                "detected_tactics": ["courier_delivery_unpaid_fee", "kyc_suspension"],
                "confidence_score": 0.92,
                "urgency_or_coercion": False,
                "financial_or_credential_demand": True,
                "reasoning_summary": "Delivery fee lure.",
            },
        }
        mock_tuple = ("Status", json.dumps(mock_payload), "Advisory")

        mock_gradio_client = MagicMock()
        mock_gradio_client.predict.return_value = mock_tuple

        with patch.object(client, "_get_hf_client", return_value=mock_gradio_client):
            result = client._query_hf_zerogpu("Emirates post fee")

        # courier_delivery_unpaid_fee -> courier_delivery_fee, kyc_suspension -> banking_kyc_freeze
        assert "courier_delivery_fee" in result.detected_tactics
        assert "banking_kyc_freeze" in result.detected_tactics

    def test_hf_zerogpu_fallback_resilience(self):
        """Verifies that if HF ZeroGPU fails or times out, client falls back cleanly without 500."""
        client = LocalSLMClient(mock_mode=False)
        client.enable_hf_zerogpu = True

        mock_gradio_client = MagicMock()
        mock_gradio_client.predict.side_effect = TimeoutError("ZeroGPU dynamic queue timeout")

        with patch.object(client, "_get_hf_client", return_value=mock_gradio_client):
            # Should not raise exception, but gracefully fall back
            result = client.triage_text("Urgent fine from Dubai Police at http://police-fake.cc")

        assert isinstance(result, TextTriageInferenceResult)
        assert client.last_provider_used == "offline_heuristics"
        assert result.is_impersonation is True
        assert result.impersonated_entity == "Dubai Police"
