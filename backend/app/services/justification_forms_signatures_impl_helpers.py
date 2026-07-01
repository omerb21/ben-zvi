from __future__ import annotations

import io

from pypdf import PdfReader as PyPdfReader, PdfWriter as PyPdfWriter
from pypdf.generic import ArrayObject, NameObject
from reportlab.pdfgen import canvas

from app.services import justification_forms_signatures_sigfields as _sigfields
from app.services import justification_forms_signatures_utils as _sig_utils


def _collect_sig_fields_from_acroform(reader) -> dict:
    sig_rects_by_page = {}

    try:
        root = reader.trailer.get("/Root")
        if not root:
            return sig_rects_by_page

        root_obj = _sig_utils._pdf_deref(root)
        acroform = root_obj.get("/AcroForm")
        if not acroform:
            return sig_rects_by_page

        acroform_obj = _sig_utils._pdf_deref(acroform)
        fields = acroform_obj.get("/Fields")
        if not fields:
            return sig_rects_by_page

        page_to_index = {}
        for i, page in enumerate(reader.pages):
            page_to_index[id(page.get_object())] = i

        def process_field(field_ref, inherited_ft=""):
            try:
                field = _sig_utils._pdf_deref(field_ref)

                ft = field.get("/FT")
                if ft:
                    current_ft = str(ft)
                else:
                    current_ft = inherited_ft

                field_name = field.get("/T")
                is_sig_by_name = False
                if field_name:
                    name_lower = str(field_name).lower()
                    if "sig" in name_lower or "חתימ" in name_lower:
                        is_sig_by_name = True

                is_sig_field = (current_ft == "/Sig") or is_sig_by_name

                if is_sig_field:
                    rect = field.get("/Rect")
                    page_ref = field.get("/P")
                    if rect and len(rect) == 4 and page_ref:
                        try:
                            page_obj = _sig_utils._pdf_deref(page_ref)
                            page_idx = page_to_index.get(id(page_obj))
                            _sig_utils._append_sig_rect_from_rect(sig_rects_by_page, page_idx, rect, dedupe=False)
                        except Exception:
                            pass

                kids = field.get("/Kids")
                if kids:
                    for kid_ref in kids:
                        process_field(kid_ref, current_ft)

            except Exception:
                pass

        for field_ref in fields:
            process_field(field_ref)

    except Exception:
        pass

    return sig_rects_by_page


def _collect_all_sig_rects(reader) -> dict:
    sig_rects_by_page = {}

    acroform_rects = _collect_sig_fields_from_acroform(reader)
    for page_idx, rects in acroform_rects.items():
        for rect_tuple in rects:
            _sig_utils._append_sig_rect(sig_rects_by_page, page_idx, rect_tuple, dedupe=False)

    for page_idx, page in enumerate(reader.pages):
        annots = page.get("/Annots") or []
        for annot_ref in annots:
            try:
                annot = annot_ref.get_object()
                if not _sigfields._is_signature_field(annot):
                    continue
                rect = annot.get("/Rect")
                _sig_utils._append_sig_rect_from_rect(sig_rects_by_page, page_idx, rect, dedupe=True)
            except Exception:
                continue

    return sig_rects_by_page


def count_signature_fields(source_pdf_bytes: bytes) -> int:
    try:
        reader = PyPdfReader(io.BytesIO(source_pdf_bytes))
    except Exception as exc:
        raise ValueError("INVALID_PDF") from exc

    if not reader.pages:
        raise ValueError("PDF_HAS_NO_PAGES")

    return sum(len(rects) for rects in _collect_all_sig_rects(reader).values())


def _page_content_fingerprint(page) -> tuple:
    content_bytes = []
    contents = page.get("/Contents")
    if contents:
        content_items = contents if isinstance(contents, list) else [contents]
        for item in content_items:
            try:
                obj = _sig_utils._pdf_deref(item)
                if hasattr(obj, "get_data"):
                    content_bytes.append(obj.get_data())
                else:
                    content_bytes.append(repr(obj).encode("utf-8", errors="ignore"))
            except Exception:
                content_bytes.append(repr(item).encode("utf-8", errors="ignore"))

    return (
        str(page.mediabox),
        str(page.get("/Rotate") or 0),
        b"\n".join(content_bytes),
    )


def _map_reference_pages_to_source(source_reader, reference_reader) -> dict[int, int]:
    reference_pages_by_fingerprint: dict[tuple, list[int]] = {}
    for ref_idx, page in enumerate(reference_reader.pages):
        fingerprint = _page_content_fingerprint(page)
        reference_pages_by_fingerprint.setdefault(fingerprint, []).append(ref_idx)

    ref_to_source: dict[int, int] = {}
    for source_idx, page in enumerate(source_reader.pages):
        fingerprint = _page_content_fingerprint(page)
        matches = reference_pages_by_fingerprint.get(fingerprint) or []
        if not matches:
            continue
        ref_to_source[matches.pop(0)] = source_idx

    return ref_to_source


def apply_signature_to_sig_fields(
    source_pdf_bytes: bytes,
    signature_image_data: str,
    reference_pdf_bytes: bytes = None,
    *,
    overlay_fallback=None,
) -> bytes:
    if not signature_image_data:
        return source_pdf_bytes

    img, img_width, img_height = _sig_utils._load_signature_image(signature_image_data)
    if img is None:
        return source_pdf_bytes

    pdf_stream = io.BytesIO(source_pdf_bytes)
    base_reader = PyPdfReader(pdf_stream)
    if not base_reader.pages:
        return source_pdf_bytes

    writer = PyPdfWriter()
    writer.clone_document_from_reader(base_reader)

    sig_rects_by_page = _collect_all_sig_rects(base_reader)

    if reference_pdf_bytes:
        try:
            ref_reader = PyPdfReader(io.BytesIO(reference_pdf_bytes))
            ref_sig_rects = _collect_all_sig_rects(ref_reader)
            ref_to_source_page = _map_reference_pages_to_source(base_reader, ref_reader)
            for page_idx, rects in ref_sig_rects.items():
                if ref_to_source_page:
                    target_page_idx = ref_to_source_page.get(page_idx)
                    if target_page_idx is None:
                        continue
                else:
                    target_page_idx = page_idx + (len(base_reader.pages) - len(ref_reader.pages))
                    if target_page_idx < 0 or target_page_idx >= len(base_reader.pages):
                        continue
                for rect in rects:
                    _sig_utils._append_sig_rect(sig_rects_by_page, target_page_idx, rect, dedupe=True)
        except Exception:
            pass

    any_signature_drawn = False

    pages_with_sigs = [(idx, sig_rects_by_page[idx]) for idx in sig_rects_by_page if sig_rects_by_page[idx]]

    for page_index, sig_rects in pages_with_sigs:
        if page_index >= len(writer.pages):
            continue

        any_signature_drawn = True
        page = writer.pages[page_index]
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(page_width, page_height))

        for llx, lly, urx, ury in sig_rects:
            box_w = max(urx - llx, 1.0)
            box_h = max(ury - lly, 1.0)

            scale = min(box_w / img_width, box_h / img_height, 1.0)
            draw_w = img_width * scale
            draw_h = img_height * scale

            x = llx + (box_w - draw_w) / 2.0
            y = lly + (box_h - draw_h) / 2.0

            c.drawImage(img, x, y, width=draw_w, height=draw_h, mask="auto")

        c.save()
        buf.seek(0)

        overlay_reader = PyPdfReader(buf)
        page.merge_page(overlay_reader.pages[0])

    if not any_signature_drawn:
        if overlay_fallback is not None:
            return overlay_fallback(
                source_pdf_bytes,
                free_text=None,
                signature_image_data=signature_image_data,
                signature_position="bottom_right",
            )
        return source_pdf_bytes

    out_buf = io.BytesIO()
    writer.write(out_buf)
    return out_buf.getvalue()


def flatten_form_fields(source_pdf_bytes: bytes) -> bytes:
    if not source_pdf_bytes:
        return source_pdf_bytes

    try:
        reader = PyPdfReader(io.BytesIO(source_pdf_bytes))
    except Exception:
        return source_pdf_bytes

    if not reader.pages:
        return source_pdf_bytes

    writer = PyPdfWriter()
    writer.clone_document_from_reader(reader)

    for page in writer.pages:
        try:
            annots = page.get("/Annots")
            if not annots:
                continue

            new_annots = []
            for annot_ref in annots:
                try:
                    if _sigfields._is_signature_field(annot_ref):
                        continue
                except Exception:
                    pass
                new_annots.append(annot_ref)

            if new_annots:
                page[NameObject("/Annots")] = ArrayObject(new_annots)
            else:
                if "/Annots" in page:
                    del page[NameObject("/Annots")]
        except Exception:
            continue

    out_buf = io.BytesIO()
    try:
        writer.write(out_buf)
    except Exception:
        return source_pdf_bytes

    return out_buf.getvalue()
