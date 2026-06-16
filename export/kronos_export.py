import json
import os
from dataclasses import asdict
from datetime import datetime

class KronosExport:
    def __init__(self, target, session_id: str):
        self.target = target
        self.session_id = session_id

    def save(self, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        name = getattr(
            self.target, "domain",
            getattr(self.target, "name", "target")
        ).replace(" ", "_")
        path = os.path.join(
            output_dir,
            f"kronos_{name}_{self.session_id}.json"
        )
        return self.save_to_path(path)

    def save_to_path(self, path: str) -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "session_id": self.session_id,
            "generated_at": datetime.now().isoformat(),
            "target": asdict(self.target)
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return path
