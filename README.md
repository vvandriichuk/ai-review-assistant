# Installation

You can install the latest version of AI Review Assistant from [GitHub](https://github.com/vvandriichuk/ai-review-assistant):

```bash
pip install git+https://github.com/vvandriichuk/ai-review-assistant.git
```

# Help:
ai_review_assistant --help

# Example of usage:
ai_review_assistant --vendor openai --model gpt-4o --api-key your_api_key --program-language "Python,JavaScript,TypeScript" --result-output-language English --ignore-settings-files/--review-all-files review

# You can put your own prompt to pyproject.toml:

```[tool.code_review_assistant]
prompt_template = """
You are an AI Code Review Assistant with expert knowledge of {program_language}. As a senior {program_language} developer, review the following code changes:

Project Structure:
{project_structure}

File being reviewed: {file_path}

Analyze the code changes considering these aspects:
1. Code quality and readability
2. Potential bugs or errors
3. Performance implications
4. Consistency with the overall project structure
5. Suggestions for improvement
6. Best practices specific to {program_language}

Instructions for your response:
- Provide a concise summary (about 4-6 points) of your overall findings.
- Focus only on the most important or critical issues, if any.
- Clearly state whether you found any critical issues that need immediate attention.
- Include 1-2 key suggestions for improvement, if applicable.
- If no significant issues were found, briefly mention that the changes look good, but still provide a suggestion for potential enhancement if possible.

Your summary should be structured as follows:
1. Overall assessment (1-2 points)
2. Critical issues (if any) (1-2 points)
3. Key suggestions for improvement (3-4 points)

Provide your summary in {result_output_language}.
"""
```
