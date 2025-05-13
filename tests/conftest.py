import shutil
import os
import pytest

@pytest.fixture(scope="function", autouse=True)
def clean_folder():
    folder_path = "build"

    # Pre-test: delete folder if it exists
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    yield

    # Post-test: delete folder again
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)