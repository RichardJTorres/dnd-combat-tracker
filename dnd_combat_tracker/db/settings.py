"""Key/value settings table CRUD."""

from typing import Optional

from sqlmodel import Session, select

from dnd_combat_tracker.db.models import AppSetting

DEFAULTS = {
    "provider": "claude",
    "claude_model": "claude-sonnet-4-6",
    "gemini_model": "gemini-2.5-flash",
    "openai_model": "gpt-4o",
    "ollama_model": "llama3.1",
}


def get(session: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    row = session.exec(select(AppSetting).where(AppSetting.key == key)).first()
    if row:
        return row.value
    return default if default is not None else DEFAULTS.get(key)


def set(session: Session, key: str, value: str) -> None:
    row = session.exec(select(AppSetting).where(AppSetting.key == key)).first()
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value)
    session.add(row)
    session.commit()
