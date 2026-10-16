import io
import logging
import re
from typing import Any
from PIL import Image

logger = logging.getLogger("hares.engine.ocr")


class OCREngine:
    """
    Sovereign Image OCR Extractor (FR-2.1, FR-4.1).
    Extracts printed and digital text from forwarded screenshots, SMS screenshots,
    payment receipts, and chat screenshots without external cloud APIs.
    """

    def __init__(self) -> None:
        self._rapidocr_instance: Any | None = None
        self._initialized = False

    def _get_ocr_engine(self) -> Any | None:
        """Lazy-initializes RapidOCR engine if local ONNX weights are present."""
        if not self._initialized:
            self._initialized = True
            try:
                # Guard against network hang in air-gapped environments
                from rapidocr_onnxruntime import RapidOCR  # type: ignore

                # RapidOCR without pre-downloaded weights will hang attempting downloads; catch gracefully
                self._rapidocr_instance = RapidOCR()
                logger.info("RapidOCR ONNX engine initialized successfully.")
            except ImportError:
                logger.debug("RapidOCR package not installed; falling back to metadata OCR.")
            except Exception as exc:
                logger.warning("RapidOCR initialization failed: %s; falling back to metadata OCR.", str(exc))
                self._rapidocr_instance = None
        return self._rapidocr_instance

    def extract_text_from_bytes(self, image_bytes: bytes, filename_hint: str = "screenshot.png") -> str:
        """
        Extracts visible text and embedded threat indicators from raw image bytes.
        """
        if not image_bytes or len(image_bytes) < 16:
            return ""

        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.width < 10 or image.height < 10:
                logger.warning("Uploaded image %s dimensions too small (%dx%d)", filename_hint, image.width, image.height)
                return ""

            # 1. Fast Sovereign Ingress: Image metadata & EXIF / comment inspection
            metadata_strings: list[str] = []
            info = image.info or {}
            for key, val in info.items():
                if isinstance(val, str) and len(val.strip()) > 3:
                    metadata_strings.append(val.strip())
            if metadata_strings:
                extracted_meta = "\n".join(metadata_strings).strip()
                logger.info("Extracted %d metadata text lines from %s", len(metadata_strings), filename_hint)
                return extracted_meta

            # Convert to standard RGB for neural OCR
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            # 2. Secondary Engine: RapidOCR ONNX runtime if available locally
            engine = self._get_ocr_engine()
            if engine is not None:
                try:
                    # RapidOCR accepts bytes, PIL Image, or numpy array
                    ocr_results, _ = engine(image_bytes)
                    if ocr_results:
                        detected_lines = [
                            item[1] for item in ocr_results if len(item) > 1 and item[1] and str(item[1]).strip()
                        ]
                        extracted_text = "\n".join(detected_lines).strip()
                        logger.info(
                            "OCR extracted %d lines (%d chars) from %s",
                            len(detected_lines),
                            len(extracted_text),
                            filename_hint,
                        )
                        return extracted_text
                except Exception as exc:
                    logger.warning("RapidOCR execution failed on %s: %s", filename_hint, str(exc))

            # 2. Secondary Engine: Tesseract if available
            try:
                import pytesseract  # type: ignore

                extracted_text = pytesseract.image_to_string(image).strip()
                if extracted_text:
                    logger.info("pytesseract extracted %d chars from %s", len(extracted_text), filename_hint)
                    return extracted_text
            except (ImportError, Exception):
                pass

            # 3. Tertiary: Image metadata & EXIF / comment string inspection
            metadata_strings: list[str] = []
            info = image.info or {}
            for key, val in info.items():
                if isinstance(val, str) and len(val) > 4:
                    metadata_strings.append(val)

            if metadata_strings:
                return "\n".join(metadata_strings)

            logger.info("Image %s parsed successfully (0 OCR text lines detected)", filename_hint)
            return ""

        except Exception as exc:
            logger.error("Failed to parse image bytes for %s: %s", filename_hint, str(exc))
            return ""
        finally:
            if "image" in locals():
                try:
                    image.close()
                except Exception:
                    pass
            import gc
            gc.collect()
