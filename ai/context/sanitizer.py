import re
import logging

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r"IGNORE\s+PREVIOUS",
    r"\[INST\]",
    r"\[/INST\]",
    r"</s>",
    r"<s>",
    r"<<SYS>>",
    r"<</SYS>>",
    r"\[SYS\]",
    r"\[/SYS\]",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
_HTML_TAGS = re.compile(r"<[^>]+>")


def sanitize(text: str) -> str:
    """Strip HTML tags and remove prompt injection patterns. Logs a warning if any found."""
    cleaned = _HTML_TAGS.sub("", text)
    for pattern in _COMPILED:
        if pattern.search(cleaned):
            logger.warning("Prompt injection pattern detected and removed: %s", pattern.pattern)
            cleaned = pattern.sub("", cleaned)
    return cleaned.strip()
