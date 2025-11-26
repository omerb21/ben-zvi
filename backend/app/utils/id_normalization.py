import re


def normalize_id_number(id_raw) -> str:
    """Normalize Israeli ID number like legacy mini_crm normalize_id.

    Steps (copied logically from legacy implementation):
    - Keep digits only
    - Strip leading zeros
    - Trim trailing zeros when length is greater than 8
    - For 8-digit values ending with 0, drop the last 0 if it yields 7 digits
    """
    if id_raw is None:
        return ""

    s = re.sub(r"\D", "", str(id_raw))
    s = s.lstrip("0")

    while len(s) > 8 and s.endswith("0"):
        s = s[:-1]

    if len(s) == 8 and s.endswith("0"):
        candidate = s[:-1]
        if len(candidate) == 7:
            s = candidate

    return s
