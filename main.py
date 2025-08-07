from utils.llm_processor import LLMProcessor
from utils.playwright_setup import  PlaywrightProjectManager
from utils.swagger import OpenAPISpecValidator
import os
from dotenv import load_dotenv

from utils.swagger_extractor import PathMethodExtractor


def main():

    load_dotenv()
    language = os.getenv("TARGET_LANGUAGE")
    swagger_file = os.getenv("SWAGGER_FILE_PATH")
    target_folder = os.getenv("TARGET_FOLDER")

    if not swagger_file or not target_folder:
        print("❌ Please set SWAGGER_FILE_PATH and TARGET_FOLDER in .env")
        return

    validator = OpenAPISpecValidator(swagger_file)
    validator.run_validation()
    projectmanager = PlaywrightProjectManager(target_folder)
    projectmanager.setup()
    extractor = PathMethodExtractor(swagger_file)
    extracted_dir=extractor.extract_paths_and_methods()

    # Step 2: Run LLM over extracted specs
    llm = LLMProcessor(target_folder,extracted_dir,language)
    llm.run()



if __name__ == "__main__":
     main()