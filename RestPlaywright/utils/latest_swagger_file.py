import os
import glob
import yaml
import re
from deepdiff import DeepDiff
from datetime import datetime


def load_swagger(file_path):
    """
       Loads a Swagger (OpenAPI) file from the given path and parses its YAML content.

       Args:
           file_path (str): Path to the Swagger file.

       Returns:
           dict: Parsed Swagger file as a Python dictionary.
       """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def get_two_latest_files(folder, prefix='Swagger'):
    """
        Finds the two most recent Swagger files in the specified folder based on a date pattern in the filename.

        Args:
            folder (str): Directory to search for Swagger files.
            prefix (str, optional): Filename prefix to match. Defaults to 'Swagger'.

        Returns:
            tuple: Paths to the two latest Swagger files. If only one file is found, returns (file, None).
        """
    files = []
    valid_extensions = ['.json', '.yaml', '.yml']
    for ext in valid_extensions:
        # files = glob.glob(os.path.join(folder, f"{prefix}*{ext}"))
        files.extend(glob.glob(os.path.join(folder, f"{prefix}*{ext}")))
    if len(files) == 0: raise Exception("The folder is empty.")
    if len(files) == 1:
        print("Folder has one file.")
        return files[0], None
    # Extract date from filenames
    files_sorted = sorted(
        files,
        key=lambda x: datetime.strptime(
            re.search(r'(\d{8}_\d{6})', os.path.basename(x)).group(1),
            "%Y%m%d_%H%M%S"
        )
    )
    print(f"Found {len(files_sorted)} files.")
    return files_sorted[-2], files_sorted[-1]

def compare_swagger_paths(old_swagger, new_swagger):
    """
        Compares the 'paths' sections of two Swagger files to identify added, deleted, and updated API paths and methods.

        Args:
            old_swagger (dict): The older Swagger file as a dictionary.
            new_swagger (dict): The newer Swagger file as a dictionary.
        Returns:
            tuple: A tuple containing three lists:
                - added (list): List of newly added paths.
                - deleted (list): List of deleted paths and methods in the format 'path_method'.
                - updated (list): List of paths that have been updated.
        """
    old_paths = old_swagger.get("paths", {})
    new_paths = new_swagger.get("paths", {})

    old_set = set(old_paths.keys())
    new_set = set(new_paths.keys())

    added = new_set - old_set
    deleted_paths = old_set - new_set
    common = old_set & new_set

    updated = []
    deleted = []

    for path in common:
        old_details = old_paths[path]
        new_details = new_paths[path]
        diff = DeepDiff(old_details, new_details, ignore_order=True)
        if diff:
            updated.append(path)
        old_methods = old_paths[path]
        new_methods = new_paths[path]

        # Detect deleted methods
        deleted_methods = set(old_methods.keys()) - set(new_methods.keys())
        for method in deleted_methods:
            deleted.append(f"{path.strip('/').replace('/', '_')}_{method.upper()}")
        # Full path deletions

    for path in deleted_paths:
        for method in old_paths[path].keys():
            deleted.append(f"{path.strip('/').replace('/', '_')}_{method.upper()}")

    return {
        "added": list(added),
        "deleted": deleted,
        "updated": updated
    }


def get_latest_swagger_file(folder):
    """
    Compares the two latest Swagger files in the specified folder and identifies added, deleted, and updated API paths.
    :param folder: Directory containing Swagger files.
    :return: Tuple containing the latest Swagger file path and a dictionary with added, deleted, and updated paths.
    """
    old_file, new_file = get_two_latest_files(folder)
    if new_file is None: return old_file, None
    print(f"Comparing:\nOld: {old_file}\nNew: {new_file}\n")

    old_swagger = load_swagger(old_file)
    new_swagger = load_swagger(new_file)

    result = compare_swagger_paths(old_swagger, new_swagger)

    print("=== Added Paths ===")
    for path in result["added"]:
        print(path)

    print("\n=== Deleted Paths ===")
    for path in result["deleted"]:
        print(path)

    print("\n=== Updated Paths ===")
    for path in result["updated"]:
        print(path)
    return new_file, result
