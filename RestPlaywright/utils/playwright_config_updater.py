import os
import json
import re
import yaml


class PlaywrightConfigUpdater:
    def __init__(self, swagger_path, project_path):
        self.swagger_path = swagger_path
        self.project_path = project_path
        self.config_path = os.path.join(project_path, 'playwright.config.js')

    # ---------- Public API ----------
    def run(self):
        self._validate_paths()
        swagger = self._load_swagger()
        base_url = self._extract_base_url(swagger)

        print(f"🔍 Extracted baseURL: {base_url}")
        config_content = self._read_file(self.config_path)

        config_content = self._ensure_auth_block(config_content)
        config_content = self._remove_projects_block(config_content)
        config_content = self._update_use_block(config_content, base_url)
        config_content = self._ensure_global_setup(config_content)
        config_content = self._update_reporter_block(config_content)

        self._write_file(self.config_path, config_content)
        print("✅ playwright.config.js updated successfully.")

    # ---------- Core Logic ----------
    def _ensure_auth_block(self, content):
        """Insert extraHTTPHeaders block if missing."""
        if "const authPath" in content:
            return content

        auth_block = (
            "import fs from 'fs';\n\n"
            "const authPath = 'auth.json';\n"
            "let extraHTTPHeaders;\n\n"
            "if (fs.existsSync(authPath)) {\n"
            "  const authData = JSON.parse(fs.readFileSync(authPath, 'utf-8'));\n"
            "  extraHTTPHeaders = authData.headers || {};\n"
            "}\n\n"
        )
        return re.sub(r"(import .*?;\n)", r"\1" + auth_block, content, 1)

    def _remove_projects_block(self, content):
        """Remove any existing projects[] block."""
        return re.sub(
            r'projects:\s*\[(?:[^][]|\[(?:[^][]|\[[^\]]*\])*\])*\],?\s*',
            '',
            content,
            flags=re.DOTALL
        )

    def _update_use_block(self, content, base_url):
        """Update or insert baseURL and extraHTTPHeaders in the 'use' block."""
        def replacer(match):
            block = match.group(1)
            block = re.sub(r'(//\s*)?baseURL:\s*[\'"].*?[\'"],?\n?', '', block)

            if "extraHTTPHeaders" not in block:
                block += "  extraHTTPHeaders,\n"

            return f"use: {{\n  baseURL: '{base_url}',\n{block}  }}"

        return re.sub(r'use:\s*{([^}]+)}', replacer, content, flags=re.DOTALL)

    def _ensure_global_setup(self, content):
        """Ensure globalSetup is present."""
        if "globalSetup:" in content:
            return content

        pattern = r"(defineConfig\(\s*\{\s*)"
        if re.search(pattern, content):
            return re.sub(pattern, r"\1globalSetup: './global-setup.js',\n  ", content)

        return re.sub(r"(\}\);?\s*)$", r"  globalSetup: './global-setup.js',\n\1", content)

    def _update_reporter_block(self, content):
        """Ensure reporter includes [ ['allure-playwright'] ] — add if missing."""
        # If reporter already configured with allure-playwright, do nothing
        if re.search(r"allure-playwright", content):
            return content

        if "reporter:" in content:
            # Reporter exists but without allure — replace with allure only
            return re.sub(
                #r"reporter:\s*\[[^\]]*\],?",
                   r"reporter:\s*[^,}]+,?",
                "reporter: [['list'], ['allure-playwright'],['html'] ],\n",
                content,
                flags=re.DOTALL
            )
        else:
            # No reporter block at all — insert one
            pattern = r"(defineConfig\(\s*\{\s*)"
            if re.search(pattern, content):
                return re.sub(
                    pattern,
                    r"\1reporter: [[list], ['allure-playwright'],['html'] ],\n  ",
                    content
                )
        return content
    # ---------- Helpers ----------
    def _validate_paths(self):
        if not os.path.isfile(self.swagger_path):
            raise FileNotFoundError(f"Swagger file not found: {self.swagger_path}")
        if not os.path.isfile(self.config_path):
            raise FileNotFoundError(f"playwright.config.js not found: {self.config_path}")

    def _load_swagger(self):
        ext = os.path.splitext(self.swagger_path)[1].lower()
        with open(self.swagger_path, 'r') as f:
            if ext == '.json':
                return json.load(f)
            elif ext in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                raise ValueError("Swagger file must be .json or .yaml/.yml")

    def _extract_base_url(self, swagger):
        try:
            return swagger['servers'][0]['url']
        except (KeyError, IndexError):
            raise ValueError("Swagger missing servers[0].url")

    def _read_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _write_file(self, path, content):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)