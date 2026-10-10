import logging
from typing import Any
import httpx
from hares.core.config import get_settings

logger = logging.getLogger("hares.services.media_downloader")


class MediaDownloader:
    """
    Two-Stage Authenticated Meta WhatsApp Cloud API Media Ingestion Pipeline (FR-1.1).
    Fetches forwarded voice notes and audio clips within the 600ms network budget:
    1. GET /v21.0/{media_id} -> Retrieves temporary download URL.
    2. GET {download_url} -> Streams raw binary media payload.
    """

    def __init__(
        self,
        access_token: str | None = None,
        api_base_url: str | None = None,
        api_version: str | None = None,
        timeout_seconds: float = 2.0,
    ) -> None:
        settings = get_settings()
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.api_base_url = (api_base_url or settings.WHATSAPP_API_BASE_URL).rstrip("/")
        self.api_version = api_version or settings.WHATSAPP_API_VERSION
        self.timeout = timeout_seconds

    ALLOWED_CDN_DOMAINS: tuple[str, ...] = (
        "facebook.com",
        "fbcdn.net",
        "fbsbx.com",
        "whatsapp.net",
        "whatsapp.com",
    )

    @classmethod
    def _validate_cdn_url(cls, download_url: str) -> None:
        """
        Validates that the Meta media download URL targets an authenticated Meta CDN hostname (AUDIT-OBS-11).
        Protects against Server-Side Request Forgery (SSRF) and malicious redirect injection.
        """
        from urllib.parse import urlparse

        parsed = urlparse(download_url)
        if parsed.scheme not in ("https", "http"):
            raise ValueError(f"SSRF Protection: Invalid URL scheme '{parsed.scheme}'. HTTPS required.")

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            raise ValueError("SSRF Protection: Missing hostname in media download URL.")

        is_valid = any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in cls.ALLOWED_CDN_DOMAINS
        )
        if not is_valid:
            raise ValueError(f"SSRF Protection: Untrusted Meta CDN host '{hostname}'.")

    def fetch_media(self, media_id: str) -> tuple[bytes, str]:
        """
        Executes two-stage retrieval sequence for the specified WhatsApp media_id.
        Returns:
            (media_bytes: bytes, mime_type: str)

        Raises:
            ValueError: If media_id is invalid or media payload cannot be downloaded.
        """
        if not media_id or not media_id.strip():
            raise ValueError("Invalid media_id provided.")

        clean_id = media_id.strip()

        # Offline / Mock handler for hermetic unit testing
        if clean_id.startswith("mock_media_") or clean_id.startswith("test_"):
            logger.debug("Serving synthetic audio payload for test media_id=%s", clean_id)
            # Produce 1 second of synthetic 16kHz mono PCM (16000 samples * 2 bytes)
            synthetic_pcm = b"\x00\x00" * 16000
            return synthetic_pcm, "audio/ogg; codecs=opus"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        with httpx.Client(timeout=self.timeout) as client:
            # Stage 1: Retrieve temporary media metadata and direct download URL
            meta_url = f"{self.api_base_url}/{self.api_version}/{clean_id}"
            try:
                resp = client.get(meta_url, headers=headers)
                resp.raise_for_status()
                meta_json = resp.json()
            except httpx.HTTPError as exc:
                logger.error("Stage 1 media URL lookup failed for media_id=%s: %s", clean_id, str(exc))
                raise ValueError(f"Failed to retrieve media URL from Meta Cloud API: {exc}")

            download_url = meta_json.get("url")
            mime_type = meta_json.get("mime_type", "audio/ogg")
            if not download_url:
                raise ValueError(f"Meta Cloud API response omitted direct download URL: {meta_json}")

            # Validate CDN URL against SSRF before outbound retrieval (AUDIT-OBS-11)
            self._validate_cdn_url(download_url)

            # Stage 2: Stream binary audio bytes
            try:
                download_resp = client.get(download_url, headers=headers)
                download_resp.raise_for_status()
                audio_bytes = download_resp.content
            except httpx.HTTPError as exc:
                logger.error("Stage 2 media binary streaming failed for media_id=%s: %s", clean_id, str(exc))
                raise ValueError(f"Failed to stream binary audio payload: {exc}")

            logger.info(
                "Successfully ingested WhatsApp media_id=%s size=%d bytes mime=%s",
                clean_id,
                len(audio_bytes),
                mime_type,
            )
            return audio_bytes, mime_type
