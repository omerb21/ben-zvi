"""
Test script to debug signature application
"""
import io
import base64
from pathlib import Path
from pypdf import PdfReader
from app.services.justification_forms import _collect_all_sig_rects, apply_signature_to_sig_fields

def test_signature_positions():
    export_dir = Path(r"app\exports\2_עומר_בן צבי")
    base_path = export_dir / "packet_2.pdf"
    edited_path = export_dir / "packet_2_edited.pdf"
    sig_path = export_dir / "client_signature.png"
    
    # Simulate the actual signing flow conditions
    print("=== Simulating signing flow conditions ===")
    print(f"base_path exists: {base_path.is_file()}")
    print(f"edited_path exists: {edited_path.is_file()}")
    print(f"base_path: {base_path}")
    print(f"edited_path: {edited_path}")
    print(f"Paths are different: {base_path != edited_path}")
    
    # Load signature as data URL
    with open(sig_path, "rb") as f:
        sig_bytes = f.read()
    TEST_SIG = "data:image/png;base64," + base64.b64encode(sig_bytes).decode()
    
    print("=== Loading PDFs ===")
    with open(base_path, "rb") as f:
        base_bytes = f.read()
    with open(edited_path, "rb") as f:
        edited_bytes = f.read()
    
    base_reader = PdfReader(io.BytesIO(base_bytes))
    edited_reader = PdfReader(io.BytesIO(edited_bytes))
    
    print(f"Base pages: {len(base_reader.pages)}")
    print(f"Edited pages: {len(edited_reader.pages)}")
    
    print("\n=== Collecting signature positions from BASE ===")
    base_rects = _collect_all_sig_rects(base_reader)
    total_base = sum(len(rects) for rects in base_rects.values())
    print(f"Found {total_base} signature positions across {len(base_rects)} pages")
    for page_idx in sorted(base_rects.keys())[:5]:
        print(f"  Page {page_idx}: {len(base_rects[page_idx])} signatures")
    if len(base_rects) > 5:
        print(f"  ... and {len(base_rects) - 5} more pages")
    
    print("\n=== Collecting signature positions from EDITED ===")
    edited_rects = _collect_all_sig_rects(edited_reader)
    total_edited = sum(len(rects) for rects in edited_rects.values())
    print(f"Found {total_edited} signature positions across {len(edited_rects)} pages")
    for page_idx in sorted(edited_rects.keys()):
        print(f"  Page {page_idx}: {len(edited_rects[page_idx])} signatures")
    
    print("\n=== Testing signature application ===")
    print("Applying signatures to edited PDF using base as reference...")
    
    result_bytes = apply_signature_to_sig_fields(
        edited_bytes,
        TEST_SIG,
        reference_pdf_bytes=base_bytes,
    )
    
    # Check if result is different from source
    if result_bytes == edited_bytes:
        print("WARNING: Output is identical to input - no signatures were applied!")
    else:
        print(f"SUCCESS: Output differs from input")
        print(f"  Input size: {len(edited_bytes)} bytes")
        print(f"  Output size: {len(result_bytes)} bytes")
        
        # Save result for inspection
        out_path = r"app\exports\2_עומר_בן צבי\test_signed.pdf"
        with open(out_path, "wb") as f:
            f.write(result_bytes)
        print(f"  Saved to: {out_path}")

if __name__ == "__main__":
    test_signature_positions()
