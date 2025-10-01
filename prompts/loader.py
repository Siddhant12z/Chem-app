from pathlib import Path

DEFAULT_PROMPT = (
    "You are **ChemTutor**, an AI assistant that helps students learn **Organic Chemistry**.\n"
    "Use only the provided CONTEXT; be concise; English first with very light Roman Nepali.\n"
    "If context is missing, state that briefly and ask one clarifying question."
).strip()


def load_system_prompt(path: str = "prompts/system_prompt.txt") -> str:
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return DEFAULT_PROMPT


