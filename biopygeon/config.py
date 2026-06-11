import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".bio_pipeline"
CONFIG_FILE = CONFIG_DIR / "config.json"

def get_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(config_dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_dict, f, indent=4)
    try:
        if os.name != 'nt':
            import os
            os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass

def get_groq_key():
    # Cek env variable dulu, fallback ke config file
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key
    
    config = get_config()
    return config.get("groq_api_key", "")

def set_groq_key(key: str):
    config = get_config()
    config["groq_api_key"] = key
    save_config(config)

def get_s2_key():
    env_key = os.environ.get("S2_API_KEY", "").strip()
    if env_key:
        return env_key
    
    config = get_config()
    return config.get("s2_api_key", "")

def set_s2_key(key: str):
    config = get_config()
    config["s2_api_key"] = key
    save_config(config)

def get_user_email():
    env_email = os.environ.get("BIOPYGEON_EMAIL", "").strip()
    if env_email:
        return env_email
    
    config = get_config()
    return config.get("user_email", "")

def set_user_email(email: str):
    config = get_config()
    config["user_email"] = email
    save_config(config)
