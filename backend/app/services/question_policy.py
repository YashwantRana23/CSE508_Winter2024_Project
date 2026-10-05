"""Conservative source-scope checks, independent of learned query labels.

These patterns detect requests needing current-law or applicability evidence;
they never determine which statute legally applies or use a legal cutoff date.
"""
import re

_NEW_STATUTES = re.compile(
    r"\b(?:bns|bnss|bsa|bharatiya\s+(?:nyaya|nagarik\s+suraksha|sakshya)\s+sanhita|bharatiya\s+sakshya\s+adhiniyam)\b", re.I
)
_CURRENT_LEGAL = re.compile(
    r"\b(?:current|latest|new|updated|present)\s+(?:(?:indian|criminal|applicable|penal)\s+){0,3}"
    r"(?:law|laws|statute|statutes|provision|provisions|amendment|amendments|punishment|penalty|code)\b"
    r"|\b(?:currently|still)\s+(?:in\s+force|apply|applies|govern|governs|applicable|valid|enforced|legal)\b"
    r"|\b(?:law|laws|punishment|penalty|provision|provisions)\s+(?:in\s+india\s+)?(?:today|now|currently)\b"
    r"|\b(?:applies|apply|applicable|governs|in\s+force)\b[^.!?\n]{0,40}\b(?:today|now|currently)\b"
    r"|\b(?:today|currently|now)\s+(?:applicable|in\s+force|enforced)\b", re.I
)
_APPLICABILITY = re.compile(
    r"\b(?:does|do|will|would|can|could|should|may|is|are)\b[^.!?\n]{0,55}\b(?:apply|applies|applicable|govern|governs)\b"
    r"|\b(?:which|what)\s+(?:law|statute|section|provision|code)\b[^.!?\n]{0,45}\b(?:apply|applies|applicable|govern|governs|use|used)\b"
    r"|\b(?:will|would|can|could|may)\b[^.!?\n]{0,45}\b(?:charged|prosecuted|convicted|punished)\b"
    r"|\b(?:what|which)\s+(?:punishment|penalty|sentence|charge)\s+(?:for|applies|will|would)\b", re.I
)
_HISTORICAL_REFERENCE = re.compile(
    r"\b(?:old|historical|former)\s+(?:ipc|indian\s+penal\s+code)\b"
    r"|\b(?:this|selected)\s+(?:book|passage|textbook)\b", re.I
)
_EVENT = re.compile(r"\b(?:offen[cs]e|crime|incident|conduct|case|act|murder|theft|law|statute|section|provision|code|ipc)\b", re.I)
_YEAR = re.compile(r"\b(?:18|19|20|21)\d{2}\b")


def source_scope_reason(question: str) -> str | None:
    if _NEW_STATUTES.search(question):
        return "This question mentions BNS/BNSS/BSA material that is not verified in the selected source."
    if _CURRENT_LEGAL.search(question):
        return "This question asks about current law or present applicability."
    if any(_APPLICABILITY.search(clause) and _EVENT.search(clause) and _YEAR.search(clause)
           for clause in re.split(r"[.!?;\n]", question)):
        return "A dated event requires verified applicability and effective-date evidence. The selected source has no such verification."
    return None


def explicit_historical_reference(question: str) -> bool:
    """A conflict cue only; it must never override source_scope_reason."""
    return bool(_HISTORICAL_REFERENCE.search(question))
