import os
import json
import re

try:
    import win32com.client
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from rich.console import Console
from biopygeon.engines.assistant import _call_groq_with_fallback

console = Console()

def format_manuscript_engine(draft_docx: str, template_docx: str, output_docx: str):
    """
    Format naskah menggunakan MS Word Native COM Automation (pywin32) 
    demi menjamin keamanan 100% pada field sitasi Mendeley/Zotero.
    """
    if not HAS_WIN32:
        console.print("[bold red][ERROR] Modul pywin32 tidak terpasang atau Anda tidak berada di Windows.[/bold red]")
        console.print("[dim]Fitur Native COM Automation mewajibkan OS Windows dan Microsoft Word terinstal.[/dim]")
        console.print("[dim]Jalankan: pip install pywin32[/dim]")
        return "Error: pywin32 tidak terpasang."
        
    draft_path = os.path.abspath(draft_docx)
    template_path = os.path.abspath(template_docx)
    output_path = os.path.abspath(output_docx)
    
    if not os.path.exists(draft_path):
        console.print(f"[bold red]Error: Draft file tidak ditemukan di {draft_path}[/bold red]")
        return f"Error: Draft file tidak ditemukan di {draft_path}"
    if not os.path.exists(template_path):
        console.print(f"[bold red]Error: Template file tidak ditemukan di {template_path}[/bold red]")
        return f"Error: Template file tidak ditemukan di {template_path}"

    console.print(f"[bold cyan]Membuka Microsoft Word (Background) via COM Automation...[/bold cyan]")
    
    word = None
    doc_draft = None
    doc_template = None
    
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False # Jalankan di background (tak terlihat)
        word.DisplayAlerts = False
        
        # 1. Buka Template Tujuan Dulu (Untuk Ekstrak Visual Clone & Hints)
        console.print("[dim]Memuat template jurnal target...[/dim]")
        doc_template = word.Documents.Open(template_path)
        
        template_styles = []
        style_hints = {}
        style_visual_overrides = {}
        
        for p in doc_template.Paragraphs:
            try:
                style_name = p.Style.NameLocal
                if p.Style.InUse and p.Style.Type == 1 and style_name not in template_styles:
                    template_styles.append(style_name)
                
                text = p.Range.Text.strip().replace('\r', '').replace('\n', '').replace('\x0b', '')
                if len(text) > 10:
                    if style_name not in style_hints:
                        style_hints[style_name] = text[:100]
                    
                    if style_name not in style_visual_overrides:
                        style_visual_overrides[style_name] = {
                            "FontName": p.Range.Font.Name,
                            "FontSize": p.Range.Font.Size
                        }
            except:
                pass
                
        if not template_styles:
            template_styles = ["Normal", "Heading 1", "Heading 2", "Title", "Abstract"]

        # 2. Buka Draft Asli & Ekstrak Signatures
        console.print("[dim]Memuat draft asli dan menganalisis clustering (Signatures)...[/dim]")
        doc_draft = word.Documents.Open(draft_path)
        draft_signatures = {}
        
        for p in doc_draft.Paragraphs:
            try:
                text = p.Range.Text.strip().replace('\r', '').replace('\n', '').replace('\x0b', '')
                if len(text) < 5:
                    continue
                
                style_name = p.Style.NameLocal
                text_lower = text.lower()
                
                # Compute signature
                sig = style_name
                if style_name == "Normal":
                    if re.match(r'^(table|tabel|tbl)\b', text_lower):
                        sig = "Normal_TableCaption"
                    elif re.match(r'^(figure|fig|gambar)\b', text_lower):
                        sig = "Normal_FigureCaption"
                    elif re.match(r'^(abstract|abstrak)\b', text_lower):
                        sig = "Normal_Abstract"
                    elif len(text) < 80 and not text.endswith('.'):
                        sig = "Normal_ShortHeading"
                    else:
                        sig = "Normal_Body"
                        
                if sig not in draft_signatures:
                    draft_signatures[sig] = []
                
                if len(draft_signatures[sig]) < 3: # Max 3 examples per signature
                    draft_signatures[sig].append(text[:100])
            except:
                pass
                
        # Copy keseluruhan isi file (ini menggaransi Mendeley field ikut ter-copy 100%)
        doc_draft.Content.Copy()
            
        # 3. Tempelkan Naskah ke Template
        bookmark_name = "KontenJurnal"
        if doc_template.Bookmarks.Exists(bookmark_name):
            console.print("[dim]Bookmark 'KontenJurnal' ditemukan. Menempelkan naskah di titik tersebut...[/dim]")
            rng = doc_template.Bookmarks(bookmark_name).Range
            rng.Paste()
        else:
            console.print("[dim]Bookmark tidak ditemukan. Menghapus teks dummy template lalu menempelkan naskah draft...[/dim]")
            # Hapus semua isi bawaan template agar tidak bercampur, lalu paste draft kita
            doc_template.Content.Delete()
            rng = doc_template.Content
            rng.Paste()
            
        # Tutup file draft
        doc_draft.Close(False)
        doc_draft = None
        
        # 4. Minta AI (Groq) melakukan pemetaan
        console.print("[bold yellow]Meminta AI memetakan Ultimate Hybrid Signatures...[/bold yellow]")
        
        hints_str = "\n".join([f"- '{k}': '{v}'" for k, v in style_hints.items()])
        system_prompt = (
            "Anda adalah AI Rule-Based Engine untuk pemformatan MS Word.\n"
            "Tugas Anda: memetakan 'Draft Signature' ke 'Template Style' yang paling tepat berdasarkan contoh teks yang diberikan.\n\n"
            f"DAFTAR TEMPLATE STYLE YANG TERSEDIA:\n{', '.join(template_styles[:150])}\n\n"
            f"CONTOH TEKS BAWAAN TEMPLATE (STYLE HINTS):\n{hints_str}\n\n"
            "ATURAN:\n"
            "1. DILARANG KERAS memetakan signature narasi teks biasa ke style bertuliskan 'Table' atau 'Figure'.\n"
            "2. Kembalikan JSON object dengan key 'mapping' yang berisi array of objects.\n"
            "3. Format object: {\"signature\": \"<nama_signature_draft>\", \"template_style\": \"<nama_style_template_yang_cocok>\"}\n"
            "4. Jika signature mengindikasikan Heading/Caption, cari style template yang sesuai.\n"
        )
        
        user_prompt = json.dumps({"draft_signatures_to_map": draft_signatures})
        
        ai_response = _call_groq_with_fallback(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=3500,
            response_format={"type": "json_object"}
        )
        
        content = ai_response.get("content", "{}")
        mapping_data = []
        try:
            parsed_json = json.loads(content)
            mapping_data = parsed_json.get("mapping", [])
        except Exception as json_err:
            console.print(f"[dim]Peringatan: Gagal parsing JSON dari AI: {json_err}[/dim]")
            
        # Bentuk dictionary pemetaan
        mapping_dict = {}
        for item in mapping_data:
            sig = item.get("signature", "")
            style_name = item.get("template_style", "Normal")
            if sig:
                mapping_dict[sig] = style_name
                
        # 5. Terapkan Style ke Paragraf di Template secara Masif
        console.print("[dim]Menerapkan eksekusi Visual Cloning secara masif...[/dim]")
        
        for p in doc_template.Paragraphs:
            try:
                text = p.Range.Text.strip().replace('\r', '').replace('\n', '').replace('\x0b', '')
                if len(text) < 5:
                    continue
                    
                style_name = p.Style.NameLocal
                text_lower = text.lower()
                
                # Hitung ulang signature untuk paragraf ini
                sig = style_name
                if style_name == "Normal":
                    if re.match(r'^(table|tabel|tbl)\b', text_lower):
                        sig = "Normal_TableCaption"
                    elif re.match(r'^(figure|fig|gambar)\b', text_lower):
                        sig = "Normal_FigureCaption"
                    elif re.match(r'^(abstract|abstrak)\b', text_lower):
                        sig = "Normal_Abstract"
                    elif len(text) < 80 and not text.endswith('.'):
                        sig = "Normal_ShortHeading"
                    else:
                        sig = "Normal_Body"
                        
                if sig in mapping_dict:
                    target_style = mapping_dict[sig]
                    
                    # Apply style!
                    p.Style = target_style
                    p.Reset()
                    p.Range.Font.ColorIndex = 0
                    
                    # Visual Cloning (Override Font dari pembuat template)
                    if target_style in style_visual_overrides:
                        overrides = style_visual_overrides[target_style]
                        # 9999999 adalah wdUndefined (mix font)
                        if overrides["FontName"] and overrides["FontName"] != 9999999:
                            p.Range.Font.Name = overrides["FontName"]
                        if overrides["FontSize"] and overrides["FontSize"] != 9999999:
                            p.Range.Font.Size = overrides["FontSize"]
                    else:
                        # Fallback ke font bawaan style jika tidak ada visual clone
                        ts = doc_template.Styles(target_style)
                        if ts.Font.Name: p.Range.Font.Name = ts.Font.Name
                        if ts.Font.Size: p.Range.Font.Size = ts.Font.Size
            except Exception:
                pass
                        
        # 6. Simpan hasil
        doc_template.SaveAs(output_path)
        console.print(f"[bold green][OK][/bold green] Manuskrip berhasil diformat dan disimpan ke: {output_path}")
        return f"Berhasil memformat dan menyimpan dokumen ke {output_path}"
        
    except Exception as e:
        console.print(f"[bold red]Terjadi kesalahan saat memproses Word secara COM Automation: {e}[/bold red]")
        return f"Gagal memformat dokumen: {e}"
    finally:
        # Pembersihan agar proses MS Word tidak nyangkut di RAM
        if doc_draft:
            try:
                doc_draft.Close(False)
            except:
                pass
        if doc_template:
            try:
                doc_template.Close(False)
            except:
                pass
        if word:
            try:
                word.Quit()
            except:
                pass
