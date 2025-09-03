import json
import os
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
                self.get_file_name(spec, path, method, operation)
        print(f"\n📁 Output directory: {self.output_dir}")
        return self.output_dir

    def get_file_name(self, spec, path, method, operation):
        mini_spec = {
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
            json.dump(mini_spec, f, indent=2)

        print(f"✅ Saved: {output_file}")

    def get_update_add_paths_and_methods(self, added_paths, updated_paths):
        spec = self.load_spec()
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            if path in updated_paths or path in added_paths:
                for method, operation in methods.items():
                    self.get_file_name(spec, path, method, operation)
        return self.output_dir

    def remove_files(self, deleted_paths, target_folder):
        try:
            clean_data = [path.strip("/").replace("/", "_").replace("{", "").replace("}", "") for path in deleted_paths]
            target_folder += "/tests"
            for file in os.listdir(target_folder):
                file_path = os.path.join(target_folder, file)

                if not os.path.isfile(file_path):
                    continue  # Skip directories
                if any(file.startswith(prefix) for prefix in clean_data):
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")
        except Exception as e:
            print(f"Error accessing folder {target_folder}: {e}")
