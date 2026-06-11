import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()

@app.command("volcano")
def volcano(
    input_file: str = typer.Option(..., "--in", help="File CSV/TSV input RNA-seq"),
    pvalue: float = typer.Option(0.05, "--pvalue", help="Ambang batas p-value"),
    log2fc: float = typer.Option(2.0, "--log2fc", help="Ambang batas Log2 Fold Change"),
    pvalue_col: str = typer.Option("pvalue", help="Nama kolom p-value di dataset"),
    fc_col: str = typer.Option("log2fc", help="Nama kolom Log2 Fold Change di dataset"),
    out_file: str = typer.Option("./omics_filtered.csv", "--out", help="Lokasi simpan file terfilter")
):
    """
    Filter data transcriptomics untuk keperluan pembuatan Volcano Plot.
    """
    console.print(f"[bold blue][+][/bold blue] Membaca data dari {input_file}...")
    
    # Lazy loading
    from biopygeon.parsers.generic import load_data
    from biopygeon.engines.omics import calculate_volcano_stats
    
    try:
        df = load_data(input_file)
        console.print(f"Data termuat: {len(df)} baris.")
        
        console.print(f"[bold blue][+][/bold blue] Mengkalkulasi regulasi gen (p < {pvalue}, |log2FC| > {log2fc})...")
        df_res, total, up, down = calculate_volcano_stats(df, pvalue_col, fc_col, pvalue, log2fc)
        
        console.print(f"[bold green][OK][/bold green] Memfilter gen. Mengidentifikasi {up} Upregulated, {down} Downregulated.")
        
        df_res.to_csv(out_file, index=False)
        console.print(f"[bold green][OK][/bold green] Data hasil filter disimpan: {out_file}")
        
    except Exception as e:
        console.print(f"[bold red][Error][/bold red] {str(e)}")
        raise typer.Exit(code=1)
