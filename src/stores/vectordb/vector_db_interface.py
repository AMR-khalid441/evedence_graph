from abc import ABC, abstractmethod
from typing import List

class VectorDBInterface(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def is_collection_existed(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    def list_all_collections(self) -> List:
        pass

    @abstractmethod
    def get_collection_info(self, collection_name: str) -> dict:
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        pass

    @abstractmethod
    def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, 
                         record_id: str = None):
        pass

    @abstractmethod
    def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        pass

    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list, limit: int):
        pass

    # Async methods (optional - for async implementations)
    async def connect_async(self):
        """Async connection. Default implementation raises NotImplementedError."""
        raise NotImplementedError("Async connection not implemented")

    async def disconnect_async(self):
        """Async disconnection. Default implementation raises NotImplementedError."""
        raise NotImplementedError("Async disconnection not implemented")

    async def is_collection_existed_async(self, collection_name: str) -> bool:
        """Async collection existence check. Default implementation raises NotImplementedError."""
        raise NotImplementedError("Async collection existence check not implemented")

    async def create_collection_async(self, collection_name: str, 
                                      embedding_size: int,
                                      do_reset: bool = False):
        """Async collection creation. Default implementation raises NotImplementedError."""
        raise NotImplementedError("Async collection creation not implemented")

    async def insert_one_async(self, collection_name: str, text: str, vector: list,
                               metadata: dict = None, 
                               record_id: str = None):
        """Async single insert. Default implementation raises NotImplementedError."""
        raise NotImplementedError("Async single insert not implemented")

    async def insert_many_async(self, collection_name: str, texts: list, 
                                vectors: list, metadata: list = None, 
                                record_ids: list = None, batch_size: int = 50):
        """Async batch insert. Default implementation raises NotImplementedError."""
        raise NotImplementedError("Async batch insert not implemented")
