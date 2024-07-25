from pathlib import Path

from setuptools import find_packages, setup

with Path("README.md").open("r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="ai_review_assistant",
    version="0.2",
    packages=find_packages(),
    install_requires=[
        "gitpython>=3.1.30",
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
        "langchain-openai>=0.0.2",
        "langchain-anthropic>=0.0.1",
        "click>=8.0.0",
        "openai>=1.0.0",
        "anthropic>=0.8.0",
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
    url="https://github.com/yourusername/ai_review_assistant",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
)
