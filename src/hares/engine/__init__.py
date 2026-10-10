"""
Deterministic Verification Engine for Project Hares.
Implements exact registrable domain allowlisting, IDN homograph & Punycode spoof detection,
bilingual entity extraction & PII sanitization, and tri-state verdict synthesis.
"""

from hares.engine.allowlist import AllowlistEngine
from hares.engine.homograph import HomographDetector
from hares.engine.sanitizer import EntityExtractor, PIIScrubber
from hares.engine.verdict import VerdictSynthesizer, TriageVerdict

__all__ = [
    "AllowlistEngine",
    "HomographDetector",
    "EntityExtractor",
    "PIIScrubber",
    "VerdictSynthesizer",
    "TriageVerdict",
]
