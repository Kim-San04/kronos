import json
import os
from datetime import datetime

class Session:
    def __init__(self, session_id: str, target_name: str, target_type: str):
        self.session_id = session_id
        self.target_name = target_name
        self.target_type = target_type
        self.started_at = datetime.now().isoformat()
        self.events = []

    def log(self, module: str, event: str, data=None):
        self.events.append({
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "event": event,
            "data": data
        })

    def save(self, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(
            output_dir,
            f"session_{self.session_id}.json"
        )
        with open(path, "w") as f:
            json.dump({
                "session_id": self.session_id,
                "target": self.target_name,
                "type": self.target_type,
                "started_at": self.started_at,
                "events": self.events
            }, f, indent=2)
        return path
