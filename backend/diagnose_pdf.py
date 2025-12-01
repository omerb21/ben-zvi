"""
Script to diagnose PDF signature fields.
Run with: python diagnose_pdf.py <path_to_pdf>
"""
import sys
import io
from pypdf import PdfReader

def analyze_pdf(pdf_path: str):
    print(f"\n{'='*60}")
    print(f"Analyzing: {pdf_path}")
    print(f"{'='*60}\n")
    
    # Read file bytes and create reader
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))
    
    print(f"Total pages: {len(reader.pages)}\n")
    
    # Check AcroForm
    print("--- AcroForm Analysis ---")
    try:
        root = reader.trailer.get("/Root")
        if root:
            root_obj = root.get_object() if hasattr(root, "get_object") else root
            acroform = root_obj.get("/AcroForm")
            if acroform:
                acroform_obj = acroform.get_object() if hasattr(acroform, "get_object") else acroform
                fields = acroform_obj.get("/Fields")
                if fields:
                    print(f"AcroForm has {len(fields)} top-level fields\n")
                    
                    def process_field(field_ref, depth=0, inherited_ft=""):
                        try:
                            field = field_ref.get_object() if hasattr(field_ref, "get_object") else field_ref
                            
                            ft = field.get("/FT")
                            current_ft = str(ft) if ft else inherited_ft
                            
                            name = field.get("/T")
                            name_str = str(name) if name else "(no name)"
                            
                            rect = field.get("/Rect")
                            page_ref = field.get("/P")
                            
                            # Check if this looks like a signature field
                            is_sig = current_ft == "/Sig"
                            name_has_sig = "sig" in name_str.lower() if name else False
                            
                            prefix = "  " * depth
                            marker = ""
                            if is_sig:
                                marker = " [SIG by FT]"
                            elif name_has_sig:
                                marker = " [SIG by name]"
                            
                            print(f"{prefix}Field: {name_str}, FT={current_ft or '(inherited)'}{marker}")
                            if rect:
                                print(f"{prefix}  Rect: {[float(r) for r in rect]}")
                            
                            kids = field.get("/Kids")
                            if kids:
                                print(f"{prefix}  Kids: {len(kids)}")
                                for kid in kids:
                                    process_field(kid, depth + 1, current_ft)
                        except Exception as e:
                            print(f"{prefix}Error processing field: {e}")
                    
                    for field_ref in fields:
                        process_field(field_ref)
                else:
                    print("AcroForm has no Fields")
            else:
                print("No AcroForm found")
        else:
            print("No Root found")
    except Exception as e:
        print(f"Error analyzing AcroForm: {e}")
    
    # Check page annotations
    print("\n--- Page Annotations Analysis ---")
    for page_idx, page in enumerate(reader.pages):
        annots = page.get("/Annots")
        if annots:
            sig_count = 0
            for annot_ref in annots:
                try:
                    annot = annot_ref.get_object()
                    
                    # Check FT directly
                    ft = annot.get("/FT")
                    
                    # Check parent chain for FT
                    inherited_ft = ""
                    current = annot.get("/Parent")
                    visited = set()
                    while current is not None:
                        try:
                            obj = current.get_object() if hasattr(current, "get_object") else current
                            obj_id = id(obj)
                            if obj_id in visited:
                                break
                            visited.add(obj_id)
                            parent_ft = obj.get("/FT")
                            if parent_ft:
                                inherited_ft = str(parent_ft)
                                break
                            current = obj.get("/Parent")
                        except:
                            break
                    
                    # Check name
                    name = annot.get("/T")
                    name_str = str(name) if name else ""
                    
                    # Build full name
                    full_name_parts = []
                    current = annot
                    visited = set()
                    while current is not None:
                        try:
                            obj = current.get_object() if hasattr(current, "get_object") else current
                            obj_id = id(obj)
                            if obj_id in visited:
                                break
                            visited.add(obj_id)
                            n = obj.get("/T")
                            if n:
                                full_name_parts.append(str(n))
                            current = obj.get("/Parent")
                        except:
                            break
                    full_name_parts.reverse()
                    full_name = ".".join(full_name_parts)
                    
                    is_sig = (str(ft) == "/Sig" if ft else False) or (inherited_ft == "/Sig")
                    name_has_sig = "sig" in full_name.lower()
                    
                    if is_sig or name_has_sig:
                        sig_count += 1
                        rect = annot.get("/Rect")
                        print(f"  Page {page_idx}: FQN={full_name}, FT={ft or inherited_ft or '(none)'}, Rect={[float(r) for r in rect] if rect else 'none'}")
                
                except Exception as e:
                    pass
            
            if sig_count == 0:
                # Check if any annots have sig-like names even if not detected
                for annot_ref in annots:
                    try:
                        annot = annot_ref.get_object()
                        name = annot.get("/T")
                        if name and "sig" in str(name).lower():
                            print(f"  Page {page_idx}: Found annotation with 'sig' in name: {name}")
                    except:
                        pass

    print("\n--- Summary ---")
    print("If no signature fields are found above, the PDF might:")
    print("1. Use a different field naming convention")
    print("2. Have signature fields without /FT=/Sig attribute")
    print("3. Have flattened/rasterized signature areas instead of form fields")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_pdf.py <path_to_pdf>")
        sys.exit(1)
    
    analyze_pdf(sys.argv[1])
