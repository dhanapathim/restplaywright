import json
import tempfile

import yaml
import jsonref
from pathlib import Path
from datetime import datetime

class SwaggerPathExtractor:
    def __init__(self, swagger_path: str):
        self.swagger_path = Path(swagger_path)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = Path(tempfile.gettempdir()) / f"restapi_{timestamp}"
        print(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def to_plain_obj(self, obj):
        if isinstance(obj, dict):
            return {k: self.to_plain_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.to_plain_obj(i) for i in obj]
        return obj

    def load_spec(self):
        with open(self.swagger_path, "r", encoding="utf-8") as f:
            if self.swagger_path.suffix in [".yaml", ".yml"]:
                raw = yaml.safe_load(f)
            else:
                raw = json.load(f)
        resolved = jsonref.replace_refs(raw, merge_props=True)
        return self.to_plain_obj(resolved)

    def sanitize_filename(self, path: str):
        return path.strip("/").replace("/", "_").replace("{", "").replace("}", "") or "root"

    def extract(self) -> Path:  # ✅ THIS IS THE KEY METHOD!
        resolved_spec = self.load_spec()

        for path, path_def in resolved_spec.get("paths", {}).items():
            mini_spec = {
                "openapi": resolved_spec.get("openapi", "3.0.0"),
                "info": resolved_spec.get("info", {}),
                "servers": resolved_spec.get("servers", []),
                "security": resolved_spec.get("security", []),
                "paths": {path: path_def},
                "components": resolved_spec.get("components", {})
            }

            filename = self.sanitize_filename(path)
            out_file = self.output_dir / f"{filename}.json"

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(mini_spec, f, indent=2)

            print(f"✅ Extracted {path} → {out_file}")

        return self.output_dir
