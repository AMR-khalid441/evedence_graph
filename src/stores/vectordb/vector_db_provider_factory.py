from src.controllers.base_controller import BaseController

from .providers import QdrantDBProvider
from .vector_db_enums import VectorDBEnums


class VectorDBProviderFactory:
    def __init__(self, config):
        self.config = config
        self.base_controller = BaseController()

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            url = (getattr(self.config, 'QDRANT_CLUSTER_URL', None) or '').strip()
            api_key = (getattr(self.config, 'QDRANT_KEY', None) or '').strip()
            if not url or not api_key:
                raise ValueError(
                    "Qdrant Cloud is required. Set QDRANT_CLUSTER_URL and QDRANT_KEY in your .env file."
                )
            db_path = self.base_controller.get_database_path(db_name=self.config.VECTOR_DB_PATH)
            return QdrantDBProvider(
                db_path=db_path,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                url=url,
                api_key=api_key,
            )
        return None
