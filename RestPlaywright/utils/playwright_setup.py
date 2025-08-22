import os
import shutil
import sys
import subprocess
from pathlib import Path

class PlaywrightProjectManager:
    def __init__(self, target_folder: str):
        self.base_path = Path(target_folder).resolve()
        print(f"📁 Target folder: {self.base_path}")

    def run_command(self, command, cwd):
        try:
            print(f"▶️ Running: {command}")
            subprocess.run(command, cwd=cwd, check=True, shell=True)
        except FileNotFoundError:
            print(f"❌ Command not found: {command.split()[0]}. Ensure it's installed and in your PATH.")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed with exit code {e.returncode}: {command}")
            sys.exit(1)

    def is_playwright_project(self, folder: Path) -> bool:
        return any([
            (folder / "playwright.config.js").exists(),
            (folder / "playwright.config.mjs").exists(),
            (folder / "tests").is_dir()
        ])

    def find_any_playwright_project(self, base_path: Path) -> bool:
        for subdir in base_path.rglob("*"):
            if subdir.is_dir() and self.is_playwright_project(subdir):
                print(f"✅ Playwright project found at: {subdir}")
                return True
        return False

    def clean_playwright_project(self,project_dir: str):
        """
        Cleans the Playwright project directory by deleting unnecessary files and folders.
        """
        project_path = Path(project_dir).resolve()



        #  Delete the 'tests-examples' folder if it exists
        examples_path = project_path / "tests-examples"
        if examples_path.exists() and examples_path.is_dir():
            shutil.rmtree(examples_path)
            print(f"🗑️ Deleted folder: {examples_path}")
        else:
            print(f"✅ Folder not found or already removed: {examples_path}")

        #  Delete all files in the 'tests' folder
        tests_path = project_path / "tests"
        if tests_path.exists() and tests_path.is_dir():
            for file in tests_path.iterdir():
                file.unlink()
                print(f"🗑️ Deleted file: {file}")
        else:
            print(f"⚠️ 'tests' directory not found at: {tests_path}")

    def initiate_project_setup(self, tests_dir: Path) -> bool:
        if self.is_playwright_project(tests_dir):
            print("ℹ️ Playwright already configured here.")
            return False

        commands = [
            "npm init playwright@latest -- --yes --lang=js --quiet --install-deps",
            "npm i -D allure-playwright dotenv"
        ]

        for cmd in commands:
            self.run_command(cmd, str(tests_dir))

            self.clean_playwright_project(tests_dir)
            self.create_workflow_yml_file(tests_dir)
            self.create_api_fixtures_file(tests_dir)
        print("✅ Playwright setup complete.")
        return True

    def setup(self):
        if not self.base_path.exists():
            print(f"📁 Creating base folder: {self.base_path}")
            self.base_path.mkdir(parents=True)

        if self.find_any_playwright_project(self.base_path):
            print("✅ Skipping setup — Playwright project already exists.")
            return

        new_proj_path = self.base_path / "playwright"
        new_proj_path.mkdir(parents=True, exist_ok=True)
        print(f"📦 Creating new Playwright project in: {new_proj_path}")
        self.initiate_project_setup(new_proj_path)

    def create_workflow_yml_file(self, project_dir: Path):
        # Define the YAML content
        yaml_content = """\
           name: Playwright Tests

           on:
             push:
               branches: [ master, main ]
             workflow_dispatch:

           jobs:
             test:
               runs-on: ubuntu-latest

               steps:
                 - name: Checkout repository
                   uses: actions/checkout@v4

                 - name: Setup Node.js
                   uses: actions/setup-node@v4
                   with:
                     node-version: '20'

                 - name: Install dependencies
                   run: npm install

                 - name: Install Playwright browsers
                   run: npx playwright install --with-deps

                 - name: Run Playwright tests
                   run: npx playwright test
                   continue-on-error: true
                 - name: 🧰 Install Allure CLI
                   run: |
                     wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.tgz
                     tar -xvzf allure-2.27.0.tgz
                     sudo mv allure-2.27.0 /opt/allure
                     sudo ln -s /opt/allure/bin/allure /usr/bin/allure
                     allure --version
                 - name: 🧾 Generate Allure report
                   run: |
                     allure generate allure-results --clean -o allure-report   
                 - name: 📤 Upload Allure report artifact
                   uses: actions/upload-artifact@v4
                   with:
                     name: allure-report
                     path: allure-report
           """

        # Define the file path
        folder_path = project_dir / ".github/workflows"
        file_path = os.path.join(folder_path, "playwright.yml")

        # Create the folder structure if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)

        # Write the YAML content to the file
        with open(file_path, "w") as f:
            f.write(yaml_content)

        print(f"Workflow file created at: {file_path}")

    def create_api_fixtures_file(self, project_dir: Path):
        # Define the YAML content
        yaml_content = """\
import { test as base } from '@playwright/test';
import * as testInfo from "allure-js-commons";
 
export const test = base.extend({
  request: async ({ request }, use) => {
    const wrapped = new Proxy(request, {
      get(target, prop) {
        if (typeof target[prop] === 'function') {
          return async (...args) => {
            // ---- Before API Call ----
            await test.step(`API Request: ${prop.toString().toUpperCase()} ${args[0]}`, async () => {
              await testInfo.attachment(
                'Request Details',
                JSON.stringify(
                  {
                    method: prop.toString().toUpperCase(),
                    url: args[0],
                    options: args[1] || {}
                  },
                  null,
                  2
                ),
                'application/json'
              );
            });
 
            const response = await target[prop](...args);
 
            let respBody;
            try {
              respBody = await response.json();
            } catch {
              respBody = await response.text();
            }
 
            const respHeaders = response.headers();
 
            await test.step(`API Response: ${response.status()} ${args[0]}`, async () => {
              await testInfo.attachment(
                'Response Details',
                JSON.stringify(
                  {
                    status: response.status(),
                    headers: respHeaders,
                    cookies: respHeaders['set-cookie'] || 'No cookies',
                    contentType: respHeaders['content-type'] || 'N/A',
                    body: respBody
                  },
                  null,
                  2
                ),
                'application/json'
              );
            });
 
            return response;
          };
        }
        return target[prop];
      }
    });
 
    await use(wrapped);
  }
});
           """

        # Define the file path
        folder_path = project_dir / "fixtures"
        file_path = os.path.join(folder_path, "apiWithAllure.js")

        # Create the folder structure if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)

        # Write the YAML content to the file
        with open(file_path, "w") as f:
            f.write(yaml_content)

        print(f"fixtures file created at: {file_path}")