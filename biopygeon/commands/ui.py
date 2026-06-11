import sys
import subprocess
import os
import typer
from rich.console import Console

app = typer.Typer(help="Jalankan antarmuka Conversational Web UI (Streamlit).")
console = Console()

@app.callback(invoke_without_command=True)
def run_ui(
    ctx: typer.Context,
    port: int = typer.Option(8501, "--port", "-p", help="Port untuk server Streamlit")
):
    """
    Menjalankan Conversational Web UI (Streamlit) berbasis browser yang estetik mirip Claude.
    """
    if ctx.invoked_subcommand is not None:
        return
        
    import biopygeon
    pkg_dir = os.path.dirname(biopygeon.__file__)
    ui_app_path = os.path.join(pkg_dir, "ui_app.py")
    
    if not os.path.exists(ui_app_path):
        # Fallback to root app.py if package file is not found
        ui_app_path = os.path.join(os.getcwd(), "app.py")
        
    console.print(f"[bold green][UI][/bold green] Memulai Biopygeon Conversational Web UI...")
    console.print(f"[dim]Menjalankan file: {ui_app_path}[/dim]")
    console.print(f"[dim]Akses antarmuka di: http://localhost:{port}[/dim]\n")
    
    try:
        # Run streamlit command in subprocess
        cmd = [sys.executable, "-m", "streamlit", "run", ui_app_path, "--server.port", str(port)]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Server Web UI dimatikan.[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Gagal menjalankan Web UI: {e}[/bold red]")
