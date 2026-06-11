import json
import os
from datetime import datetime
from pathlib import Path

AUDIT_FILE = str(Path.home() / "biopygeon_audit.jsonl")

def log_action(agent_type: str, action: str, params: dict, status: str = "success", error: str = ""):
    """
    Mencatat setiap pemanggilan alat ke dalam jejak audit (Audit Trail).
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_type": agent_type,
        "action": action,
        "parameters": params,
        "status": status,
        "error": error
    }
    try:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Failed to write audit log: {e}")
