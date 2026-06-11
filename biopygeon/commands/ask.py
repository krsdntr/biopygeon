import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(no_args_is_help=True)
console = Console()

@app.callback(invoke_without_command=True)
def ask(
    ctx: typer.Context,
    prompt: str = typer.Argument(..., help="Pertanyaan Anda menggunakan bahasa alami")
):
    """
    Asisten Peneliti Virtual (berbasis LLM Groq) untuk memandu penggunaan biopygeon.
    """
    if ctx.invoked_subcommand is not None:
        return
        
    console.print("[bold blue][AI][/bold blue] Memproses pertanyaan Anda...")
    
    from biopygeon.engines.assistant import ask_groq
    
    try:
        jawaban = ask_groq(prompt)
        console.print(Panel(jawaban, title="[bold green]Saran Asisten", expand=False))
    except Exception as e:
        console.print(f"[bold red][Error][/bold red] {str(e)}")
        raise typer.Exit(code=1)
