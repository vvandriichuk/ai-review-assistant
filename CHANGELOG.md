# Changelog

## [0.6.2] - 2024-07-27
### Added
- Added missed rich library to dependencies list

## [0.6.1] - 2024-07-27
### Fixed
- Fixed some minor bugs with versions and documentations

## [0.6.0] - 2024-07-27
### Added
- You can put your own prompt to pyproject.toml file using [tool.code_review_assistant] block. Example of such block:

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

## [0.5.0] - 2024-07-26
### Added
- You can check version of AI Review Assistant

## [0.4.0] - 2024-07-26
### Added
- Added splitting long context by batch size
- Added support for multiple languages
- Added support for multiple models
- You can run AI Review Assistant in any directory

### Changed
- Updated version of main dependencies libs

## [0.1.0] - 2024-07-25
### Added
- Init library

[Unreleased]: https://github.com/vvandriichuk/ai-review-assistant/compare/v0.6.2...HEAD
[0.6.2]: https://github.com/vvandriichuk/ai-review-assistant/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/vvandriichuk/ai-review-assistant/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/vvandriichuk/ai-review-assistant/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/vvandriichuk/ai-review-assistant/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/vvandriichuk/ai-review-assistant/compare/v0.1.0...v0.4.0
[0.1.0]: https://github.com/vvandriichuk/ai-review-assistant/releases/tag/v0.1.0
