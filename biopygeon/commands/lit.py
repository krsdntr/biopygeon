import typer
import pandas as pd
import os
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

app = typer.Typer(no_args_is_help=True)
console = Console()

@app.command("search")
def lit_search(
    query: str = typer.Option(None, "--query", help="Kata kunci pencarian literatur"),
    limit: int = typer.Option(None, "--limit", help="Jumlah maksimal jurnal yang dikembalikan"),
    year: int = typer.Option(None, "--year", help="Filter rentang tahun publikasi"),
    oa: bool = typer.Option(None, "--oa", help="Hanya tampilkan jurnal Open Access"),
    sort: str = typer.Option(None, "--sort", help="1: Sitasi, 2: Terbaru"),
    export_csv: bool = typer.Option(None, "--export-csv", help="Simpan data mentah ke CSV"),
    export_pdf: bool = typer.Option(None, "--export-pdf", help="Buat laporan PDF cerdas (AI)")
):
    """
    Mencari literatur saintifik (Opsi Interaktif tersedia jika argumen kosong).
    """
    from biopygeon.config import get_user_email, set_user_email
    
    # 0. Pengecekan Email untuk Keamanan API
    user_email = get_user_email()
    if not user_email:
        console.print("[bold yellow][!] Keamanan API: Anda belum mengonfigurasi email.[/bold yellow]")
        console.print("Server seperti NCBI (PubMed) dan OpenAlex mewajibkan email pengembang untuk menghindari pemblokiran IP.")
        email_input = Prompt.ask("[bold cyan]Masukkan alamat email Anda[/bold cyan]")
        set_user_email(email_input)
        console.print("[bold green][OK][/bold green] Email berhasil disimpan ke konfigurasi lokal.\n")
        
    # 1. Mode Interaktif untuk Argumen yang Kosong
    if query is None:
        query = Prompt.ask("[bold cyan]Masukkan kata kunci pencarian literatur[/bold cyan]")
    if limit is None:
        limit_str = Prompt.ask("[bold cyan]Jumlah maksimal jurnal[/bold cyan]", default="5")
        limit = int(limit_str)
    if year is None:
        year_str = Prompt.ask("[bold cyan]Batasi tahun? (Kosongkan jika tidak)[/bold cyan]", default="")
        year = int(year_str) if year_str.strip() else None
    if oa is None:
        oa = Confirm.ask("[bold cyan]Hanya tampilkan Open Access?[/bold cyan]", default=False)
    if sort is None:
        sort = Prompt.ask("[bold cyan]Urutkan berdasarkan (1: Sitasi, 2: Terbaru + relevansi)[/bold cyan]", choices=["1", "2"], default="1")
        
    console.print(f"\n[bold blue][+][/bold blue] Mencari jurnal dengan query: '{query}'...")
    
    from biopygeon.engines.literature import search_literature_with_fallback
    from biopygeon.engines.assistant import generate_report
    from biopygeon.engines.report_generator import save_pdf_report
    
    try:
        with console.status(f"[bold blue]Memulai SearchThink Pipeline untuk '{query}'...[/bold blue]") as status:
            def update_status(msg):
                console.print(f"[dim]{msg}[/dim]")
                status.update(f"[bold blue]{msg}[/bold blue]")
                
            results = search_literature_with_fallback(query, max_results=limit, year_filter=year, oa_filter=oa, sort_by=sort, progress_callback=update_status)
        
        if not results:
            console.print("[!] Tidak ada literatur yang ditemukan.")
            raise typer.Exit()
            
        # Konversi ke DataFrame agar seragam
        df = pd.DataFrame(results)
            
        table = Table(title="Hasil Pencarian SearchThink Pipeline", show_header=True, header_style="bold magenta")
        table.add_column("Judul Jurnal", style="cyan")
        table.add_column("Sumber", style="blue")
        table.add_column("Penulis", style="green")
        table.add_column("Tahun")
        table.add_column("Sitasi", justify="right")
        table.add_column("Skor AI", justify="right", style="magenta")
        table.add_column("OA")
        
        for r in results:
            table.add_row(
                r['title'], 
                r.get('source', 'Unknown'),
                r['authors'], 
                str(r['year']), 
                str(r['citations']), 
                str(r.get('relevance_score', '-')),
                r['is_oa']
            )
            
        console.print(table)
        
        # 2. Interaktif Ekspor CSV & PDF
        if export_csv is None:
            export_csv = Confirm.ask("\n[bold cyan]Cetak dataset ke format CSV?[/bold cyan]", default=False)
            
        if export_csv:
            csv_path = os.path.join(os.getcwd(), "hasil_pencarian.csv")
            df.to_csv(csv_path, index=False)
            console.print(f"[bold green][OK][/bold green] CSV berhasil disimpan di: {csv_path}")
            
        if export_pdf is None:
            export_pdf = Confirm.ask("[bold cyan]Buat Laporan Eksekutif PDF dengan interpretasi AI?[/bold cyan]", default=False)
            
        if export_pdf:
            console.print("\n[bold yellow][*][/bold yellow] Menghasilkan sintesis AI menggunakan Groq...")
            ai_text = generate_report(df)
            
            console.print("[bold yellow][*][/bold yellow] Merender grafik tren dan dokumen PDF...")
            pdf_path = save_pdf_report(query, df, ai_text, os.getcwd())
            console.print(f"[bold green][OK][/bold green] Laporan PDF berhasil dibuat: {pdf_path}")
            console.print("[dim]Catatan: Data provenance (.provenance.json) juga telah di-generate untuk keperluan audit ilmiah.[/dim]")
            
        console.print("\n[OK] Selesai.")
        
    except Exception as e:
        console.print(f"\n[bold red][Error][/bold red] {str(e)}")
        raise typer.Exit(code=1)

@app.command("map")
def lit_map(
    query: str = typer.Option(None, "--query", help="Kata kunci pencarian bibliometrik"),
    limit: int = typer.Option(100, "--limit", help="Jumlah jurnal untuk ditarik (100-500 disarankan)"),
    year: int = typer.Option(None, "--year", help="Filter rentang tahun publikasi")
):
    """
    Membuat Peta Jaringan Bibliometrik (Dashboard HTML) dari data massal.
    """
    from biopygeon.config import get_user_email, set_user_email
    
    # 0. Pengecekan Email untuk Keamanan API
    user_email = get_user_email()
    if not user_email:
        console.print("[bold yellow][!] Keamanan API: Anda belum mengonfigurasi email.[/bold yellow]")
        console.print("Server seperti NCBI (PubMed) dan OpenAlex mewajibkan email pengembang untuk menghindari pemblokiran IP.")
        email_input = Prompt.ask("[bold cyan]Masukkan alamat email Anda[/bold cyan]")
        set_user_email(email_input)
        console.print("[bold green][OK][/bold green] Email berhasil disimpan ke konfigurasi lokal.\n")

    if query is None:
        query = Prompt.ask("[bold cyan]Masukkan kata kunci pemetaan bibliometrik[/bold cyan]")
        
    console.print(f"\n[bold blue][+][/bold blue] Menarik data massal untuk: '{query}'...")
    
    from biopygeon.engines.literature import search_literature_with_fallback
    from biopygeon.engines.bibliometrics import render_bibliometric_dashboard
    
    try:
        with console.status(f"[bold blue]Mengunduh metadata literatur (Target: {limit})...[/bold blue]") as status:
            def update_status(msg):
                console.print(f"[dim]{msg}[/dim]")
                status.update(f"[bold blue]{msg}[/bold blue]")
                
            # Tarik data massal tanpa mementingkan sorting yang berat, prioritaskan kuantitas
            results, search_metadata = search_literature_with_fallback(query, max_results=limit, year_filter=year, sort_by="1", progress_callback=update_status, skip_ranking=True, return_metadata=True)
        
        if not results:
            console.print("[!] Tidak ada literatur yang ditemukan.")
            raise typer.Exit()
            
        df = pd.DataFrame(results)
        console.print(f"[bold green][OK][/bold green] Berhasil mengunduh {len(df)} metadata literatur.")
        
        # 1. Simpan CSV Data Mentah
        csv_path = os.path.join(os.getcwd(), "bibliometrik_raw_data.csv")
        df.to_csv(csv_path, index=False)
        console.print(f"[bold green][OK][/bold green] Data mentah berhasil disimpan di: [cyan]{csv_path}[/cyan]")
        
        with console.status(f"[bold blue]Merender Bibliometric Dashboard...[/bold blue]") as status:
            def update_status2(msg):
                console.print(f"[dim]{msg}[/dim]")
                status.update(f"[bold blue]{msg}[/bold blue]")
                
            html_path = os.path.join(os.getcwd(), "Bibliometric_Dashboard.html")
            render_bibliometric_dashboard(
                df, 
                output_path=html_path, 
                progress_callback=update_status2,
                query=query,
                limit=limit,
                year=year,
                metadata=search_metadata
            )
            
        console.print(f"\n[bold green][OK][/bold green] Dashboard Bibliometrik Interaktif berhasil dibuat: [cyan]{html_path}[/cyan]")
        console.print("[dim]Silakan buka file HTML tersebut menggunakan web browser Anda (Chrome/Firefox/Edge).[/dim]")
        
    except Exception as e:
        console.print(f"\n[bold red][Error][/bold red] {str(e)}")
        raise typer.Exit(code=1)
