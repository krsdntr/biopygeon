import typer
from rich.console import Console

from biopygeon.commands import omics, publish, lit, auth, ask, chat, bio, ui

app = typer.Typer(help="Biopygeon CLI: The Last Mile Publication Aggregator", no_args_is_help=True)
console = Console()

# Menambahkan subcommands
app.add_typer(omics.app, name="omics", help="Analisis dan filter data Omics")
app.add_typer(publish.app, name="publish", help="Render data terproses menjadi figur publikasi")
app.add_typer(lit.app, name="lit", help="Cari dan himpun literatur saintifik (OpenAlex)")
app.add_typer(auth.app, name="auth", help="Otentikasi dan manajemen kunci API lokal")
app.add_typer(ask.app, name="ask", help="(Deprecated) Asisten cerdas berbasis AI Groq")
app.add_typer(chat.app, name="chat", help="Mode agen interaktif (Agentic Chat)")
app.add_typer(bio.app, name="bio", help="Analisis Sekuens & Struktur Biologi (ProtParam, BLAST, Docking)")
app.add_typer(ui.app, name="ui", help="Jalankan antarmuka Conversational Web UI (Streamlit)")

if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        from rich.console import Console
        Console().print("\n[bold yellow]Operasi dibatalkan oleh pengguna (Ctrl+C).[/bold yellow]")
    except Exception as e:
        from rich.console import Console
        from biopygeon.logger import logger
        logger.error(f"Fatal error: {e}", exc_info=True)
        Console().print(f"\n[bold red]Kesalahan Fatal:[/bold red] Terjadi kesalahan tak terduga. Silakan periksa log (.biopygeon/logs/app.log)")
