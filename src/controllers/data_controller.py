import re
from pathlib import Path

from fastapi import UploadFile
from src.models import ResponseSignal

from .base_controller import BaseController
from .project_controller import ProjectController


class DataController(BaseController):

    def __init__(self):
        super().__init__()
        self.size_scale = 1048576  # convert MB to bytes

    def validate_uploaded_file(self, file: UploadFile):
        ext = file.filename.split(".")[-1].lower().strip()
        allowed = [x.lower().strip() for x in self.app_settings.FILE_ALLOWED_TYPES]

        if ext not in allowed:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value

    def generate_unique_filepath(self, orig_file_name: str, project_id: str):
        random_key = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)
        cleaned_file_name = self.get_clean_file_name(orig_file_name=orig_file_name)
        base_path = Path(project_path)
        new_file_path = base_path / (random_key + "_" + cleaned_file_name)

        while new_file_path.exists():
            random_key = self.generate_random_string()
            new_file_path = base_path / (random_key + "_" + cleaned_file_name)

        return str(new_file_path), random_key + "_" + cleaned_file_name

    def get_clean_file_name(self, orig_file_name: str):

        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name
