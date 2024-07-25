import os

def install_pre_commit_hook():
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

    hooks_dir = os.path.join(os.getcwd(), '.git', 'hooks')
    pre_commit_path = os.path.join(hooks_dir, 'pre-commit')

    if not os.path.exists(hooks_dir):
        os.makedirs(hooks_dir)

    with open(pre_commit_path, 'w') as f:
        f.write(hook_script)

    os.chmod(pre_commit_path, 0o755)
    print(f"Pre-commit hook installed at {pre_commit_path}")