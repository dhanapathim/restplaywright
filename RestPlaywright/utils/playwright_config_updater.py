import os
import json
import re
import yaml


class PlaywrightConfigUpdater:
    def __init__(self, swagger_path, project_path):
        self.swagger_path = swagger_path
        self.project_path = project_path
        self.config_path = os.path.join(project_path, 'playwright/playwright.config.js')

    def run(self):
        self._validate_paths()
        swagger = self._load_swagger()
        base_url = self._extract_base_url(swagger)
        print(f"🔍 Extracted baseURL: {base_url}")
        self._update_config_file(base_url)

    def _validate_paths(self):
        if not os.path.isfile(self.swagger_path):
            print(f"❌ Swagger file not found at: {self.swagger_path}")
            exit(1)

        if not os.path.isfile(self.config_path):
            print(f"❌ playwright.config.js not found at: {self.config_path}")
            exit(1)

    def _load_swagger(self):
        ext = os.path.splitext(self.swagger_path)[1].lower()
        with open(self.swagger_path, 'r') as f:
            if ext == '.json':
                return json.load(f)
            elif ext in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                print("❌ Swagger file must be .json or .yaml/.yml")
                exit(1)

    def _extract_base_url(self, swagger):
        try:
            return swagger['servers'][0]['url']
        except (KeyError, IndexError):
            print("❌ Swagger missing servers[0].url")
            exit(1)

    def _update_config_file(self, base_url):
        with open(self.config_path, 'r') as f:
            content = f.read()

        # Step 1: Remove the entire projects block
        content = re.sub(
            r'projects:\s*\[(?:[^][]|\[(?:[^][]|\[[^\]]*\])*\])*\],?\s*',
            '',
            content,
            flags=re.DOTALL
        )

        # Step 2: Update the use block
        def update_use_block(match):
            block = match.group(1)

            # Remove old or commented baseURL
            block = re.sub(r'(//\s*)?baseURL:\s*[\'"].*?[\'"],?\n?', '', block)

            # Add new baseURL
            updated = f"    baseURL: '{base_url}',\n{block}"
            return f"use: {{\n{updated}  }}"

        content = re.sub(r'use:\s*{([^}]+)}', update_use_block, content, flags=re.DOTALL)

        # Write updated content
        with open(self.config_path, 'w') as f:
            f.write(content)

        print(f"✅ playwright.config.js updated successfully.")


