from setuptools import setup, find_packages

setup(
    name='ai_review_assistant',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'gitpython',
        'langchain',
        'click',
    ],
    entry_points={
        'console_scripts': [
            'ai_review_assistant=ai_review_assistant.main:cli',
            'install-ai-review-hook=ai_review_assistant.hooks.pre_commit:install_pre_commit_hook',
        ],
    },
    include_package_data=True,
)