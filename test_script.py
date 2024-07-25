from ai_review_assistant.review import CodeReviewAssistant

# Тестовый код
assistant = CodeReviewAssistant(
    repo_path=".",
    vendor_name="openai",
    model_name="gpt-4o",
    api_key="sk-None-QIQMFZQTRxTRGXLt8982T3BlbkFJsFxMruDUElDvjn8euaVG",
)


# Пример использования
result = assistant.review_changes(
    "example.py",
    "def hello():\n    print('Hello')",
    "def hello():\n    print('Hello, World!')",
)
print(result)
