from pathlib import Path

# Skill root: 4 levels up from this file
# this file: src/subagent/system_designer_beta/config.py
SKILL_ROOT = Path(__file__).parent.parent.parent.parent.resolve()

PROMPTS_DIR = SKILL_ROOT / "prompts"
DATA_DIR = SKILL_ROOT / "data"
DOCS_DIR = SKILL_ROOT / "docs"
