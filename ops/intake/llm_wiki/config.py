from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_root: Path = Path(os.getenv("LLM_WIKI_ROOT", "/workspace/llm-wiki"))
    shared_token: str = os.getenv("INTAKE_SHARED_TOKEN", "")
    base_url: str = os.getenv("INTAKE_BASE_URL", "").rstrip("/")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_webhook_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    telegram_allowed_chat_ids_raw: str = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    query_poll_seconds: int = int(os.getenv("QUERY_POLL_SECONDS", "5"))
    maintainer_interval_seconds: int = int(os.getenv("MAINTAINER_INTERVAL_SECONDS", "300"))
    auto_ingest_enabled: bool = os.getenv("AUTO_INGEST_ENABLED", "true").lower() == "true"
    auto_lint_enabled: bool = os.getenv("AUTO_LINT_ENABLED", "true").lower() == "true"
    lint_interval_seconds: int = int(os.getenv("LINT_INTERVAL_SECONDS", "900"))
    lint_batch_size: int = int(os.getenv("LINT_BATCH_SIZE", "12"))
    lint_batches_per_interval: int = int(os.getenv("LINT_BATCHES_PER_INTERVAL", "3"))
    auto_commit_enabled: bool = os.getenv("AUTO_COMMIT_ENABLED", "false").lower() == "true"
    openclaw_query_command: str = os.getenv("OPENCLAW_QUERY_COMMAND", "python3 ops/openclaw/run_query_job.py").strip()
    openclaw_ingest_command: str = os.getenv("OPENCLAW_INGEST_COMMAND", "python3 ops/openclaw/run_ingest_job.py").strip()
    openclaw_lint_command: str = os.getenv("OPENCLAW_LINT_COMMAND", "python3 ops/openclaw/run_lint_job.py").strip()

    @property
    def raw_dir(self) -> Path:
        return self.app_root / "raw"

    @property
    def inbox_dir(self) -> Path:
        return self.raw_dir / "inbox"

    @property
    def imports_dir(self) -> Path:
        return self.raw_dir / "imports"

    @property
    def processed_dir(self) -> Path:
        return self.imports_dir / "processed"

    @property
    def rejected_dir(self) -> Path:
        return self.imports_dir / "rejected"

    @property
    def sources_dir(self) -> Path:
        return self.raw_dir / "sources"

    @property
    def assets_dir(self) -> Path:
        return self.raw_dir / "assets"

    @property
    def wiki_dir(self) -> Path:
        return self.app_root / "wiki"

    @property
    def wiki_sources_dir(self) -> Path:
        return self.wiki_dir / "sources"

    @property
    def wiki_entities_dir(self) -> Path:
        return self.wiki_dir / "entities"

    @property
    def wiki_concepts_dir(self) -> Path:
        return self.wiki_dir / "concepts"

    @property
    def wiki_projects_dir(self) -> Path:
        return self.wiki_dir / "projects"

    @property
    def wiki_repositories_dir(self) -> Path:
        return self.wiki_dir / "repositories"

    @property
    def wiki_answers_dir(self) -> Path:
        return self.wiki_dir / "answers"

    @property
    def wiki_recipes_dir(self) -> Path:
        return self.wiki_dir / "recipes"

    @property
    def wiki_syntheses_dir(self) -> Path:
        return self.wiki_dir / "syntheses"

    @property
    def wiki_templates_dir(self) -> Path:
        return self.wiki_dir / "templates"

    @property
    def state_dir(self) -> Path:
        return self.app_root / "ops" / "state"

    @property
    def query_pending_dir(self) -> Path:
        return self.state_dir / "queries" / "pending"

    @property
    def query_running_dir(self) -> Path:
        return self.state_dir / "queries" / "running"

    @property
    def query_done_dir(self) -> Path:
        return self.state_dir / "queries" / "done"

    @property
    def query_failed_dir(self) -> Path:
        return self.state_dir / "queries" / "failed"

    @property
    def ingest_pending_dir(self) -> Path:
        return self.state_dir / "ingest" / "pending"

    @property
    def ingest_running_dir(self) -> Path:
        return self.state_dir / "ingest" / "running"

    @property
    def ingest_done_dir(self) -> Path:
        return self.state_dir / "ingest" / "done"

    @property
    def ingest_failed_dir(self) -> Path:
        return self.state_dir / "ingest" / "failed"

    @property
    def lint_pending_dir(self) -> Path:
        return self.state_dir / "lint" / "pending"

    @property
    def lint_running_dir(self) -> Path:
        return self.state_dir / "lint" / "running"

    @property
    def lint_done_dir(self) -> Path:
        return self.state_dir / "lint" / "done"

    @property
    def lint_failed_dir(self) -> Path:
        return self.state_dir / "lint" / "failed"

    @property
    def telegram_last_answer_dir(self) -> Path:
        return self.state_dir / "telegram" / "last-answer"

    @property
    def scheduler_dir(self) -> Path:
        return self.state_dir / "scheduler"

    @property
    def lint_scheduler_state_file(self) -> Path:
        return self.scheduler_dir / "lint-scheduler.json"

    @property
    def allowed_chat_ids(self) -> set[str]:
        return {item.strip() for item in self.telegram_allowed_chat_ids_raw.split(",") if item.strip()}
