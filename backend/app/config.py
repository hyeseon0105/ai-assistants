import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class Settings:
    """환경 설정 및 OpenAI 클라이언트 래퍼."""

    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    _client: OpenAI | None = None

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

        if not api_key:
            raise ValueError("OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")

        self.OPENAI_API_KEY = api_key
        self.OPENAI_MODEL = model

    @property
    def client(self) -> OpenAI:
        """OpenAI 클라이언트를 지연 초기화하여 반환."""
        if self._client is None:
            self._client = OpenAI(api_key=self.OPENAI_API_KEY)
        return self._client


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """애플리케이션 전역에서 재사용할 Settings 인스턴스."""
    return Settings()


settings = get_settings()


