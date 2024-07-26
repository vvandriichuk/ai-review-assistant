from pathlib import Path

from setuptools import find_packages, setup

# Read the content of README.md
with Path("README.md").open("r", encoding="utf-8") as f:
    long_description = f.read()

# Read the content of CHANGELOG.md
try:
    with Path("CHANGELOG.md").open("r", encoding="utf-8") as f:
        long_description += "\n\n" + f.read()
except FileNotFoundError:
    print(
        "WARNING: CHANGELOG.md not found. Consider creating one for better package documentation.",
    )

setup(
    name="ai_review_assistant",
    use_scm_version={
        "version_scheme": "no-guess-dev",
        "local_scheme": "no-local-version",
    },
    setup_requires=["setuptools_scm"],
    packages=find_packages(),
    install_requires=[
        "gitpython>=3.1.43",
        "langchain>=0.2.11",
        "langchain-core>=0.2.23",
        "langchain-openai>=0.1.17",
        "langchain-anthropic>=0.1.20",
        "click>=8.1.7",
        "openai>=1.37.0",
        "anthropic>=0.31.2",
        "importlib-metadata;python_version<'3.8'",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pylint>=2.15.0",
            "black>=22.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai_review_assistant=ai_review_assistant.main:cli",
            "install-ai-review-hook=ai_review_assistant.hooks.pre_commit:install_pre_commit_hook",
        ],
    },
    include_package_data=True,
    python_requires=">=3.11",
    author="Viktor Andriichuk",
    author_email="v.andriichuk@gmail.com",
    description="An AI-powered code review assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vandriichuk/ai_review_assistant",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
    package_data={
        "": ["CHANGELOG.md"],
    },
)
