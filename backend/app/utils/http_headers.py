from __future__ import annotations


def build_pdf_headers(filename: str, *, inline: bool) -> dict[str, str]:
    disposition = "inline" if inline else "attachment"
    # Ensure filename is ASCII-safe for HTTP headers
    safe_filename = filename.encode('ascii', errors='ignore').decode('ascii')
    if not safe_filename:
        safe_filename = "report.pdf"
    return {
        "Content-Disposition": f'{disposition}; filename="{safe_filename}"',
    }


def build_inline_pdf_headers(filename: str) -> dict[str, str]:
    return build_pdf_headers(filename, inline=True)


def build_attachment_pdf_headers(filename: str) -> dict[str, str]:
    return build_pdf_headers(filename, inline=False)
