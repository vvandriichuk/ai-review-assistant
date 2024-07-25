from pathlib import Path
from typing import NoReturn


def install_pre_commit_hook() -> NoReturn:
    """Install the pre-commit hook for AI code review."""
    hook_script = """#!/bin/sh
    # Check if skipping AI review is required
    if git rev-parse --abbrev-ref HEAD | grep -q 'ignore-ai-reviewer'; then
        exit 0
    fi

    # Run the Python script for analysis
    ai_review_assistant review

    # Check the script execution status
    if [ $? -ne 0 ]; then
      echo "Code review failed. Please fix the issues before committing."
      exit 1
    fi

    exit 0
    """

    hooks_dir = Path.cwd() / ".git" / "hooks"
    pre_commit_path = hooks_dir / "pre-commit"

    hooks_dir.mkdir(parents=True, exist_ok=True)

    pre_commit_path.write_text(hook_script)

    pre_commit_path.chmod(0o755)
    print(f"Pre-commit hook installed at {pre_commit_path}")
    raise SystemExit
