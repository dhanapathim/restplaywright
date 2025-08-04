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

    def initiate_project_setup(self, tests_dir: Path) -> bool:
        if self.is_playwright_project(tests_dir):
            print("ℹ️ Playwright already configured here.")
            return False

        commands = [
            "npm init playwright@latest -- --lang=js --quiet --install-deps",
            "npm i -D allure-playwright dotenv"
        ]

        for cmd in commands:
            self.run_command(cmd, str(tests_dir))

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
