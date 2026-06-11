import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Analisis Sekuens & Struktur Biologi", no_args_is_help=True)
console = Console()

@app.command("protparam")
def protparam(sequence: str):
    """Menghitung properti fisikokimia protein."""
    from biopygeon.engines.biology import calculate_protparam
    try:
        with console.status("[bold blue]Menghitung parameter...[/bold blue]"):
            res_str = calculate_protparam(sequence)
        console.print("[bold cyan]Hasil ProtParam:[/bold cyan]")
        console.print(res_str)
    except Exception as e:
        console.print(f"[bold red]Gagal analisis ProtParam:[/bold red] {e}")

@app.command("blast")
def blast(sequence: str, program: str = typer.Option("blastp", "--program", "-p", help="blastp atau blastn")):
    """Melakukan pencarian NCBI BLAST."""
    from biopygeon.engines.biology import run_ncbi_blast
    try:
        with console.status(f"[bold blue]Menjalankan {program} di NCBI (ini bisa memakan waktu)...[/bold blue]") as status:
            def update_status(msg):
                status.update(f"[bold blue]{msg}[/bold blue]")
            results = run_ncbi_blast(sequence, program=program, progress_callback=update_status)
            
        if not results:
            console.print("[!] Tidak ada homologi ditemukan.")
            return
            
        table = Table(title=f"Hasil BLAST ({len(results)} hits)", show_header=True)
        table.add_column("Title", style="cyan")
        table.add_column("E-value", style="magenta")
        table.add_column("Identity", style="green")
        for r in results:
            table.add_row(r['title'], str(r['e_value']), r['identity'])
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Gagal analisis BLAST:[/bold red] {e}")

@app.command("primer")
def primer_design(
    sequence: str = typer.Argument(..., help="Sekuens DNA target"),
    min_size: int = typer.Option(150, help="Ukuran minimal produk PCR"),
    max_size: int = typer.Option(500, help="Ukuran maksimal produk PCR"),
    num: int = typer.Option(5, help="Jumlah pasang primer yang dihasilkan")
):
    """
    Desain pasangan primer PCR untuk suatu sekuens DNA menggunakan engine primer3.
    """
    from biopygeon.engines.biology import design_pcr_primers
    from rich.table import Table
    try:
        with console.status("[bold blue]Mendesain primer PCR...[/bold blue]"):
            primers = design_pcr_primers(sequence, prod_size_min=min_size, prod_size_max=max_size, num_return=num)
            
        if not primers:
            console.print("[!] Tidak dapat menemukan primer yang cocok untuk kriteria tersebut.")
            raise typer.Exit(1)
            
        table = Table(title=f"Hasil Desain Primer PCR ({len(primers)} Pasang)", show_header=True)
        table.add_column("No", style="dim", width=4)
        table.add_column("Forward (Tm/GC%)", style="cyan")
        table.add_column("Reverse (Tm/GC%)", style="magenta")
        table.add_column("Product Size", style="green")
        
        for p in primers:
            fw_info = f"{p['forward_seq']}\n({p['forward_tm']}°C / {p['forward_gc']}%)"
            rv_info = f"{p['reverse_seq']}\n({p['reverse_tm']}°C / {p['reverse_gc']}%)"
            table.add_row(str(p['pair_id']), fw_info, rv_info, f"{p['product_size']} bp")
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]Gagal mendesain primer:[/bold red] {e}")

@app.command("pdb")
def pdb_search(query: str, limit: int = typer.Option(5, "--limit", "-l", help="Jumlah batas hasil")):
    """Mencari struktur protein di database PDB."""
    from biopygeon.engines.biology import search_protein_structure
    try:
        with console.status(f"[bold blue]Mencari struktur '{query}' di NCBI PDB...[/bold blue]") as status:
            def update_status(msg):
                status.update(f"[bold blue]{msg}[/bold blue]")
            results = search_protein_structure(query, max_results=limit, progress_callback=update_status)
            
        if not results:
            console.print(f"[!] Struktur untuk '{query}' tidak ditemukan.")
            return
            
        table = Table(title=f"Hasil Pencarian Struktur ({len(results)} PDB)", show_header=True)
        table.add_column("PDB ID", style="cyan")
        table.add_column("Judul", style="green")
        table.add_column("Metode")
        table.add_column("Resolusi", justify="right")
        for r in results:
            table.add_row(r.get("pdb_id", "N/A"), r.get("title", "No Title"), r.get("method", "Unknown"), str(r.get("resolution", "N/A")))
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Gagal mencari struktur:[/bold red] {e}")

@app.command("prepare-docking")
def prepare_docking(input_path: str, output_path: str):
    """Mempersiapkan PDB untuk docking dengan menghapus molekul air & heteroatom."""
    from biopygeon.engines.biology import clean_pdb_for_docking
    try:
        with console.status("[bold blue]Membersihkan file PDB...[/bold blue]"):
            res_path = clean_pdb_for_docking(input_path, output_path)
        console.print(f"[bold green][OK][/bold green] File docking siap di: {res_path}")
    except Exception as e:
        console.print(f"[bold red]Gagal membersihkan PDB:[/bold red] {e}")

@app.command("msa")
def msa(
    input_file: str = typer.Argument(..., help="Path ke file FASTA input"),
    output_file: str = typer.Option("alignment_result.fasta", "--output", "-o", help="Path tujuan penyimpanan file hasil FASTA")
):
    """Melakukan Multiple Sequence Alignment via EBI Clustal Omega."""
    from biopygeon.engines.biology import run_ebi_clustalo
    try:
        with console.status(f"[bold blue]Menginisialisasi MSA ke server EBI...[/bold blue]") as status:
            def update_status(msg):
                status.update(f"[bold blue]{msg}[/bold blue]")
            out_path = run_ebi_clustalo(input_file, output_file, progress_callback=update_status)
        console.print(f"[bold green]Alignment selesai! Hasil disimpan di {out_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Gagal melakukan MSA:[/bold red] {e}")
