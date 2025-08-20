import sys
import json
import yaml
from pathlib import Path
from openapi_spec_validator import validate
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError


class OpenAPISpecValidator:
    VALID_EXTENSIONS = ['.json', '.yaml', '.yml']

    def __init__(self, swagger_file: str):
        self.swagger_file = swagger_file
        self.spec = None

    def run_validation(self):
        path = Path(self.swagger_file)
        self._check_file(path)
        self.spec = self._load_spec(path)
        self._check_openapi_version(self.spec)
        self._validate_spec(self.spec)

    def _check_file(self, path: Path):
        if not path.exists():
            print(f"❌ File does not exist: {path}")
            sys.exit(1)

        if path.suffix not in self.VALID_EXTENSIONS:
            print(f"❌ Invalid file extension: {path.suffix}. Only .json, .yaml, or .yml allowed.")
            sys.exit(1)

        print(f"📄 File detected: {path.name}")

    def _load_spec(self, file_path: Path):
        with file_path.open('r', encoding='utf-8') as f:
            if file_path.suffix == '.json':
                return json.load(f)
            else:
                return yaml.safe_load(f)

    def _check_openapi_version(self, spec: dict):
        version = spec.get("openapi")
        if not version:
            print("❌ 'openapi' field not found. This is not a valid OpenAPI 3.x+ spec.")
            sys.exit(1)

        major, minor, *_ = version.split('.')
        if int(major) < 3:
            print(f"❌ OpenAPI version {version} is not supported. Must be >= 3.0.0.")
            sys.exit(1)

        print(f"🔍 OpenAPI version {version} detected — OK.")

    def _validate_spec(self, spec: dict):
        try:
            validate(spec)
            print("✅ OpenAPI 3.x spec is valid.")
        except RecursionError:
            print("❌ Validation failed due to circular or deeply nested references (maximum recursion depth).")
            sys.exit(1)
        except OpenAPIValidationError as e:
            print(f"❌ OpenAPI spec is invalid: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            sys.exit(1)
