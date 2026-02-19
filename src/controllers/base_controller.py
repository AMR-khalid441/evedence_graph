from src.helpers.config import get_settings, Settings
import os
import random
import string
from pathlib import Path

class BaseController:
    
    def __init__(self):

        self.app_settings = get_settings()
        
        self.base_dir = os.path.dirname( os.path.dirname(__file__) )
        self.files_dir = os.path.join(
            self.base_dir,
            "assets/files"
        )

    def get_database_path(self, db_name: str) -> str:
        """Return the absolute path for a database directory (e.g. vector DB storage).
        Resolves to a folder under the project root (parent of src/)."""
        return str(Path(self.base_dir).parent / db_name)
        
    def generate_random_string(self, length: int=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
