import typer
from rich.console import Console
import os

app = typer.Typer(no_args_is_help=True)
console = Console()

@app.command("volcano")
def publish_volcano(
    input_file: str = typer.Option(..., "--in", help="File CSV/TSV hasil filter omics (mengandung kolom pvalue, log2fc, Regulation)"),
    journal: str = typer.Option("nature", "--journal", help="Template jurnal (nature, elsevier)"),
    out_file: str = typer.Option("./Volcano_Plot.tiff", "--out", help="Lokasi file gambar disimpan"),
    pvalue_col: str = typer.Option("pvalue", help="Nama kolom p-value"),
    fc_col: str = typer.Option("log2fc", help="Nama kolom Log2 Fold Change")
):
    """
    Render Volcano Plot berkualitas jurnal Q1.
    """
    console.print(f"[bold blue][+][/bold blue] Memuat template: {journal.title()}...")
    
    # Lazy imports
    import matplotlib.pyplot as plt
    import matplotlib.style as style
    import pandas as pd
    import numpy as np
    
    try:
        # Load style
        style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'styles', f'{journal.lower()}.mplstyle')
        if os.path.exists(style_path):
            style.use(style_path)
        else:
            console.print(f"[!] Warning: Style {journal} tidak ditemukan, menggunakan default.")
        
        # Load data
        df = pd.read_csv(input_file)
        if 'Regulation' not in df.columns:
            # Jika belum diproses, kita proses sederhana di tempat atau tolak
            raise ValueError("Kolom 'Regulation' tidak ditemukan. Jalankan 'biopygeon omics volcano' terlebih dahulu.")
            
        fig, ax = plt.subplots()
        
        # Plot non-significant
        ns = df[df['Regulation'] == 'Not Significant']
        ax.scatter(ns[fc_col], -np.log10(ns[pvalue_col]), color='grey', alpha=0.5, label='Not Sig')
        
        # Plot Upregulated
        up = df[df['Regulation'] == 'Upregulated']
        ax.scatter(up[fc_col], -np.log10(up[pvalue_col]), color='#D55E00', label='Up')
        
        # Plot Downregulated
        down = df[df['Regulation'] == 'Downregulated']
        ax.scatter(down[fc_col], -np.log10(down[pvalue_col]), color='#0072B2', label='Down')
        
        ax.set_xlabel('Log2 Fold Change')
        ax.set_ylabel('-Log10(p-value)')
        ax.legend()
        
        # Save figure
        plt.savefig(out_file, format='tiff', dpi=300)
        plt.close()
        
        console.print(f"[bold green][OK][/bold green] Figure berhasil dibuat: {out_file} (300 DPI)")
        
    except Exception as e:
        console.print(f"[bold red][Error][/bold red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("enrichment")
def publish_bubble_plot(
    input_file: str = typer.Option(..., "--in", help="File CSV hasil pengayaan dari Enrichr"),
    journal: str = typer.Option("nature", "--journal", help="Template jurnal (nature, elsevier)"),
    out_file: str = typer.Option("./Enrichment_Bubble.tiff", "--out", help="Lokasi simpan gambar"),
    term_col: str = typer.Option("Term", help="Kolom nama pathway"),
    pval_col: str = typer.Option("P-value", help="Kolom p-value"),
    count_col: str = typer.Option("Genes", help="Kolom list gen untuk dihitung jumlahnya")
):
    """Render Bubble Plot untuk hasil Gene Ontology Enrichment."""
    console.print(f"[bold blue][+][/bold blue] Memuat template: {journal.title()}...")
    import matplotlib.pyplot as plt
    import matplotlib.style as style
    import pandas as pd
    import numpy as np
    
    try:
        style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'styles', f'{journal.lower()}.mplstyle')
        if os.path.exists(style_path):
            style.use(style_path)
            
        df = pd.read_csv(input_file)
        
        if count_col in df.columns:
            df['GeneCount'] = df[count_col].apply(lambda x: len(str(x).split(';')))
        else:
            df['GeneCount'] = 10
            
        df['-log10(p-value)'] = -np.log10(df[pval_col])
        df = df.sort_values(by='-log10(p-value)', ascending=True).tail(15)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        scatter = ax.scatter(
            x=df['-log10(p-value)'], 
            y=df[term_col], 
            s=df['GeneCount'] * 20, 
            c=df['-log10(p-value)'], 
            cmap='viridis', 
            alpha=0.7, 
            edgecolors='k'
        )
        
        ax.set_xlabel('-Log10(P-value)')
        ax.set_title('Gene Enrichment Analysis')
        cbar = plt.colorbar(scatter)
        cbar.set_label('Significance')
        
        plt.tight_layout()
        plt.savefig(out_file, format='tiff', dpi=300)
        plt.close()
        
        console.print(f"[bold green][OK][/bold green] Bubble plot berhasil dibuat: {out_file}")
    except Exception as e:
        console.print(f"[bold red][Error][/bold red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("venn")
def publish_venn(
    file_a: str = typer.Option(..., "--a", help="File CSV grup A"),
    file_b: str = typer.Option(..., "--b", help="File CSV grup B"),
    col_name: str = typer.Option("gene_id", help="Nama kolom berisi ID/gen"),
    out_file: str = typer.Option("./Venn_Diagram.tiff", "--out", help="Lokasi simpan gambar"),
    journal: str = typer.Option("nature", "--journal", help="Template jurnal")
):
    """Render Venn Diagram antara 2 grup."""
    console.print(f"[bold blue][+][/bold blue] Membaca data untuk Venn Diagram...")
    from matplotlib_venn import venn2
    import matplotlib.pyplot as plt
    import pandas as pd
    import matplotlib.style as style
    
    try:
        style_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'styles', f'{journal.lower()}.mplstyle')
        if os.path.exists(style_path):
            style.use(style_path)
            
        df_a = pd.read_csv(file_a)
        df_b = pd.read_csv(file_b)
        
        set_a = set(df_a[col_name].dropna().astype(str))
        set_b = set(df_b[col_name].dropna().astype(str))
        
        fig, ax = plt.subplots(figsize=(6, 6))
        venn2([set_a, set_b], set_labels=('Group A', 'Group B'), set_colors=('#D55E00', '#0072B2'), alpha=0.7)
        
        plt.title('Gene Intersection')
        plt.savefig(out_file, format='tiff', dpi=300)
        plt.close()
        
        console.print(f"[bold green][OK][/bold green] Venn diagram berhasil dibuat: {out_file}")
    except Exception as e:
        console.print(f"[bold red][Error][/bold red] {str(e)}")
        raise typer.Exit(code=1)
