import json
import tempfile
import yaml
from pathlib import Path
from datetime import datetime

class PathMethodExtractor:
    def __init__(self, swagger_path: str):
        self.swagger_path = Path(swagger_path)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_dir = Path(tempfile.gettempdir()) / f"restapi{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def to_plain_obj(self, obj):
        if isinstance(obj, dict):
            return {k: self.to_plain_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.to_plain_obj(i) for i in obj]
        return obj

    def sanitize_filename(self, path: str, method: str):
        clean_path = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        filename_prefix = clean_path if clean_path else "root"
        return f"{filename_prefix}_{method.upper()}"

    def load_spec(self):
        with open(self.swagger_path, "r", encoding="utf-8") as f:
            if self.swagger_path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            else:
                return json.load(f)

    def extract_paths_and_methods(self):
        spec = self.load_spec()
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            for method, operation in methods.items():
                mini_spec = {
                    "openapi": spec.get("openapi", "3.0.0"),
                    "info": spec.get("info", {}),
                    "servers": spec.get("servers", []),
                    "security": spec.get("security", []),
                    "paths": {
                        path: {
                            method: operation
                        }
                    },
                    "components": spec.get("components", {})
                }

                filename = self.sanitize_filename(path, method) + ".json"
                output_file = self.output_dir / filename

                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(mini_spec, f, indent=2,default=str)

                print(f"✅ Saved: {output_file}")

        print(f"\n📁 Output directory: {self.output_dir}")
        return self.output_dir
