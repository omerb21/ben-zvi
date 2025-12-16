from __future__ import annotations

from app.services import justification_forms_signatures_utils as _sig_utils


def _get_inherited_ft(field_obj) -> str:
    current = field_obj
    visited = set()
    while current is not None:
        try:
            obj = _sig_utils._pdf_deref(current)
            obj_id = id(obj)
            if obj_id in visited:
                break
            visited.add(obj_id)

            ft = obj.get("/FT")
            if ft:
                return str(ft)

            current = obj.get("/Parent")
        except Exception:
            break
    return ""


def _get_full_field_name(field_obj) -> str:
    parts = []
    current = field_obj
    visited = set()
    while current is not None:
        try:
            obj = _sig_utils._pdf_deref(current)
            obj_id = id(obj)
            if obj_id in visited:
                break
            visited.add(obj_id)

            name = obj.get("/T")
            if name:
                parts.append(str(name))

            current = obj.get("/Parent")
        except Exception:
            break
    parts.reverse()
    return ".".join(parts)


def _is_signature_field(annot) -> bool:
    ft = _get_inherited_ft(annot)
    if ft == "/Sig":
        return True

    full_name = _get_full_field_name(annot).lower()
    if "sig" in full_name or "חתימ" in full_name:
        return True

    field_name = annot.get("/T")
    if field_name:
        name_str = str(field_name).lower()
        if "sig" in name_str or "חתימ" in name_str:
            return True

    return False
