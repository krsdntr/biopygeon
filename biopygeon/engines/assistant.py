import requests
import json
from biopygeon.config import get_groq_key

GROQ_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b"
]

def _call_groq_with_fallback(system_prompt: str, user_prompt: str = None, messages_history: list = None, temperature: float = 0.2, max_tokens: int = 500, response_format: dict = None, tools: list = None, tool_choice: str = "auto") -> dict:
    """Fungsi helper untuk memanggil API Groq dengan fallback otomatis jika gagal/rate-limit."""
    api_key = get_groq_key()
    if not api_key:
        raise ValueError("API Key Groq tidak ditemukan. Gunakan 'biopygeon auth set-key --groq-key XYZ'.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    last_error = None
    for model in GROQ_MODELS:
        messages = [{"role": "system", "content": system_prompt}]
        
        if messages_history:
            messages.extend(messages_history)
        elif user_prompt:
            messages.append({"role": "user", "content": user_prompt})
            
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']
        except requests.exceptions.RequestException as e:
            # Jika mendapatkan error 400 (Tool Use Failed), 429 (Rate Limit) atau error server 5xx, coba model berikutnya
            if response is not None and response.status_code in [400, 429, 500, 503]:
                last_error = e
                continue
            else:
                # Error lain (seperti 400 Bad Request atau 401 Unauthorized) langsung lempar exception
                raise RuntimeError(f"Gagal berkomunikasi dengan Groq API (Model {model}): {e}")
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Semua model Groq gagal diakses. Error terakhir: {last_error}")


def ask_groq(prompt: str) -> str:
    """(Deprecated) Mengirim pertanyaan panduan dasar."""
    system_message = (
        "Anda adalah Biopygeon Assistant. Berikan penjelasan yang komprehensif, namun tetap relevan dan tidak bertele-tele."
    )
    msg = _call_groq_with_fallback(system_prompt=system_message, user_prompt=prompt, temperature=0.2, max_tokens=800)
    return msg.get("content", "") or ""


def generate_report(df_jurnal, user_query: str = None) -> str:
    """Mensintesis laporan dari Top 5 jurnal."""
    top_5 = df_jurnal.head(5) if hasattr(df_jurnal, 'head') else df_jurnal[:5]
    if len(top_5) == 0:
        return "Data tidak cukup untuk dianalisis."

    abstracts_text = ""
    # Mendukung dataframe maupun list of dict
    if hasattr(top_5, 'iterrows'):
        for idx, row in top_5.iterrows():
            abstracts_text += f"\nJurnal {idx+1}: {row.get('title', '')}\nAbstrak: {row.get('abstract', 'Tidak tersedia')}\n"
    else:
        for idx, row in enumerate(top_5):
            abstracts_text += f"\nJurnal {idx+1}: {row.get('title', '')}\nAbstrak: {row.get('abstract', 'Tidak tersedia')}\n"

    if user_query:
        system_msg = (
            f"Anda adalah seorang penulis sains dan ilmuwan riset ahli. Tugas UTAMA Anda adalah menjawab pertanyaan pengguna secara komprehensif: '{user_query}'.\n"
            "Gunakan pengetahuan medis dan ilmiah internal Anda yang luas untuk memberikan jawaban langsung dan akurat. "
            "Sebagai tambahan, Anda diberikan 5 abstrak jurnal terbaru di bawah ini. JANGAN HANYA merangkum abstrak tersebut. "
            "Gunakan abstrak tersebut sebagai *bukti pendukung (sitasi)* untuk memperkuat penjelasan Anda jika relevan. "
            "Jika abstrak kurang relevan, tetap fokus menjawab pertanyaan berdasarkan keahlian Anda, namun sebutkan tren fokus riset terbaru berdasarkan abstrak tersebut. "
            "Buatlah interpretasi yang hidup, kritis, dan berwawasan luas. PENTING: Anda WAJIB menyertakan sitasi berupa nomor jurnal (misalnya [1], [1, 3]) setiap kali mengutip fakta spesifik dari daftar abstrak."
        )
    else:
        system_msg = (
            "Anda adalah seorang penulis sains dan ilmuwan riset ahli. Tulislah sebuah sintesis naratif bergaya "
            "jurnalistik ilmiah (seperti artikel di Nature atau Science) berdasarkan abstrak jurnal-jurnal berikut. "
            "JANGAN sekadar mendaftar 'Jurnal 1 membahas A, Jurnal 2 membahas B'. Sebaliknya, jalinlah temuan-temuan "
            "tersebut menjadi sebuah cerita ilmiah yang mengalir. Soroti konsensus utama, tren inovasi, kontradiksi, "
            "serta batasan riset saat ini. Buatlah interpretasi yang hidup, kritis, dan berwawasan luas. PENTING: Anda WAJIB menyertakan "
            "sitasi berupa nomor jurnal (misalnya [1], [1, 3]) setiap kali Anda mengutip atau merujuk pada fakta/temuan spesifik."
        )

    try:
        msg = _call_groq_with_fallback(system_prompt=system_msg, user_prompt=abstracts_text, temperature=0.3, max_tokens=2500)
        return msg.get("content", "") or ""
    except Exception as e:
        return f"Terjadi kesalahan saat memproses narasi AI: {e}"

def generate_generic_interpretation(data_str: str, analysis_type: str) -> str:
    """Menghasilkan interpretasi ilmiah AI dari data analisis generik (ProtParam, BLAST, dll)."""
    system_msg = (
        "Anda adalah ilmuwan bioinformatika senior. Tugas Anda adalah memberikan interpretasi "
        f"eksekutif dari hasil analisis {analysis_type} yang diberikan oleh pengguna. "
        "Fokus pada wawasan biologis yang relevan (misalnya kestabilan protein, signifikansi evolusi, "
        "atau makna dari nilai p-value). Gunakan bahasa profesional dan terstruktur dalam 2-3 paragraf."
    )
    try:
        msg = _call_groq_with_fallback(system_prompt=system_msg, user_prompt=data_str, temperature=0.3, max_tokens=500)
        return msg.get("content", "") or ""
    except Exception as e:
        return f"Terjadi kesalahan saat memproses narasi AI: {e}"


def agent_router(prompt: str, history: list = None) -> dict:
    from biopygeon.engines.tool_registry import ROUTER_TOOLS_SCHEMA as TOOLS
    
    """
    Agen AI membaca maksud pengguna dan mengembalikan instruksi eksekusi alat dalam format JSON kompatibel ke backend.
    """
    system_msg = """Anda adalah Agen Penghubung (Router) pintar dalam aplikasi Biopygeon.
Tugas Anda adalah memahami permintaan pengguna dan memutuskan alat mana yang akan dipanggil.

🚨 ATURAN EMAS UNTUK MULTI-LANGKAH (PRIORITAS UTAMA) 🚨
JIKA pengguna meminta tugas yang secara logis membutuhkan LEBIH DARI SATU langkah/alat, Anda WAJIB memanggil `run_autonomous_pipeline`.
Contoh tugas multi-langkah:
- "cari protein X dan analisis protparam" (Butuh alat pencari/pengunduh, LALU alat protparam)
- "1SLT_A analisis protparam" (Butuh mengunduh 1SLT_A, LALU menganalisisnya)
- "unduh data lalu plot"
JANGAN PERNAH memanggil alat tunggal (seperti `fetch_sequence`) jika pengguna meminta analisis atas target tersebut yang membutuhkan alat lain!

PENTING: JANGAN mengarang parameter. Jika opsi tidak wajib, biarkan kosong. Jangan menanyakan format CSV.
JIKA pengguna meminta aksi tunggal (misal hanya "unduh 1SLT"), panggil Fungsi tersebut langsung.

KHUSUS UNTUK `lit_search`: Jika pengguna menggunakan bahasa Indonesia, terjemahkan ke Inggris.
PASTIKAN parameter query SELALU menggunakan topik dari percakapan TERAKHIR pengguna.
"""
    
    messages = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    try:
        message = _call_groq_with_fallback(
            system_prompt=system_msg,
            messages_history=messages,
            temperature=0.1,
            max_tokens=800,
            tools=TOOLS,
            tool_choice="auto"
        )
        
        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            action = tool_call["function"]["name"]
            try:
                params = json.loads(tool_call["function"]["arguments"])
            except:
                params = {}
            return {
                "action": action,
                "params": params,
                "reply": f"Baik, saya akan mengeksekusi {action}..."
            }
        else:
            content = message.get("content", "") or ""
            # Fallback jika LLM berhalusinasi teks aksi alih-alih memanggil alat
            p_lower = prompt.lower()
            if "ekspor" in p_lower or "export" in p_lower:
                if "csv" in p_lower:
                    return {"action": "export_results", "params": {"format": "csv"}, "reply": "Baik, saya akan mengeksekusi export_results (CSV)..."}
                elif "html" in p_lower:
                    return {"action": "export_results", "params": {"format": "html"}, "reply": "Baik, saya akan mengeksekusi export_results (HTML)..."}
                elif "pdf" in p_lower:
                    return {"action": "export_results", "params": {"format": "pdf"}, "reply": "Baik, saya akan mengeksekusi export_results (PDF)..."}
                    
            return {
                "action": "chat",
                "params": {},
                "reply": content
            }
    except Exception as e:
        return {
            "action": "chat",
            "params": {},
            "reply": f"Maaf, terjadi masalah saat menghubungi AI: {str(e)}"
        }
