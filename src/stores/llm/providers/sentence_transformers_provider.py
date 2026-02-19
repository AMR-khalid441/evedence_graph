import logging
from typing import Optional

from sentence_transformers import SentenceTransformer

from ..llm_interface import LLMInterface
from .openai_provider import OpenAIProvider


class SentenceTransformersProvider(LLMInterface):
    """
    Provider that uses SentenceTransformers (e.g. neuml/pubmedbert-base-embeddings)
    for embeddings and delegates text generation to OpenAI.
    """

    def __init__(
        self,
        openai_api_key: str,
        openai_api_url: Optional[str] = None,
        default_input_max_characters: int = 1000,
        default_generation_max_output_tokens: int = 1000,
        default_generation_temperature: float = 0.1,
    ):
        self._openai = OpenAIProvider(
            api_key=openai_api_key,
            api_url=openai_api_url,
            default_input_max_characters=default_input_max_characters,
            default_generation_max_output_tokens=default_generation_max_output_tokens,
            default_generation_temperature=default_generation_temperature,
        )
        self._embedding_model: Optional[SentenceTransformer] = None
        self._embedding_size: Optional[int] = None
        self.logger = logging.getLogger(__name__)

    @property
    def default_input_max_characters(self) -> int:
        return self._openai.default_input_max_characters

    @default_input_max_characters.setter
    def default_input_max_characters(self, value: int) -> None:
        self._openai.default_input_max_characters = value

    def set_generation_model(self, model_id: str) -> None:
        self._openai.set_generation_model(model_id)

    def set_embedding_model(self, model_id: str, embedding_size: int) -> None:
        self._embedding_model = SentenceTransformer(model_id)
        self._embedding_size = 768  # PubMedBERT and similar models use 768

    def embed_text(self, text: str, document_type: str = None):
        if self._embedding_model is None:
            self.logger.error("Embedding model was not set")
            return None
        if not text or not str(text).strip():
            self.logger.error("Cannot embed empty text")
            return None
        try:
            embedding = self._embedding_model.encode(
                text, truncate=True, max_length=512, convert_to_numpy=True
            )
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error while embedding text: {e}")
            return None

    def generate_text(
        self,
        prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None,
        temperature: float = None,
        max_input_characters: int = None,
    ):
        return self._openai.generate_text(
            prompt=prompt,
            chat_history=chat_history,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            max_input_characters=max_input_characters,
        )

    def construct_prompt(
        self, prompt: str, role: str, max_input_characters: int = None
    ):
        return self._openai.construct_prompt(
            prompt=prompt, role=role, max_input_characters=max_input_characters
        )
