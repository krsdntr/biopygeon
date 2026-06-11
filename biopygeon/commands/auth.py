import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()

@app.command("set-key")
def auth(
    groq_key: str = typer.Option(None, "--groq-key", help="API Key dari platform Groq Cloud"),
    s2_key: str = typer.Option(None, "--s2-key", help="API Key dari platform Semantic Scholar"),
    email: str = typer.Option(None, "--email", help="Email untuk OpenAlex Polite Pool dan NCBI")
):
    """
    Menyimpan kredensial API secara lokal untuk fitur cerdas.
    """
    from biopygeon.config import set_groq_key, set_s2_key, set_user_email
    try:
        if groq_key:
            set_groq_key(groq_key)
            console.print("[bold green][OK][/bold green] Kunci Groq API berhasil disimpan secara lokal.")
        if s2_key:
            set_s2_key(s2_key)
            console.print("[bold green][OK][/bold green] Kunci Semantic Scholar API berhasil disimpan secara lokal.")
        if email:
            set_user_email(email)
            console.print("[bold green][OK][/bold green] Email pengguna berhasil disimpan secara lokal.")
            
        if not groq_key and not s2_key and not email:
            console.print("[!] Tidak ada argumen yang dimasukkan. Gunakan --help untuk melihat opsi.")
    except Exception as e:
        console.print(f"[bold red][Error][/bold red] Gagal menyimpan kunci: {e}")

@app.command("status")
def status():
    """
    Melihat status API Key yang tersimpan lokal secara aman.
    """
    from biopygeon.config import get_groq_key, get_s2_key, get_user_email
    groq = get_groq_key()
    s2 = get_s2_key()
    email = get_user_email()
    
    def mask_key(k):
        return k[:4] + "*" * 15 + k[-4:] if len(k) > 10 else "Tidak di-set"
        
    console.print("[bold cyan]Status Kredensial Lokal (Biopygeon):[/bold cyan]")
    console.print(f"Groq API Key : {mask_key(groq) if groq else 'Tidak di-set'}")
    console.print(f"S2 API Key   : {mask_key(s2) if s2 else 'Tidak di-set'}")
    console.print(f"User Email   : {email if email else 'Tidak di-set'}")
