import re


def normalize_zm_phone(raw):
    """
    Lipila requires Zambian numbers as `260XXXXXXXXX` (country code, no
    `+`, no leading 0) — runners naturally type `0977...`, `+260977...`,
    or `260977...`; normalize all three rather than making the format
    the runner's problem.
    """

    digits = re.sub(r"\D", "", raw or "")

    if digits.startswith("260") and len(digits) == 12:
        return digits

    if digits.startswith("0") and len(digits) == 10:
        return "260" + digits[1:]

    if len(digits) == 9:
        return "260" + digits

    # Doesn't match a known shape — pass through as-is so Lipila's own
    # validation error surfaces rather than silently mangling it further.
    return digits
