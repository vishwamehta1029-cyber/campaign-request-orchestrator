import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    notion_api_key: str = os.getenv("NOTION_API_KEY", "").strip()
    notion_parent_page_id: str = os.getenv("NOTION_PARENT_PAGE_ID", "").strip()
    notion_tasks_database_id: str = os.getenv("NOTION_TASKS_DATABASE_ID", "").strip()

    cors_origin: str = os.getenv("CORS_ORIGIN", "http://localhost:5173").strip()

    # Safety valves for running with a real OPENAI_API_KEY on a publicly
    # reachable deployment — every request costs real money, so a public
    # demo needs hard caps rather than trusting visitors to be nice.
    max_requests_per_ip_per_hour: int = int(os.getenv("MAX_REQUESTS_PER_IP_PER_HOUR", "5"))
    max_live_requests_per_day: int = int(os.getenv("MAX_LIVE_REQUESTS_PER_DAY", "40"))
    max_request_text_chars: int = int(os.getenv("MAX_REQUEST_TEXT_CHARS", "500"))

    @property
    def agent_live(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def notion_live(self) -> bool:
        return bool(self.notion_api_key and self.notion_parent_page_id and self.notion_tasks_database_id)

    @property
    def cors_origins(self) -> list[str]:
        origins = {o.strip() for o in self.cors_origin.split(",") if o.strip()}
        origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
        return list(origins)


settings = Settings()
