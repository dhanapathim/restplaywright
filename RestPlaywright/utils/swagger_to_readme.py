import os
import json
import yaml
from pathlib import Path

class SwaggerToReadme:
    def __init__(self, swagger_path, output_path):
        self.swagger_path = Path(swagger_path)
        self.output_path = Path(output_path)/"README.MD"
        self.swagger = self._load_swagger()

    def _load_swagger(self):
        ext = self.swagger_path.suffix.lower()
        with open(self.swagger_path, "r", encoding="utf-8") as f:
            if ext == ".json":
                return json.load(f)
            elif ext in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            else:
                raise ValueError("Swagger file must be JSON or YAML")

    def generate_readme(self):
        info = self.swagger.get("info", {})
        title = info.get("title", "API")
        version = info.get("version", "N/A")
        description = info.get("description", "").strip()

        servers = self.swagger.get("servers", [])
        base_urls = [s.get("url") for s in servers] if servers else ["N/A"]

        # Extract endpoints
        paths = self.swagger.get("paths", {})
        endpoints_summary = []
        for path, methods in paths.items():
            for method, details in methods.items():
                summary = details.get("summary", "")
                endpoints_summary.append(f"- `{method.upper()} {path}` → {summary}")

        # Extract security/auth info
        security_schemes = self.swagger.get("components", {}).get("securitySchemes", {})
        auth_summary = []
        for name, scheme in security_schemes.items():
            scheme_in = scheme.get("in", "")
            scheme_type = scheme.get("type", "")
            auth_summary.append(f"- {name}: {scheme_type} ({scheme_in})")

        # Build README content
        READMEcontent = f""" 
# 🧪 QA REST Automation Testing Workflow

This repository contains an automated **REST API testing framework** powered by **Playwright**.  
It is designed to:  

- Parse **Swagger/OpenAPI** specifications  
- Auto-generate **Playwright tests** for each endpoint  
- Validate **request → response content-types** (JSON / XML)  
- Produce detailed reports with **Allure**  
- Support **CI/CD integration**  

---
##{title}

{description if description else ''}

## 📌 API Overview
- **Version:** {version}
- **Base URLs:** {", ".join(base_urls)}

## 🚀 Endpoints
""" + "\n".join(endpoints_summary) + """

---

## 🔑 Authentication
""" + ("\n".join(auth_summary) if auth_summary else "No authentication required.") + """

---

## ⚙️ Content Types
- **Requests:** application/json, application/xml, application/x-www-form-urlencoded
- **Responses:** application/json, application/xml

---
## 📂Playwright Project Structure

.github/workflows/playwright.yml
allure-report/
allure-results/
node_modules/
test-results/
tests/
  ├── pet_findByStatus_GET.spec.js
  ├── pet_findByTags_GET.spec.js
  ├── pet_petId_DELETE.spec.js
  ├── pet_petId_GET.spec.js
  ├── pet_petId_POST.spec.js
 
.env
.gitignore
auth.json
global-setup.js
package.json
package-lock.json
playwright.config.js
README.md



## 🧪 How to Test (with Playwright)

Playwright tests can be auto-generated to cover:
- Each path and method
- All request/response content-type combinations (json/xml)
- Valid and invalid payloads

Run tests:
```bash
npx playwright test

npx allure generate ./allure-results --clean -o ./allure-report
npx allure open ./allure-report


"""






        self.output_path.write_text(READMEcontent, encoding="utf-8")
        print(f"✅ README.md generated at {self.output_path}")
