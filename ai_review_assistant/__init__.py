from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ai_review_assistant")
except PackageNotFoundError:
    __version__ = "unknown"
