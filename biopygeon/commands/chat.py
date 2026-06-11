import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
import pandas as pd
import os
import json

if os.name == 'nt':
    os.system("chcp 65001 >nul 2>&1")

app = typer.Typer(help="Mode agen cerdas. Obrolan bahasa natural yang bisa memanggil alat CLI.")
console = Console(legacy_windows=False)

@app.callback(invoke_without_command=True)
def chat_loop():
    """
    Masuk ke mode obrolan agen cerdas.
    """
    from biopygeon.engines.assistant import agent_router
    from biopygeon.engines.literature import search_semanticscholar
    
    console.print("[bold cyan]=== 🕊️ Biopygeon Agentic Chat ===" )
    console.print("Halo! Saya asisten Biopygeon Anda. Ketik 'exit' atau 'quit' untuk keluar.")
    console.print("Anda dapat menanyakan hal umum atau menyuruh saya menganalisis data biologi.\n")
    
    from biopygeon.engines.cache_manager import get_cache_dir
    working_dir = working_dir
    if not os.access(working_dir, os.W_OK):
        working_dir = get_cache_dir()
        console.print(f"[bold yellow][!] Direktori saat ini read-only. File akan disimpan di: {working_dir}[/bold yellow]")
    
    chat_history = []
    last_df = None
    auto_reprompt = False
    error_message = ""
    retries = 0
    MAX_RETRIES = 2
    last_query = ""
    last_action_type = None
    last_primer_data = None
    last_primer_seq = ""
    last_primer_params = {}
    last_pdb_data = None
    last_fasta_data = None
    last_ai_interpretation = None
    last_blast_rid = None
    
    def save_run_metadata(action_type: str, params: dict, output_files: list):
        import datetime
        metadata = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action_type,
            "parameters": params,
            "output_files": output_files,
            "agent_version": "0.5.38"
        }
        filename = f"run_metadata_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(working_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)
        console.print(f"[dim]Metadata run tersimpan di: {filename}[/dim]")
        return filepath
        
    from biopygeon.config import get_user_email, set_user_email
    if not get_user_email():
        console.print("[bold yellow]Peringatan: Email pengguna belum diatur![/bold yellow]")
        console.print("[dim]Beberapa layanan API publik (NCBI, OpenAlex) mewajibkan email asli Anda untuk akses yang lebih cepat (Polite Pool).[/dim]")
        email_input = Prompt.ask("[bold cyan]Masukkan email Anda (tekan Enter untuk mengabaikan)[/bold cyan]")
        if email_input.strip():
            set_user_email(email_input.strip())
            console.print("[bold green]Email berhasil disimpan! Akses Polite Pool diaktifkan.[/bold green]")
            
    while True:
        try:
            if auto_reprompt and retries < MAX_RETRIES:
                user_input = error_message
                retries += 1
                console.print(f"[bold yellow]Mencoba memperbaiki secara otomatis oleh AI (Percobaan {retries}/{MAX_RETRIES})...[/bold yellow]")
            else:
                auto_reprompt = False
                retries = 0
                user_input = Prompt.ask("[bold green]Anda[/bold green]")
                if user_input.lower() in ['exit', 'quit', 'keluar']:
                    console.print("[bold yellow]Sampai jumpa![/bold yellow]")
                    break
                if not user_input.strip():
                    continue
            
            with console.status("[bold cyan]Agen sedang berpikir...[/bold cyan]", spinner="dots"):
                response = agent_router(user_input, history=chat_history)
                
            action = response.get('action', 'chat')
            params = response.get('params', {})
            reply = response.get('reply', '')
            
            # Tampilkan pesan dari agen
            if reply:
                console.print(f"[bold magenta]Bio-Agent:[/bold magenta] {reply}")
                
            # Simpan histori obrolan
            if action == "error":
                auto_reprompt = True
                error_message = f"[Sistem] " + params.get("error", "Unknown error")
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": f"[Aksi yang dipanggil gagal: {action}]"})
            else:
                chat_history.append({"role": "user", "content": user_input})
                if reply:
                    chat_history.append({"role": "assistant", "content": reply})
                
            if action == "chat":
                pass
            # Eksekusi Alat
            elif action == "lit_search":
                from biopygeon.engines.literature import search_literature_with_fallback
                query = params.get("query", "science")
                limit = params.get("limit", 5)
                year_filter = params.get("year_filter")
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"Mencari literatur untuk '{query}'...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 5  # default jump if not specified
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                        
                    results = search_literature_with_fallback(query, max_results=limit, year_filter=year_filter, progress_callback=update_status)
                    progress.update(task_id, completed=100)
                    
                if not results:
                    console.print("[!] Tidak ada literatur yang ditemukan.")
                df = pd.DataFrame(results)
                last_df = df
                last_query = query
                last_action_type = "lit_search"
                
                table = Table(title=f"Hasil Pencarian ({len(results)} Jurnal)", show_header=True, header_style="bold magenta")
                table.add_column("No", style="dim", width=4)
                table.add_column("Judul", style="cyan")
                table.add_column("Penulis", style="green")
                table.add_column("Tahun")
                table.add_column("Sitasi", justify="right")
                
                for idx, row in df.iterrows():
                    table.add_row(
                        str(idx + 1),
                        row.get("title", "No Title"),
                        row.get("authors", "Unknown"),
                        str(row.get("year", 0)),
                        str(row.get("citations", 0))
                    )
                console.print(table)
                
                from biopygeon.engines.assistant import generate_report
                from rich.markdown import Markdown
                with console.status("[bold cyan]AI sedang menyusun jawaban berdasarkan literatur...[/bold cyan]", spinner="dots"):
                    ai_response_text = generate_report(df, user_input)
                    
                console.print(Markdown(ai_response_text))
                last_ai_interpretation = ai_response_text
                chat_history.append({"role": "assistant", "content": ai_response_text})
                
            elif action == "lit_search_bibliometrics":
                from biopygeon.engines.literature import search_literature_with_fallback
                from biopygeon.engines.bibliometrics import render_bibliometric_dashboard
                query = params.get("query", "science")
                limit = params.get("limit", 100)
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"Mengekstrak bulk data '{query}' (Target: {limit})...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 5
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                        
                    results, query_meta = search_literature_with_fallback(query, max_results=limit, sort_by="1", progress_callback=update_status, skip_ranking=True, return_metadata=True)
                    progress.update(task_id, completed=100)
                    
                if not results:
                    console.print("[!] Tidak ada literatur yang ditemukan.")
                    chat_history.append({"role": "assistant", "content": "[Aksi: Tidak ada literatur ditemukan untuk pemetaan]"})
                    continue
                    
                df = pd.DataFrame(results)
                last_df = df
                last_query = query
                last_action_type = "lit_search"
                console.print(f"[bold green][OK][/bold green] Berhasil mengekstrak {len(df)} literatur.")
                
                with console.status("[bold cyan]Merender Dashboard Bibliometrik...[/bold cyan]", spinner="dots"):
                    html_path = os.path.join(working_dir, "Bibliometric_Dashboard.html")
                    render_bibliometric_dashboard(df, output_path=html_path, query=query, limit=limit, metadata=query_meta)
                    save_run_metadata(action, params, [html_path])
                    
                console.print(f"[bold green][OK][/bold green] Pemetaan selesai! Buka file ini di browser: [cyan]{html_path}[/cyan]")
                chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengekstrak {len(df)} literatur dan merender Peta Bibliometrik ke {html_path}]"})
                    
            elif action == "find_protein":
                from biopygeon.engines.biology import search_protein_structure
                protein_name = params.get("protein_name", "")
                limit = params.get("limit", 5)
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"Mencari struktur untuk '{protein_name}'...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 10
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                    results = search_protein_structure(protein_name, max_results=limit, progress_callback=update_status)
                    progress.update(task_id, completed=100)
                    
                if not results:
                    console.print(f"[!] Struktur untuk '{protein_name}' tidak ditemukan.")
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Tidak dapat menemukan struktur {protein_name}]"})
                    continue
                    
                table = Table(title=f"Hasil Pencarian Struktur ({len(results)} PDB)", show_header=True, header_style="bold magenta")
                table.add_column("No", style="dim", width=4)
                table.add_column("PDB ID", style="cyan")
                table.add_column("Judul", style="green")
                table.add_column("Metode")
                table.add_column("Resolusi", justify="right")
                
                for idx, row in enumerate(results):
                    table.add_row(
                        str(idx + 1),
                        row.get("pdb_id", "N/A"),
                        row.get("title", "No Title"),
                        row.get("method", "Unknown"),
                        str(row.get("resolution", "N/A"))
                    )
                console.print(table)
                last_pdb_data = results
                last_action_type = "find_protein"
                chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil menampilkan {len(results)} struktur protein {protein_name}]"})
                    
            elif action == "fetch_sequence":
                from biopygeon.engines.biology import fetch_fasta_sequence
                accession = params.get("accession", "")
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"Mengambil FASTA untuk '{accession}'...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 20
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                        
                    fasta_data = fetch_fasta_sequence(accession, progress_callback=update_status)
                    progress.update(task_id, completed=100)
                    
                if not fasta_data:
                    console.print(f"[!] FASTA untuk '{accession}' tidak ditemukan.")
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Tidak dapat menemukan FASTA untuk {accession}]"})
                    continue
                    
                from rich.panel import Panel
                # Tampilkan 15 baris pertama agar layar tidak penuh
                lines = fasta_data.split('\n')
                display_str = '\n'.join(lines[:15]) + ("\n..." if len(lines) > 15 else "")
                console.print(Panel(display_str, title=f"FASTA: {accession}", border_style="green"))
                
                last_fasta_data = fasta_data
                last_action_type = "fetch_sequence"
                chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengambil sekuens FASTA untuk {accession}]\n{fasta_data[:200]}..."})
                    
            elif action == "download_protein_data":
                from biopygeon.engines.biology import download_protein_files
                from biopygeon.engines.cache_manager import get_cache_dir
                
                pdb_id = params.get("pdb_id", "")
                file_type = params.get("file_type", "both")
                
                target_dir = working_dir
                if not os.access(target_dir, os.W_OK):
                    target_dir = get_cache_dir()
                    console.print(f"[bold yellow][!] Peringatan: Direktori saat ini read-only. File akan disimpan di cache: {target_dir}[/bold yellow]")
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"Mengunduh file {file_type.upper()} untuk '{pdb_id}'...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 20
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                        
                    downloaded = download_protein_files(pdb_id, file_type, target_dir, progress_callback=update_status)
                    progress.update(task_id, completed=100)
                    
                if downloaded:
                    for f in downloaded:
                        console.print(f"[bold green][OK][/bold green] File berhasil diunduh: [cyan]{f}[/cyan]")
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengunduh {len(downloaded)} file untuk {pdb_id}]"})
                else:
                    console.print(f"[!] Gagal mengunduh file untuk '{pdb_id}'.")
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Gagal mengunduh file untuk {pdb_id}]"})
                    
            elif action == "export_results":
                fmt = params.get("format", "pdf").lower()
                
                if last_action_type == "run_blast" and last_blast_rid:
                    import requests
                    
                    fmt_map = {
                        "xml": "XML",
                        "json": "JSON2_S",
                        "csv": "Tabular",
                        "tsv": "Tabular",
                        "text": "Text",
                        "asn1": "ASN.1",
                        "fasta": "Text"
                    }
                    if fmt == "pdf":
                        # Continue to normal PDF export logic for BLAST
                        pass
                    else:
                        f_type = fmt_map.get(fmt, fmt.upper())
                        console.print(f"[bold cyan]Mengunduh format {f_type} dari NCBI...[/bold cyan]")
                        try:
                            # For CSV/TSV, NCBI returns Tabular TSV.
                            r = requests.get("https://blast.ncbi.nlm.nih.gov/Blast.cgi", params={"CMD": "Get", "FORMAT_TYPE": f_type, "RID": last_blast_rid})
                            
                            content = r.text
                            if fmt == "csv" and f_type == "Tabular":
                                # Convert Tabular TSV to CSV
                                lines = content.split('\n')
                                content = '\n'.join([','.join(line.split('\t')) for line in lines])
                                
                            ext = fmt
                            if fmt == "asn1": ext = "asn"
                            filename = os.path.join(working_dir, f"blast_{last_blast_rid}.{ext}")
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(content)
                                
                            console.print(f"[bold green][OK][/bold green] File {fmt.upper()} berhasil diunduh: [cyan]{filename}[/cyan]")
                            save_run_metadata(action, params, [filename])
                            chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengunduh format {fmt.upper()} untuk BLAST RID {last_blast_rid}]"})
                        except Exception as e:
                            console.print(f"[!] Gagal mengunduh {fmt}: {e}")
                            chat_history.append({"role": "assistant", "content": f"[Aksi: Gagal mengunduh format {fmt}]"})
                        continue
                
                if last_action_type == "primer" and last_primer_data:
                    from biopygeon.engines.report_generator import save_primer_pdf_report
                    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                    with Progress(
                        SpinnerColumn(spinner_name="dots", style="bold yellow"),
                        TextColumn("[bold yellow]{task.description}"),
                        BarColumn(complete_style="yellow", finished_style="bold green"),
                        TaskProgressColumn(),
                        console=console
                    ) as progress:
                        task_id = progress.add_task("Merender laporan Primer PCR...", total=100)
                        def update_status(msg, advance=0):
                            if advance == 0: advance = 5
                            progress.update(task_id, description=f"[bold yellow]{msg}[/bold yellow]", advance=advance)
                            
                        pdf_path = save_primer_pdf_report(last_primer_data, working_dir, sequence=last_primer_seq, params_used=last_primer_params, progress_callback=update_status)
                        progress.update(task_id, completed=100)
                    console.print(f"[bold green][OK][/bold green] Laporan PDF Primer berhasil dibuat: {pdf_path}")
                    save_run_metadata(action, params, [pdf_path])
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengekspor Laporan PDF Primer]"})
                    continue
                    
                if last_action_type == "find_protein" and last_pdb_data:
                    import time
                    if fmt == "csv":
                        df = pd.DataFrame(last_pdb_data)
                        filename = os.path.join(working_dir, f"pdb_results_{int(time.time())}.csv")
                        df.to_csv(filename, index=False)
                        console.print(f"[bold green][OK][/bold green] Data PDB berhasil diekspor ke: [cyan]{filename}[/cyan]")
                        save_run_metadata(action, params, [filename])
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Ekspor hasil PDB ke {filename}]"})
                    else:
                        console.print(f"[!] Format '{fmt}' belum didukung untuk ekspor hasil PDB. Coba ketik 'ekspor csv'.")
                    continue
                
                if last_action_type == "fetch_sequence" and last_fasta_data:
                    import time
                    if fmt not in ["fasta", "txt", "fa"]:
                        fmt = "fasta"
                        console.print("[dim]Format dialihkan otomatis ke .fasta karena data merupakan sekuens protein/DNA.[/dim]")
                    
                    filename = os.path.join(working_dir, f"sequence_{int(time.time())}.{fmt}")
                    with open(filename, "w", encoding='utf-8') as f:
                        f.write(last_fasta_data)
                    console.print(f"[bold green][OK][/bold green] Sekuens FASTA berhasil disimpan ke: [cyan]{filename}[/cyan]")
                    save_run_metadata(action, params, [filename])
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Ekspor FASTA berhasil ke {filename}]"})
                    continue
                    
                if last_action_type != "lit_search" or last_df is None or last_df.empty:
                    console.print("[!] Anda harus melakukan pencarian terlebih dahulu (literatur, primer, PDB, atau sekuens) sebelum mengekspor.")
                    chat_history.append({"role": "assistant", "content": "[Aksi: Gagal mengekspor karena belum ada data yang sesuai]"})
                    continue
                    
                if fmt == "csv":
                    csv_path = os.path.join(working_dir, "hasil_pencarian.csv")
                    last_df.to_csv(csv_path, index=False)
                    console.print(f"[bold green][OK][/bold green] Data berhasil diekspor ke: {csv_path}")
                    save_run_metadata(action, params, [csv_path])
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengekspor data ke CSV]"})
                    continue
                elif fmt == "html":
                    from biopygeon.engines.assistant import generate_report
                    from biopygeon.engines.report_generator import save_html_dashboard
                    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                    
                    with Progress(
                        SpinnerColumn(spinner_name="dots", style="bold yellow"),
                        TextColumn("[bold yellow]{task.description}"),
                        BarColumn(complete_style="yellow", finished_style="bold green"),
                        TaskProgressColumn(),
                        console=console
                    ) as progress:
                        task_id = progress.add_task("Membangun Dasbor HTML Premium...", total=100)
                        def update_status(msg, advance=0):
                            if advance == 0: advance = 5
                            progress.update(task_id, description=f"[bold yellow]{msg}[/bold yellow]", advance=advance)
                            
                        ai_interpretation = last_ai_interpretation if last_ai_interpretation else "Sintesis AI tidak tersedia."
                        html_path = save_html_dashboard(f"Literature Review: {last_query}", "Biopygeon Autonomous Literature Mining", ai_interpretation, working_dir, dataframe=last_df, progress_callback=update_status)
                        progress.update(task_id, completed=100)
                    
                    console.print(f"[bold green][OK][/bold green] Dasbor HTML Premium berhasil dibuat: {html_path}")
                    save_run_metadata(action, params, [html_path])
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengekspor Dasbor HTML Premium]"})
                else: # pdf
                    from biopygeon.engines.report_generator import save_pdf_report
                    from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                    
                    with Progress(
                        SpinnerColumn(spinner_name="dots", style="bold yellow"),
                        TextColumn("[bold yellow]{task.description}"),
                        BarColumn(complete_style="yellow", finished_style="bold green"),
                        TaskProgressColumn(),
                        console=console
                    ) as progress:
                        task_id = progress.add_task("Merender Laporan PDF Eksekutif...", total=100)
                        def update_status(msg, advance=0):
                            if advance == 0: advance = 5
                            progress.update(task_id, description=f"[bold yellow]{msg}[/bold yellow]", advance=advance)
                            
                        # Gunakan sintesis AI yang sudah dibuat di lit_search, jika tidak ada, buat baru fallback
                        ai_interpretation = last_ai_interpretation if last_ai_interpretation else "Sintesis AI tidak tersedia."
                            
                        pdf_path = save_pdf_report(last_query, last_df, ai_interpretation, working_dir, progress_callback=update_status)
                        progress.update(task_id, completed=100)
                    console.print(f"[bold green][OK][/bold green] Laporan Riset PDF berhasil dibuat: {pdf_path}")
                    chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengekspor Laporan PDF cerdas]"})
                    
            elif action == "extract_domain":
                from biopygeon.engines.biology import extract_domain
                seq = params.get("sequence", "")
                motif = params.get("motif", "WFQNHR")
                before_aa = params.get("before_aa", 30)
                after_aa = params.get("after_aa", 25)
                
                with console.status("[bold cyan]Mengekstrak domain spesifik...[/bold cyan]", spinner="dots"):
                    try:
                        res = extract_domain(seq, motif, before_aa, after_aa)
                        console.print(f"[bold green][OK][/bold green] Domain berhasil diekstrak!")
                        console.print(f"Panjang Protein Utuh: {res['full_protein_length']} aa")
                        console.print(f"Koordinat Domain: asam amino {res['domain_start_aa']} s.d {res['domain_end_aa']}")
                        console.print(f"Panjang Domain: {res['domain_nt_length']} bp")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mengekstrak domain nukleotida sepanjang {res['domain_nt_length']} bp]\n\nHasil: {res}"})
                    except Exception as e:
                        console.print(f"[!] Gagal mengekstrak domain: {e}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Gagal mengekstrak domain: {e}]"})
                        
            elif action == "calculate_protein_params":
                from biopygeon.engines.biology import calculate_protein_params
                seq = params.get("sequence", "")
                tag = params.get("fusion_tag", "LEHHHHHH")
                
                with console.status("[bold cyan]Menghitung parameter protein rekombinan...[/bold cyan]", spinner="dots"):
                    try:
                        res = calculate_protein_params(seq, tag)
                        from rich.panel import Panel
                        
                        panel_txt = (
                            f"Panjang Asam Amino: {res['length_aa']} aa\n"
                            f"Berat Molekul: {res['molecular_weight_kDa']} kDa\n"
                            f"Titik Isoelektrik (pI): {res['isoelectric_point']}\n"
                            f"Muatan di pH 7: {res['charge_at_ph7']}"
                        )
                        console.print(Panel(panel_txt, title="Fisikokimia Protein Kloning", border_style="cyan"))
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil menghitung parameter protein kloning]\n\nHasil: {res}"})
                    except Exception as e:
                        console.print(f"[!] Gagal menghitung parameter protein: {e}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Gagal menghitung parameter protein kloning: {e}]"})

            elif action == "analyze_protparam":
                from biopygeon.engines.biology import calculate_protparam
                from biopygeon.engines.assistant import ask_groq
                from biopygeon.engines.report_generator import save_generic_pdf_report
                from rich.prompt import Confirm
                from rich.panel import Panel
                
                seq = params.get("sequence", "")
                
                success = False
                res_str, data_dict = "", {}
                with console.status("[bold cyan]Menganalisis sekuens (ProtParam)...[/bold cyan]", spinner="dots"):
                    try:
                        res_str, data_dict = calculate_protparam(seq)
                        success = True
                    except Exception as e:
                        console.print(f"[!] Gagal analisis ProtParam: {e}")
                        
                if success:
                    console.print(Panel(res_str, title="Hasil ProtParam", border_style="green"))
                    
                    if Confirm.ask("Simpan hasil dan Interpretasi AI ke dalam TXT?"):
                        with console.status("[bold cyan]Meminta interpretasi ProtParam (AI)...[/bold cyan]", spinner="dots"):
                            ai_text = ask_groq("Interpretasikan hasil ProtParam berikut:\n" + res_str)
                            
                        txt_path = os.path.join(working_dir, "protparam_result.txt")
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write("=== HASIL PROTPARAM ===\n")
                            f.write(res_str)
                            f.write("\n\n=== INTERPRETASI AI ===\n")
                            f.write(ai_text)
                            
                        console.print("[bold green][OK][/bold green] Data TXT dan Interpretasi berhasil disimpan ke: " + os.path.abspath(txt_path))
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil menghitung ProtParam dan mengekspor ke TXT]"})
                    else:
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil menghitung ProtParam]"})
                    
            elif action == "run_blast":
                from biopygeon.engines.biology import run_ncbi_blast
                from biopygeon.engines.assistant import ask_groq
                from biopygeon.engines.report_generator import save_generic_pdf_report
                seq = params.get("sequence", "")
                prog = params.get("program", "blastp")
                
                default_db = "nr_cluster_seq" if prog == "blastp" else "nt"
                db = params.get("database", default_db)
                if not db:
                    db = default_db
                limit = params.get("limit", 5)
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"Menjalankan {prog} melawan '{db}' di NCBI...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 5
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                    try:
                        results, blast_rid = run_ncbi_blast(seq, program=prog, database=db, max_results=limit, progress_callback=update_status)
                        progress.update(task_id, completed=100)
                        last_blast_rid = blast_rid
                        last_action_type = "run_blast"
                    except Exception as e:
                        console.print(f"[!] Gagal BLAST: {e}")
                        results = None

                if results is not None:
                    if not results:
                        console.print("[!] Tidak ada homologi ditemukan.")
                    else:
                        table = Table(title=f"Hasil BLAST ({len(results)} hits)", show_header=True)
                        table.add_column("Description", style="cyan")
                        table.add_column("Max Score")
                        table.add_column("Total Score")
                        table.add_column("Query Cover")
                        table.add_column("E value", style="magenta")
                        table.add_column("Per. Ident", style="green")
                        table.add_column("Acc. Len")
                        table.add_column("Accession", style="blue")
                        for r in results:
                            e_val = r['e_value']
                            e_str = "0.0" if e_val == 0 else f"{e_val:.2e}"
                            table.add_row(
                                r['description'], str(r['max_score']), str(r['total_score']), 
                                r['query_cover'], e_str, r['per_ident'], 
                                str(r['acc_len']), r['accession']
                            )
                        console.print(table)
                        
                        from rich.prompt import Confirm
                        if Confirm.ask("Simpan hasil ke CSV dan buat PDF Interpretasi AI?"):
                            csv_path = os.path.join(working_dir, "blast_results.csv")
                            df_blast = pd.DataFrame(results)
                            df_blast.to_csv(csv_path, index=False)
                            
                            with console.status("[bold cyan]Menulis interpretasi BLAST (AI)...[/bold cyan]", spinner="dots"):
                                data_str = df_blast.to_string()
                                ai_text = ask_groq("Interpretasikan hasil BLAST (homologi) ini secara singkat:\n" + data_str)
                                pdf_path = save_generic_pdf_report("BLAST Homology Report", f"Program: {prog} | Database: {db}", ai_text, working_dir, raw_data=df_blast, full_sequence=seq)
                            
                            console.print(f"[bold green][OK][/bold green] Data CSV: {csv_path}")
                            console.print(f"[bold green][OK][/bold green] PDF Interpretasi: {pdf_path}")
                            chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil menjalankan BLAST dengan {len(results)} hit dan mengekspor CSV/PDF]"})
                        else:
                            chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil menjalankan BLAST dengan {len(results)} hit]"})
                        
            elif action == "prepare_docking":
                from biopygeon.engines.biology import prepare_structure_for_vina
                in_path = params.get("input_path", "")
                out_path = params.get("output_path", "cleaned_docking.pdbqt")
                p_type = params.get("prep_type", "target")
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task(f"Mempersiapkan struktur {p_type} untuk docking...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 10
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                    try:
                        res_path = prepare_structure_for_vina(in_path, out_path, prep_type=p_type.lower(), progress_callback=update_status)
                        progress.update(task_id, completed=100)
                        console.print(f"[bold green][OK][/bold green] File docking siap di: {res_path}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil memproses struktur {p_type} ke {res_path}]"})
                    except Exception as e:
                        console.print(f"[!] Gagal memproses struktur docking: {e}")
                    
            elif action == "run_msa":
                from biopygeon.engines.biology import run_ebi_clustalo
                in_path = params.get("input_fasta", "")
                out_path = params.get("output_fasta", "alignment.fasta")
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task("Mempersiapkan MSA di EBI...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 5
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                    try:
                        res_path = run_ebi_clustalo(in_path, out_path, progress_callback=update_status)
                        progress.update(task_id, completed=100)
                        console.print(f"[bold green][OK][/bold green] Hasil MSA berhasil disimpan ke: {res_path}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil melakukan MSA dan menyimpan ke {res_path}]"})
                    except Exception as e:
                        console.print(f"[!] Gagal mengeksekusi MSA: {e}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Gagal mengeksekusi MSA]"})
                        
            elif action == "plot_phylo":
                from biopygeon.engines.biology import render_phylogenetic_tree
                aln_file = params.get("alignment_file", "")
                out_file = params.get("output_tiff", "phylo_tree.tiff")
                
                from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, SpinnerColumn
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold green"),
                    TextColumn("[bold cyan]{task.description}"),
                    BarColumn(complete_style="cyan", finished_style="bold green"),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    task_id = progress.add_task("Membangun visualisasi Pohon Filogenetik...", total=100)
                    def update_status(msg, advance=0):
                        if advance == 0: advance = 20
                        progress.update(task_id, description=f"[bold cyan]{msg}[/bold cyan]", advance=advance)
                    try:
                        res_path = render_phylogenetic_tree(aln_file, out_file, progress_callback=update_status)
                        progress.update(task_id, completed=100)
                        console.print(f"[bold green][OK][/bold green] Gambar Pohon Filogenetik siap di: {res_path}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil membangun Pohon Filogenetik ke {res_path}]"})
                    except Exception as e:
                        console.print(f"[!] Gagal membangun pohon filogenetik: {e}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Gagal membangun pohon filogenetik: {e}]"})
                        
            elif action == "design_primer":
                from biopygeon.engines.biology import design_pcr_primers
                seq = params.get("sequence", "")
                
                prod_min = params.get("prod_size_min", 150)
                prod_max = params.get("prod_size_max", 500)
                tm_opt = params.get("tm_opt", 60.0)
                tm_min = params.get("tm_min", 57.0)
                tm_max = params.get("tm_max", 63.0)
                
                fwd_enzyme = params.get("fwd_enzyme", "")
                fwd_enzyme_seq = params.get("fwd_enzyme_seq", "")
                rev_enzyme = params.get("rev_enzyme", "")
                rev_enzyme_seq = params.get("rev_enzyme_seq", "")
                fwd_overhang = params.get("fwd_overhang", "")
                rev_overhang = params.get("rev_overhang", "")
                drop_stop_codon = params.get("drop_stop_codon", False)
                
                cloning_mode_active = bool(fwd_enzyme_seq or rev_enzyme_seq or fwd_overhang or rev_overhang)
                status_msg = "[bold cyan]Mendesain primer PCR (Kloning Mode)...[/bold cyan]" if cloning_mode_active else "[bold cyan]Mendesain primer PCR standar...[/bold cyan]"
                
                with console.status(status_msg, spinner="dots"):
                    try:
                        res = design_pcr_primers(
                            seq, 
                            prod_size_min=prod_min, 
                            prod_size_max=prod_max,
                            tm_opt=tm_opt,
                            tm_min=tm_min,
                            tm_max=tm_max,
                            fwd_enzyme=fwd_enzyme,
                            fwd_enzyme_seq=fwd_enzyme_seq,
                            rev_enzyme=rev_enzyme,
                            rev_enzyme_seq=rev_enzyme_seq,
                            fwd_overhang=fwd_overhang,
                            rev_overhang=rev_overhang,
                            drop_stop_codon=drop_stop_codon
                        )
                        if not res:
                            console.print("[!] Gagal menemukan pasangan primer yang memenuhi syarat.")
                            chat_history.append({"role": "assistant", "content": "[Aksi: Gagal menemukan primer PCR]"})
                        else:
                            last_primer_data = res
                            last_primer_seq = seq
                            last_primer_params = params
                            last_action_type = "primer"
                            console.print(f"Ditemukan {len(res)} pasangan primer potensial:")
                            for p in res:
                                console.print(f"[bold green]Primer #{p['rank']}[/bold green] (Produk: {p['product_size']} bp)")
                                if p.get('cloning_mode'):
                                    console.print(f"  Fwd: [cyan]{p['forward']['sequence']}[/cyan] (Tm-bind: {p['forward']['tm_bind']}°C, GC: {p['forward']['gc']}%, Panjang: {p['forward']['length']} bp)")
                                    console.print(f"  Rev: [cyan]{p['reverse']['sequence']}[/cyan] (Tm-bind: {p['reverse']['tm_bind']}°C, GC: {p['reverse']['gc']}%, Panjang: {p['reverse']['length']} bp)")
                                else:
                                    console.print(f"  Fwd: {p['forward']['sequence']} (Tm: {p['forward']['tm']}°C, GC: {p['forward']['gc']}%)")
                                    console.print(f"  Rev: {p['reverse']['sequence']} (Tm: {p['reverse']['tm']}°C, GC: {p['reverse']['gc']}%)")
                            chat_history.append({"role": "assistant", "content": f"[Aksi: Berhasil mendesain {len(res)} primer PCR]"})
                    except Exception as e:
                        console.print(f"[!] Gagal desain primer: {e}")
                        chat_history.append({"role": "assistant", "content": f"[Aksi: Gagal merancang primer karena error: {e}]"})

            # Modul A
            elif action == "harmonize_data":
                from biopygeon.engines.q1_pipeline import harmonize_data
                in_csv = params.get("input_csv")
                out_csv = params.get("output_csv")
                strategy = params.get("strategy", "mean")
                base_method = params.get("baseline_method", "als")
                with console.status("[bold cyan]Mengharmonisasi data (ALS/Missing Value)...[/bold cyan]"):
                    res = harmonize_data(in_csv, out_csv, strategy=strategy, baseline_method=base_method)
                console.print(f"[bold green]{res}[/bold green]")
                if out_csv: save_run_metadata(action, params, [out_csv])
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})

            # Modul B
            elif action == "render_network":
                from biopygeon.engines.q1_pipeline import render_network
                in_csv = params.get("input_csv")
                out_tiff = params.get("output_tiff")
                out_html = params.get("output_html")
                src_col = params.get("source_col")
                tgt_col = params.get("target_col")
                nodes_csv = params.get("nodes_csv")
                with console.status("[bold cyan]Merender grafik SSN / Network...[/bold cyan]"):
                    res = render_network(in_csv, out_tiff, out_html, src_col, tgt_col, nodes_csv=nodes_csv)
                console.print(f"[bold green]{res}[/bold green]")
                files = []
                if out_tiff: files.append(out_tiff)
                if out_html: files.append(out_html)
                if files: save_run_metadata(action, params, files)
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})

            # Modul C
            elif action == "plot_q1_figure":
                from biopygeon.engines.q1_pipeline import plot_q1_figure
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "q1_plot.html")
                ptype = params.get("plot_type")
                x_col = params.get("x_col")
                y_col = params.get("y_col")
                with console.status(f"[bold cyan]Membuat plot publikasi {ptype.upper()} dengan statistik otomatis...[/bold cyan]"):
                    res = plot_q1_figure(in_csv, out_html, ptype, x_col, y_col)
                console.print(f"[bold green]{res}[/bold green]")
                if out_html: save_run_metadata(action, params, [out_html])
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})

            # Modul D
            elif action == "generate_methodology":
                from biopygeon.engines.q1_pipeline import generate_methodology
                output_txt = params.get("output_txt", "methodology.txt")
                baseline_method = params.get("baseline_method", "als")
                plot_type = params.get("plot_type", "boxplot")
                journal = params.get("journal", "nature")
                with console.status("[bold cyan]Menulis draf metodologi...[/bold cyan]"):
                    res = generate_methodology(output_txt, baseline_method, plot_type, journal)
                console.print(f"[bold green]{res}[/bold green]")
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})
                
            # Modul Premium: AI Word Formatter
            elif action == "format_manuscript":
                from biopygeon.engines.formatter import format_manuscript_engine
                draft_docx = params.get("draft_docx")
                template_docx = params.get("template_docx")
                output_docx = params.get("output_docx")
                
                with console.status("[bold cyan]Memformat dokumen XML dengan AI (menjaga sitasi Mendeley)...[/bold cyan]"):
                    res = format_manuscript_engine(draft_docx, template_docx, output_docx)
                console.print(f"[bold green]{res}[/bold green]")
                if output_docx: save_run_metadata(action, params, [output_docx])
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})
                
            # Modul Omics tambahan
            elif action == "plot_heatmap":
                from biopygeon.engines.omics import plot_heatmap
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "heatmap.html")
                with console.status("[bold cyan]Membuat Heatmap Interaktif...[/bold cyan]"):
                    res = plot_heatmap(in_csv, out_html)
                console.print(f"[bold green]{res}[/bold green]")
                if out_html: save_run_metadata(action, params, [out_html])
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})
                
            elif action == "plot_enrichment":
                from biopygeon.engines.omics import plot_enrichment
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "enrichment.html")
                with console.status("[bold cyan]Membuat plot pengayaan interaktif...[/bold cyan]"):
                    res = plot_enrichment(in_csv, out_html)
                console.print(f"[bold green]{res}[/bold green]")
                if out_html: save_run_metadata(action, params, [out_html])
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})
                
            elif action == "plot_volcano":
                from biopygeon.engines.omics import plot_volcano
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "volcano.html")
                pval_col = params.get("pvalue_col")
                fc_col = params.get("fc_col")
                pval_th = params.get("pval_threshold", 0.05)
                fc_th = params.get("log2fc_threshold", 1.0)
                gene_col = params.get("gene_col", None)
                
                with console.status("[bold cyan]Membuat Volcano Plot Interaktif...[/bold cyan]"):
                    res = plot_volcano(in_csv, out_html, pval_col, fc_col, pval_th, fc_th, gene_col)
                console.print(f"[bold green]{res}[/bold green]")
                if out_html: save_run_metadata(action, params, [out_html])
                chat_history.append({"role": "assistant", "content": f"[SYSTEM] {res}"})
                
            else:
                console.print(f"[bold red]Aksi '{action}' belum diimplementasikan di CLI.[/bold red]")

            # Batasi histori agar token tidak meledak (simpan 10 pesan terakhir)
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Sampai jumpa![/bold yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
