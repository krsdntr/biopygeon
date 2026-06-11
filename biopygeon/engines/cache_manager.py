import os
import time
import shutil

CACHE_DIR_NAME = ".biopygeon_cache"
MAX_CACHE_SIZE_MB = 100
MAX_AGE_HOURS = 24

def get_cache_dir() -> str:
    """Mendapatkan path absolute ke direktori cache, membuatnya jika belum ada."""
    cache_path = os.path.join(os.path.expanduser("~"), ".biopygeon", "cache")
    os.makedirs(cache_path, exist_ok=True)
    return cache_path

def enforce_cache_limits(progress_callback=None) -> None:
    """Membersihkan file lama jika cache terlalu besar atau sudah kadaluwarsa."""
    cache_path = get_cache_dir()
    
    if not os.path.exists(cache_path):
        return
        
    current_time = time.time()
    total_size = 0
    files_to_check = []
    
    for filename in os.listdir(cache_path):
        filepath = os.path.join(cache_path, filename)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            total_size += stat.st_size
            files_to_check.append({
                "path": filepath,
                "size": stat.st_size,
                "mtime": stat.st_mtime
            })
            
    # Hapus file yang lebih tua dari MAX_AGE_HOURS
    age_limit = current_time - (MAX_AGE_HOURS * 3600)
    for f in files_to_check:
        if f["mtime"] < age_limit:
            try:
                os.remove(f["path"])
                total_size -= f["size"]
                f["deleted"] = True
            except Exception:
                pass
                
    # Jika masih melebih MAX_CACHE_SIZE_MB, hapus file tertua sampai ukuran aman
    files_to_check = [f for f in files_to_check if not f.get("deleted", False)]
    files_to_check.sort(key=lambda x: x["mtime"]) # Sort by oldest first
    
    max_bytes = MAX_CACHE_SIZE_MB * 1024 * 1024
    
    while total_size > max_bytes and files_to_check:
        oldest = files_to_check.pop(0)
        try:
            os.remove(oldest["path"])
            total_size -= oldest["size"]
        except Exception:
            pass

def clear_all_cache() -> None:
    """Menghapus semua isi direktori cache secara manual."""
    cache_path = get_cache_dir()
    if os.path.exists(cache_path):
        shutil.rmtree(cache_path)
    get_cache_dir()
