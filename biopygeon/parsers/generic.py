import pandas as pd
import os

def load_data(file_path: str) -> pd.DataFrame:
    """
    Membaca file data dengan cerdas.
    Mendeteksi pemisah (delimiter) dan membersihkan data kosong.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} tidak ditemukan.")
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        df = pd.read_csv(file_path)
    elif ext in ['.tsv', '.txt']:
        df = pd.read_csv(file_path, sep='\t')
    else:
        # Fallback ke deteksi otomatis engine python
        df = pd.read_csv(file_path, sep=None, engine='python')
        
    # Bersihkan baris yang sepenuhnya kosong (biasa terjadi dari output alat lab)
    df.dropna(how='all', inplace=True)
    return df
