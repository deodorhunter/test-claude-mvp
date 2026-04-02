import re
import logging

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    # LLaMA / Mistral special tokens
    r"IGNORE\s+PREVIOUS",
    r"\[INST\]",
    r"\[/INST\]",
    r"</s>",
    r"<s>",
    r"<<SYS>>",
    r"<</SYS>>",
    r"\[SYS\]",
    r"\[/SYS\]",
    # Role-override patterns (ChatML / raw role injection)
    r"^(SYSTEM|USER|ASSISTANT)\s*:",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    # Jailbreak / DAN patterns
    r"DAN\s+mode",
    r"\bjailbreak\b",
    r"ignore\s+all\s+previous\s+instructions?",
    # Role reversal / persona hijack
    r"you\s+are\s+now\s+(an?\s+)?(different|new|unrestricted|evil|uncensored)",
    # Prompt boundary / delimiter injection
    r"-{3,}\s*(END|STOP|RESET)\s*-{3,}",
    r"###\s*(SYSTEM|INSTRUCTION)",
    # Template / Jinja injection ({{ ... }})
    r"\{\{.*?\}\}",
    # XML system/instruction tag injection (primary OpenClaw vector)
    r"</?instructions\b",
    r"</?system\b",
    r"</?prompt\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_PATTERNS]
_HTML_TAGS = re.compile(r"<[^>]+>")


def sanitize(text: str) -> str:
    """Strip HTML tags and remove prompt injection patterns. Logs a warning if any found."""
    cleaned = _HTML_TAGS.sub("", text)
    for pattern in _COMPILED:
        if pattern.search(cleaned):
            logger.warning("Prompt injection pattern detected and removed: %s", pattern.pattern)
            cleaned = pattern.sub("", cleaned)
    return cleaned.strip()
