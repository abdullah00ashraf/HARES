import logging
import re
from typing import Any

# Pattern matching UAE local/international phone numbers and generic 10-15 digit sequences
PHONE_PATTERN = re.compile(
    r"(?:\+?971[\s\-]?(?:5[0124568]|2|3|4|6|7|9)[\s\-]?\d{7}"
    r"|(?:\b05[0124568][\s\-]?\d{7}\b)"
    r"|(?:\+?\b[1-9]\d{9,14}\b))"
)


def redact_phone_numbers(text: str) -> str:
    """Replaces any raw telephone numbers within text with [REDACTED_PHONE]."""
    if not isinstance(text, str):
        return text
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", text)


class PhoneSanitizingFilter(logging.Filter):
    """
    Centralized logging filter enforcing Class B PII protection (FR-4.1, AUDIT-OBS-13).
    Recursively scrubs any raw phone numbers from log messages, format args, and tracebacks
    before records are dispatched to console or sinks.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # 1. Scrub record message if string
        if isinstance(record.msg, str):
            record.msg = redact_phone_numbers(record.msg)

        # 2. Scrub record args
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    redact_phone_numbers(arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: (redact_phone_numbers(v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }

        # 3. Scrub exc_text if already rendered
        if record.exc_text and isinstance(record.exc_text, str):
            record.exc_text = redact_phone_numbers(record.exc_text)

        # 4. Scrub stack_info if present
        if record.stack_info and isinstance(record.stack_info, str):
            record.stack_info = redact_phone_numbers(record.stack_info)

        return True


def configure_logging(level: str = "INFO") -> None:
    """
    Configures application-wide logging with attached PhoneSanitizingFilter.
    Ensures zero raw phone numbers escape into terminal outputs or Docker logs.
    """
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    sanitizer = PhoneSanitizingFilter()

    # Ensure all existing and newly created handlers have the sanitizer filter
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        handler.addFilter(sanitizer)
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            # Avoid duplicate filters
            if not any(isinstance(f, PhoneSanitizingFilter) for f in handler.filters):
                handler.addFilter(sanitizer)

    # Also add filter directly to root logger
    if not any(isinstance(f, PhoneSanitizingFilter) for f in root_logger.filters):
        root_logger.addFilter(sanitizer)
