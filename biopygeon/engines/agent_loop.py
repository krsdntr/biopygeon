import json
import time
from biopygeon.engines.assistant import _call_groq_with_fallback
from biopygeon.engines.tool_registry import FULL_FUNCTIONS, FULL_TOOLS_SCHEMA
from biopygeon.engines.audit_logger import log_action

def run_autonomous_loop(user_prompt: str, tools_schema: list = FULL_TOOLS_SCHEMA, function_registry: dict = FULL_FUNCTIONS, max_steps: int = 5, progress_callback=None) -> str:
    """
    Menjalankan loop ReAct secara otonom.
    progress_callback adalah fungsi (str) -> None untuk UI update.
    """
    system_prompt = (
        "Anda adalah Biopygeon Autonomous Agent, asisten AI canggih. Anda memiliki akses ke berbagai fungsi (alat/tools). "
        "Gunakan alat-alat tersebut secara bertahap untuk menyelesaikan perintah pengguna. "
        "Selalu periksa output dari alat sebelum melangkah ke tahap selanjutnya. "
        "PENTING: Jangan mencoba menebak data. Jika butuh data, gunakan alat (misal http_request atau web_scrape). "
        "Jika butuh perhitungan, gunakan run_python. "
        "Berikan jawaban akhir yang komprehensif kepada pengguna HANYA jika Anda sudah yakin tugas selesai."
    )
    
    messages = [{"role": "user", "content": user_prompt}]
    
    if progress_callback:
        progress_callback("Memulai pemikiran otonom...")
        
    for step in range(max_steps):
        try:
            response_msg = _call_groq_with_fallback(
                system_prompt=system_prompt,
                messages_history=messages,
                temperature=0.1,
                max_tokens=2000,
                tools=tools_schema,
                tool_choice="auto"
            )
            
            messages.append(response_msg)
            
            # Jika ada tool calls
            tool_calls = response_msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    func_name = tc['function']['name']
                    try:
                        func_args = json.loads(tc['function']['arguments'])
                    except json.JSONDecodeError:
                        func_args = {}
                        
                    if progress_callback:
                        progress_callback(f"Menjalankan alat: {func_name} ...")
                        
                    # Eksekusi fungsi
                    if func_name in function_registry:
                        try:
                            # Log action
                            log_action("Autonomous_ReAct_Agent", func_name, func_args, "success")
                            
                            # call the function with unpacked args
                            tool_result = function_registry[func_name](**func_args)
                        except Exception as e:
                            log_action("Autonomous_ReAct_Agent", func_name, func_args, "error", str(e))
                            tool_result = f"Error execution: {str(e)}"
                    else:
                        tool_result = f"Error: Function {func_name} not found in registry."
                        
                    # Simpan hasil alat
                    messages.append({
                        "tool_call_id": tc['id'],
                        "role": "tool",
                        "name": func_name,
                        "content": str(tool_result)[:1500] + ("..." if len(str(tool_result)) > 1500 else "")
                    })
                    
                # Beri jeda kecil (backoff) untuk mencegah limit rate
                time.sleep(1)
                continue # Lanjut ke loop berikutnya untuk membiarkan AI membaca hasil
                
            else:
                # Tidak ada tool calls, berarti AI sudah memberikan jawaban akhir
                content = response_msg.get("content", "")
                if progress_callback:
                    progress_callback("Tugas otonom selesai!")
                return content, messages
                
        except Exception as e:
            if "429" in str(e):
                if progress_callback:
                    progress_callback("Terkena Rate Limit Groq. Menunggu 5 detik...")
                time.sleep(5)
                continue
            return f"Terjadi kesalahan pada autonomous loop: {e}", messages
            
    # Jika loop maksimal tercapai
    if progress_callback:
        progress_callback("Batas maksimum langkah tercapai.")
    return "Maaf, tugas terlalu kompleks atau mencapai batas loop maksimum (5 steps). Sebagian data mungkin sudah diproses.", messages
