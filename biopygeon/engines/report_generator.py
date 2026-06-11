import os
import re
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def create_trends_chart(df_jurnal, folder_path):
    """Membuat grafik tren publikasi dan sitasi per tahun."""
    df = df_jurnal.copy()
    df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
    df = df[df['year'] > 0]
    
    df_trends = df.groupby('year').agg(
        jumlah_publikasi=('title', 'count'),
        total_sitasi=('citations', 'sum')
    ).reset_index()
    
    df_trends = df_trends.sort_values('year')
    
    if df_trends.empty:
        return None
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    years = df_trends['year'].astype(str).tolist()
    
    ax1.plot(years, df_trends['jumlah_publikasi'], marker='o', color='#2B6CB0', linewidth=2.5, markersize=6)
    ax1.set_title("Tren Publikasi per Tahun", fontsize=11, fontweight='bold', pad=10, color='#1A365D')
    ax1.set_xlabel("Tahun", fontsize=9)
    ax1.set_ylabel("Jumlah Paper", fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.tick_params(axis='x', rotation=30)
    
    ax2.bar(years, df_trends['total_sitasi'], color='#319795', width=0.45, edgecolor='#234E52')
    ax2.set_title("Akumulasi Sitasi", fontsize=11, fontweight='bold', pad=10, color='#1A365D')
    ax2.set_xlabel("Tahun", fontsize=9)
    ax2.set_ylabel("Total Sitasi", fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.tick_params(axis='x', rotation=30)
    
    plt.tight_layout()
    chart_path = os.path.join(folder_path, "trends.png")
    try:
        plt.savefig(chart_path, dpi=300)
        plt.close()
        return chart_path
    except Exception:
        plt.close()
        return None

def add_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#718096'))
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
    canvas.setLineWidth(0.5)
    canvas.line(0.75*inch, 0.5*inch + 10, 7.75*inch, 0.5*inch + 10)
    now_str = datetime.now().strftime("%d %B %Y, %H:%M")
    canvas.drawString(0.75*inch, 0.5*inch, f"Laporan Analisis Eksekutif Biopygeon | Dibuat pada: {now_str}")
    canvas.drawRightString(7.75*inch, 0.5*inch, f"Halaman {doc.page}")
    canvas.restoreState()

def save_pdf_report(query, df_jurnal, ai_interpretation, folder_path, pdf_export_limit=5, progress_callback=None):
    pdf_path = os.path.join(folder_path, "Laporan_Riset.pdf")
    chart_path = create_trends_chart(df_jurnal, folder_path)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.85*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#1A365D'), spaceAfter=6)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor('#4A5568'), spaceAfter=15)
    h1_style = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=colors.HexColor('#2B6CB0'), spaceBefore=14, spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, textColor=colors.HexColor('#2D3748'), spaceAfter=8)
    bold_label_style = ParagraphStyle('BoldLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#1A365D'))
    normal_val_style = ParagraphStyle('NormalVal', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=colors.HexColor('#2D3748'))
    table_header_style = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.white)
    table_body_style = ParagraphStyle('TB', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10.5, textColor=colors.HexColor('#2D3748'))
    
    elements = []
    elements.append(Paragraph("BIOPYGEON RESEARCH INTELLIGENCE", bold_label_style))
    elements.append(Spacer(1, 4))
    elements.append(Table([['']], colWidths=[7.0*inch], rowHeights=[1.5], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A365D'))])))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Laporan Analisis Riset & Tren Literatur", title_style))
    elements.append(Paragraph(f"<b>Kueri Riset:</b> \"{query}\"<br/><b>Dihasilkan Oleh:</b> Biopygeon (AI-Powered)", subtitle_style))
    
    elements.append(Paragraph("📊 Metrik Statistik Literatur Dianalisis", h1_style))
    total_papers = len(df_jurnal)
    total_citations = df_jurnal['citations'].sum()
    avg_citations = df_jurnal['citations'].mean() if total_papers > 0 else 0
    min_year = df_jurnal['year'].min() if total_papers > 0 else "N/A"
    max_year = df_jurnal['year'].max() if total_papers > 0 else "N/A"
    oa_pct = (df_jurnal['is_oa'] == 'Ya').sum() / total_papers * 100 if total_papers > 0 else 0
    
    stats_data = [
        [Paragraph("<b>Total Makalah:</b>", bold_label_style), Paragraph(f"{total_papers}", normal_val_style), Paragraph("<b>Sitasi:</b>", bold_label_style), Paragraph(f"{total_citations}", normal_val_style)],
        [Paragraph("<b>Rentang Tahun:</b>", bold_label_style), Paragraph(f"{min_year} s/d {max_year}", normal_val_style), Paragraph("<b>Rata-rata Sitasi:</b>", bold_label_style), Paragraph(f"{avg_citations:.1f}", normal_val_style)],
        [Paragraph("<b>Persentase OA:</b>", bold_label_style), Paragraph(f"{oa_pct:.1f}%", normal_val_style), Paragraph("<b>Sumber Data:</b>", bold_label_style), Paragraph("OpenAlex", normal_val_style)]
    ]
    
    stats_table = Table(stats_data, colWidths=[2.0*inch, 1.5*inch, 2.0*inch, 1.5*inch])
    stats_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')), ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#EDF2F7')), ('PADDING', (0,0), (-1,-1), 6)]))
    elements.append(stats_table)
    elements.append(Spacer(1, 10))
    
    if chart_path and os.path.exists(chart_path):
        elements.append(Paragraph("📈 Visualisasi Tren Penelitian & Sitasi", h1_style))
        elements.append(Image(chart_path, width=7.0*inch, height=2.94*inch))
        elements.append(Spacer(1, 10))
        
    elements.append(Paragraph("📋 Daftar Publikasi Teratas", h1_style))
    top_table_data = [[Paragraph("No", table_header_style), Paragraph("Thn", table_header_style), Paragraph("Sitasi", table_header_style), Paragraph("Judul Publikasi Ilmiah", table_header_style), Paragraph("Penulis & Penerbit Jurnal", table_header_style)]]
    
    for idx, row in df_jurnal.head(pdf_export_limit).iterrows():
        judul_wrap = Paragraph(f"<b>{row['title']}</b>", table_body_style)
        penulis_wrap = Paragraph(f"{row['authors']}<br/><font color='#718096'><i>{row['journal']}</i></font>", table_body_style)
        top_table_data.append([Paragraph(str(idx+1), table_body_style), Paragraph(str(row['year']), table_body_style), Paragraph(str(row['citations']), table_body_style), judul_wrap, penulis_wrap])
        
    jurnal_table = Table(top_table_data, colWidths=[0.35*inch, 0.55*inch, 0.6*inch, 3.5*inch, 2.0*inch])
    table_styles = [('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), ('PADDING', (0,0), (-1,-1), 6)]
    for i in range(1, len(top_table_data)):
        table_styles.append(('BACKGROUND', (0, i), (-1, i), colors.white if i % 2 != 0 else colors.HexColor('#F7FAFC')))
    jurnal_table.setStyle(TableStyle(table_styles))
    
    elements.append(jurnal_table)
    elements.append(Spacer(1, 10))
    
    if ai_interpretation:
        elements.append(Paragraph("🧠 Sintesis Naratif & Interpretasi Literatur (AI)", h1_style))
        paragraphs = ai_interpretation.split('\n')
        for p in paragraphs:
            text = p.strip()
            if text:
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                if text.startswith('- ') or text.startswith('* '):
                    elements.append(Paragraph(text[2:], ParagraphStyle('Bullet', parent=body_style, leftIndent=15, firstLineIndent=-10)))
                else:
                    elements.append(Paragraph(text, body_style))
                
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    
    if chart_path and os.path.exists(chart_path):
        try:
            time.sleep(0.5)
            os.remove(chart_path)
        except:
            pass
            
    return pdf_path

def save_generic_pdf_report(title, subtitle, ai_interpretation, folder_path, raw_data=None, full_sequence=""):
    pdf_path = os.path.join(folder_path, f"{title.replace(' ', '_')}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.85*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor('#1A365D'), spaceAfter=6)
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor('#4A5568'), spaceAfter=15)
    h1_style = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=17, textColor=colors.HexColor('#2B6CB0'), spaceBefore=14, spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, textColor=colors.HexColor('#2D3748'), spaceAfter=8)
    bold_label_style = ParagraphStyle('BoldLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#1A365D'))
    
    elements = []
    elements.append(Paragraph("BIOPYGEON ANALYSIS REPORT", bold_label_style))
    elements.append(Spacer(1, 4))
    elements.append(Table([['']], colWidths=[7.0*inch], rowHeights=[1.5], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A365D'))])))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(subtitle, subtitle_style))
    
    if full_sequence:
        seq_style = ParagraphStyle('Seq', parent=styles['Normal'], fontName='Courier', fontSize=8, leading=10, textColor=colors.HexColor('#4A5568'))
        elements.append(Paragraph("🧬 Target Sequence", h1_style))
        import textwrap
        # Pisahkan menjadi baris-baris 80 karakter agar tidak keluar batas
        wrapped_seq = "<br/>".join(textwrap.wrap(full_sequence, width=80))
        elements.append(Paragraph(wrapped_seq, seq_style))
        elements.append(Spacer(1, 10))
        
    if raw_data is not None:
        elements.append(Paragraph("📊 Extracted Analysis Data", h1_style))
        
        table_header_style = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.white)
        table_body_style = ParagraphStyle('TB', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=colors.HexColor('#2D3748'))
        
        if isinstance(raw_data, dict):
            # Format sebagai tabel Key-Value
            data_list = [[Paragraph("Parameter", table_header_style), Paragraph("Nilai", table_header_style)]]
            for k, v in raw_data.items():
                data_list.append([Paragraph(str(k), table_body_style), Paragraph(str(v), table_body_style)])
                
            t = Table(data_list, colWidths=[2.5*inch, 4.0*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            for i in range(1, len(data_list)):
                t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.white if i % 2 != 0 else colors.HexColor('#F7FAFC'))]))
            elements.append(t)
            
        elif hasattr(raw_data, 'columns'): # DataFrame
            # Format sebagai tabel grid (untuk BLAST dll)
            cols = list(raw_data.columns)
            data_list = [[Paragraph(str(c), table_header_style) for c in cols]]
            for _, row in raw_data.iterrows():
                row_data = []
                for val in row:
                    row_data.append(Paragraph(str(val), table_body_style))
                data_list.append(row_data)
                
            # Hitung lebar dinamis
            num_cols = len(cols)
            col_width = 7.0 * inch / num_cols if num_cols > 0 else 1*inch
            t = Table(data_list, colWidths=[col_width]*num_cols)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            for i in range(1, len(data_list)):
                t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.white if i % 2 != 0 else colors.HexColor('#F7FAFC'))]))
            elements.append(t)
            
        elements.append(Spacer(1, 10))

    if ai_interpretation:
        elements.append(Paragraph("🧠 Interpretasi Analisis (AI)", h1_style))
        paragraphs = ai_interpretation.split('\n')
        for p in paragraphs:
            text = p.strip()
            if text:
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                if text.startswith('- ') or text.startswith('* '):
                    elements.append(Paragraph(text[2:], ParagraphStyle('Bullet', parent=body_style, leftIndent=15, firstLineIndent=-10)))
                else:
                    elements.append(Paragraph(text, body_style))
                
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    return pdf_path

def save_html_dashboard(title, subtitle, ai_interpretation, folder_path, dataframe=None, progress_callback=None):
    html_path = os.path.join(folder_path, f"{title.replace(' ', '_').replace(':', '')}_Dashboard.html")
    
    if dataframe is not None:
        try:
            from biopygeon.engines.bibliometrics import render_bibliometric_dashboard
            render_bibliometric_dashboard(dataframe, output_path=html_path)
            return html_path
        except Exception:
            pass
            
    html_content = f"<html><head><title>{title}</title></head><body style='font-family:sans-serif; padding:2rem;'><h1>{title}</h1><h2>{subtitle}</h2><hr/><h3>AI Interpretation</h3><pre style='white-space:pre-wrap;'>{ai_interpretation}</pre></body></html>"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_path

def save_primer_pdf_report(primer_data, folder_path, sequence="", params_used=None):
    import time
    is_cloning_any = any(p.get('cloning_mode', False) for p in primer_data)
    prefix = "Desain_Primer_Kloning_" if is_cloning_any else "Desain_Primer_Standar_"
    pdf_path = os.path.join(folder_path, f"{prefix}{int(time.time())}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=0.75*inch, rightMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.85*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#1A365D'), spaceAfter=15)
    h1_style = ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#2B6CB0'), spaceBefore=14, spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#2D3748'), spaceAfter=8)
    
    table_header_style = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.white)
    table_body_style = ParagraphStyle('TB', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#2D3748'))
    
    elements = []
    
    # 1. Judul Laporan
    elements.append(Paragraph("1. Laporan Desain Primer & Parameter Termal", title_style))
    elements.append(Paragraph("Berikut adalah rancangan primer spesifik untuk amplifikasi PCR yang diminta. Parameter desain dan input sekuens tercantum di bawah ini.", body_style))
    elements.append(Spacer(1, 10))
    
    # 2. Input Sekuens
    if sequence:
        elements.append(Paragraph("2. Input Sekuens (Target DNA)", ParagraphStyle('H2', parent=h1_style, textColor=colors.HexColor('#2C5282'))))
        seq_wrapped = "<br/>".join([sequence[i:i+60] for i in range(0, len(sequence), 60)])
        seq_style = ParagraphStyle('Seq', parent=body_style, fontName='Courier', fontSize=8, leading=10, backColor=colors.HexColor('#F7FAFC'), borderColor=colors.HexColor('#E2E8F0'), borderWidth=1, padding=8)
        elements.append(Paragraph(f"<b>>Sequence_Target ({len(sequence)} bp)</b><br/>{seq_wrapped}", seq_style))
        elements.append(Spacer(1, 10))
        
    # 3. Parameter
    if params_used:
        elements.append(Paragraph("3. Parameter Eksekusi", ParagraphStyle('H2', parent=h1_style, textColor=colors.HexColor('#2C5282'))))
        param_text = ""
        for k, v in params_used.items():
            param_text += f"• <b>{k}</b>: {v}<br/>"
        elements.append(Paragraph(param_text, body_style))
        elements.append(Spacer(1, 10))
        
    # 4. Hasil Tabel Primer
    elements.append(Paragraph("4. Rancangan Primer Terbaik", ParagraphStyle('H2', parent=h1_style, textColor=colors.HexColor('#2C5282'))))
    elements.append(Spacer(1, 10))
    
    # Render table
    data_list = [[
        Paragraph("Primer", table_header_style), 
        Paragraph("Sekuens (5' -> 3')", table_header_style), 
        Paragraph("Panjang", table_header_style), 
        Paragraph("Tm Spesifik", table_header_style), 
        Paragraph("Fungsi Utama", table_header_style)
    ]]
    
    for p in primer_data:
        fwd = p['forward']
        rev = p['reverse']
        is_cloning = p.get('cloning_mode', False)
        
        fwd_seq = fwd['sequence']
        rev_seq = rev['sequence']
        
        if is_cloning:
            fwd_seq_formatted = fwd_seq.replace(fwd['overhang'], fwd['overhang'] + " ").replace(fwd['enzyme'], " " + fwd['enzyme']) if fwd.get('overhang') else fwd_seq
            rev_seq_formatted = rev_seq.replace(rev['overhang'], rev['overhang'] + " ").replace(rev['enzyme'], " " + rev['enzyme']) if rev.get('overhang') else rev_seq
            fwd_desc = f"Menyisipkan situs {fwd.get('enzyme')} dan memulai translasi in-frame dari RBS plasmid."
            rev_desc = f"Menghilangkan stop codon gen, menyisipkan situs {rev.get('enzyme')} secara in-frame langsung ke His-tag."
            tm_fwd = f"~{fwd['tm_bind']}°C"
            tm_rev = f"~{rev['tm_bind']}°C"
        else:
            fwd_seq_formatted = fwd_seq
            rev_seq_formatted = rev_seq
            fwd_desc = "Amplifikasi target PCR"
            rev_desc = "Amplifikasi target PCR"
            tm_fwd = f"~{fwd['tm']}°C"
            tm_rev = f"~{rev['tm']}°C"
            
        data_list.append([
            Paragraph("Forward", table_body_style),
            Paragraph(fwd_seq_formatted, table_body_style),
            Paragraph(f"{fwd['length']} bp", table_body_style),
            Paragraph(tm_fwd, table_body_style),
            Paragraph(fwd_desc, table_body_style)
        ])
        
        data_list.append([
            Paragraph("Reverse", table_body_style),
            Paragraph(rev_seq_formatted, table_body_style),
            Paragraph(f"{rev['length']} bp", table_body_style),
            Paragraph(tm_rev, table_body_style),
            Paragraph(rev_desc, table_body_style)
        ])
        
        # Only print the best pair
        break

    t = Table(data_list, colWidths=[1.0*inch, 2.5*inch, 0.8*inch, 0.8*inch, 1.9*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    for i in range(1, len(data_list)):
        t.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.white if i % 2 != 0 else colors.HexColor('#F7FAFC'))]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Touchdown Protocol
    elements.append(Paragraph("Rekomendasi Siklus Reaksi PCR (Thermal Cycling Protocol):", ParagraphStyle('H2', parent=h1_style, textColor=colors.HexColor('#319795'))))
    elements.append(Paragraph("Karena primer memiliki bagian overhang restriksi yang tidak menempel pada cetakan awal, disarankan menggunakan protokol <b>Touchdown PCR / Two-step PCR</b> untuk hasil amplifikasi murni maksimal:", body_style))
    
    protocol_text = """
    <b>1. Siklus Awal (Siklus 1 - 5):</b> Gunakan suhu annealing rendah sebesar <b>60°C - 62°C</b> karena hanya bagian spesifik-gen primer yang menempel pada DNA cetakan sintetik.<br/>
    <b>2. Siklus Lanjutan (Siklus 6 - 30):</b> Naikkan suhu annealing menjadi <b>68°C - 70°C</b> karena seluruh untai primer lengkap (termasuk situs potong restriksi) sudah menempel sempurna pada produk PCR cetakan hasil siklus awal.
    """
    
    prot_style = ParagraphStyle('Protocol', parent=body_style, backColor=colors.HexColor('#FFFFF0'), borderColor=colors.HexColor('#F6E05E'), borderWidth=1, padding=10)
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(protocol_text, prot_style))
    
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#718096'))
        canvas.drawString(0.75*inch, 0.5*inch, "Biopygeon AI - Modul Desain Primer")
        canvas.drawRightString(8.5*inch - 0.75*inch, 0.5*inch, f"Halaman {doc.page}")
        canvas.restoreState()
        
    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
    return pdf_path
