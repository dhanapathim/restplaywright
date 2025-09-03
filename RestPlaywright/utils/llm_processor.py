import json
import os
import yaml
import jsonref
from pathlib import Path
from RestPlaywright.utils import llm
from langchain.schema import HumanMessage, SystemMessage, AIMessage

def to_langchain_messages(messages):
    """Convert OpenAI-style messages into LangChain messages"""
    converted = []
    for m in messages:
        if m["role"] == "system":
            converted.append(SystemMessage(content=m["content"]))
        elif m["role"] == "user":
            converted.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            converted.append(AIMessage(content=m["content"]))
    return converted


class LLMProcessor:
    def __init__(self, target_folder: str, input_dir: str, language: str, output_dir: str = None):
        self.playwright_dir = Path(target_folder)
        self.input_dir = Path(input_dir)
        print(self.playwright_dir)
        self.output_dir = Path(output_dir) if output_dir else self.playwright_dir / "tests"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = llm
        BASE_DIR = Path(__file__).resolve().parent
        # go up one level and then into prompts/
        PROMPT_PATH = BASE_DIR.parent / "prompts" / "prompt_codegen.txt"
        self.prompt_data = PROMPT_PATH.read_text(encoding="utf-8").strip()
        self.messages = [
            {
                "role": "system",
                "content": (self.prompt_data)
            }
        ]

    def to_plain_obj(self, obj):
        if isinstance(obj, dict):
            return {k: self.to_plain_obj(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.to_plain_obj(i) for i in obj]
        return obj

    def load_spec(self, file: Path):
        with open(file, "r", encoding="utf-8") as f:
            if file.suffix in [".yaml", ".yml", ".json"]:
                raw = yaml.safe_load(f)
            else:
                raw = json.load(f)

        if raw is None:
            raise ValueError(f"File {file.name} is empty or invalid.")
        resolved = jsonref.replace_refs(raw, merge_props=True)
        return self.to_plain_obj(resolved)

    def build_prompt(self, spec: dict, filename: str) -> str:
        # Only pass filename + spec as input
        return f"""
            OpenAPI file: **{filename}**

            Spec:
            {json.dumps(spec, indent=2)}

            Generate the Playwright .spec.js file.
            """

    def run(self):
        for file in self.input_dir.iterdir():
            if file.suffix.lower() not in [".json", ".yaml", ".yml"]:
                continue
            try:
                print(f"📄 Processing {file.name}")
                spec = self.load_spec(file)
                # prompt = self.build_prompt(spec, file.name)
                # Instead of building a long prompt, just attach spec + filename
                user_message = self.build_prompt(spec, file.name)
                self.messages.append({"role": "user", "content": user_message})

                # Convert to LangChain messages
                lc_messages = to_langchain_messages(self.messages)

                # Call your LangChain LLM
                response = llm.invoke(lc_messages)

                # Extract the content
                reply = response.content.strip()

                # Save assistant reply back to conversation
                self.messages.append({"role": "assistant", "content": reply})

                with open(self.output_dir / f"{file.stem}.spec.js", "w", encoding="utf-8") as f:
                    f.write(reply)
                clean_code_fences(self.output_dir)

                print(f"✅ Saved LLM response for {file.name}")

            except Exception as e:
                print(f"❌ Failed to process {file.name}: {e}")


class GlobalSetup:
    def __init__(self, target_folder: str, swagger_file: str, output_dir: str = None):
        self.playwright_dir = Path(target_folder)
        self.swagger_file = Path(swagger_file)
        self.output_dir = Path(output_dir) if output_dir else self.playwright_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = llm
        BASE_DIR = Path(__file__).resolve().parent
        # go up one level and then into prompts/
        PROMPT_PATH = BASE_DIR.parent / "prompts" / "prompt_globalsetup.txt"

        self.prompt_data = PROMPT_PATH.read_text(encoding="utf-8").strip()

        self.messages = [
            {
                "role": "system",
                "content": (self.prompt_data)
            }
        ]

    def load_spec(self):
        with open(self.swagger_file, "r", encoding="utf-8") as f:
            if self.swagger_file.suffix.lower() in [".yaml", ".yml"]:
                spec = yaml.safe_load(f)
                return yaml.dump(spec)
            elif self.swagger_file.suffix.lower() == ".json":
                spec = json.load(f)
                return json.dumps(spec, indent=2)
            else:
                raise ValueError("Unsupported Swagger file format.")

    def build_global_setup_prompt(self, spec: dict, filename: str) -> str:
        return f"""
        OpenAPI file: **{filename}**

        Spec:
        {json.dumps(spec, indent=2)}

        Generate the global setup .js file.
        """

    def genarateglobalsetup(self):
        spec = self.load_spec()

        user_message = self.build_global_setup_prompt(spec, self.swagger_file)

        self.messages.append({"role": "user", "content": user_message})
        lc_messages = to_langchain_messages(self.messages)

        # Call your LangChain LLM
        response = llm.invoke(lc_messages)

        # Extract the content
        reply = response.content.strip()

        with open(self.output_dir / "global-setup.js", "w", encoding="utf-8") as f:
            f.write(reply)
        clean_code_fences(self.output_dir)


def clean_code_fences(root_folder, extensions=[".js", ".ts", ]):
    for subdir, _, files in os.walk(root_folder):
        for filename in files:
            if any(filename.endswith(ext) for ext in extensions):
                file_path = os.path.join(subdir, filename)

                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                # Remove starting and ending Markdown code fences
                if lines and lines[0].strip() == "```javascript":
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]

                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

    print(f"✅ Cleaned all files in: {root_folder}")
