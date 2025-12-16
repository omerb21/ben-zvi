from __future__ import annotations


def build_pdf_headers(filename: str, *, inline: bool) -> dict[str, str]:
    disposition = "inline" if inline else "attachment"
    return {
        "Content-Disposition": f'{disposition}; filename="{filename}"',
    }


def build_inline_pdf_headers(filename: str) -> dict[str, str]:
    return build_pdf_headers(filename, inline=True)


def build_attachment_pdf_headers(filename: str) -> dict[str, str]:
    return build_pdf_headers(filename, inline=False)
