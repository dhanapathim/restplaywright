from RestPlaywright.utils.latest_swagger_file import get_latest_swagger_file
from RestPlaywright.utils.llm_processor import LLMProcessor, GlobalSetup
from RestPlaywright.utils.playwright_config_updater import PlaywrightConfigUpdater
from RestPlaywright.utils.playwright_setup import  PlaywrightProjectManager
from RestPlaywright.utils.swagger import OpenAPISpecValidator
import os
from dotenv import load_dotenv

from RestPlaywright.utils.swagger_extractor import PathMethodExtractor


def main():

    global extracted_dir
    load_dotenv()
    language = os.getenv("TARGET_LANGUAGE")
    swagger_folder = os.getenv("SWAGGER_FILE_PATH")
    target_folder = os.getenv("TARGET_FOLDER")

    if not swagger_folder or not target_folder:
        print("❌ Please set SWAGGER_FILE_PATH and TARGET_FOLDER in .env")
        return
    swagger_file, result = get_latest_swagger_file(swagger_folder)
    validator = OpenAPISpecValidator(swagger_file)
    validator.run_validation()
    projectmanager = PlaywrightProjectManager(target_folder)
    new_setup=projectmanager.setup()
    updater = PlaywrightConfigUpdater(swagger_file, target_folder)
    updater.run()
    extractor = PathMethodExtractor(swagger_file)
    if result is None or new_setup:
        extracted_dir = extractor.extract_paths_and_methods()
    else:
        if result["added"] is not None or result["updated"] is not None:
            if new_setup:
                extracted_dir = extractor.extract_paths_and_methods()
            else:
                extracted_dir = extractor.get_update_add_paths_and_methods(result["added"], result["updated"])

    # Step 2: Run LLM over extracted specs
    if extracted_dir is not None:
        llm = GlobalSetup(target_folder, swagger_file)
        llm.genarateglobalsetup()
        llm = LLMProcessor(target_folder,extracted_dir,language)
        llm.run()
    if result is not None and result["deleted"] is not None:
        extractor.remove_files(result["deleted"], target_folder)


if __name__ == "__main__":
     main()