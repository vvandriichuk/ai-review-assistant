import pytest
from click.testing import CliRunner
from git import Repo
from unittest.mock import Mock, patch

from ai_review_assistant.main import (
    cli,
    get_current_and_previous_commit,
    get_file_changes,
    parse_languages,
)
from ai_review_assistant.review import CodeReviewAssistant


@pytest.fixture
def mock_repo():
    mock = Mock(spec=Repo)
    mock.head.commit.hexsha = "current_commit_hash"
    mock.head.commit.parents = [Mock(hexsha="previous_commit_hash")]
    return mock


@pytest.fixture
def mock_assistant():
    mock = Mock(spec=CodeReviewAssistant)
    mock.review_changes.return_value = "Mocked review result"
    return mock


def test_get_current_and_previous_commit(mock_repo):
    current, previous = get_current_and_previous_commit(mock_repo)
    assert current.hexsha == "current_commit_hash"
    assert previous.hexsha == "previous_commit_hash"


def test_get_file_changes():
    mock_current_commit = Mock()
    mock_previous_commit = Mock()
    mock_diff = Mock()
    mock_diff.a_path = "test_file.py"
    mock_diff.a_blob.data_stream.read.return_value = b"old content"
    mock_diff.b_blob.data_stream.read.return_value = b"new content"
    mock_previous_commit.diff.return_value.iter_change_type.return_value = [mock_diff]

    changes = get_file_changes(mock_current_commit, mock_previous_commit)

    assert "test_file.py" in changes
    assert changes["test_file.py"]["before"] == "old content"
    assert changes["test_file.py"]["after"] == "new content"


@patch("ai_review_assistant.main.Repo")
@patch("ai_review_assistant.main.CodeReviewAssistant")
@patch("ai_review_assistant.main.get_file_changes")
@patch("ai_review_assistant.main.find_git_root")
def test_cli_review_command(
    MockFindGitRoot,
    MockGetFileChanges,
    MockCodeReviewAssistant,
    MockRepo,
    mock_repo,
    mock_assistant,
):
    MockFindGitRoot.return_value = "/mock/git/root"
    MockRepo.return_value = mock_repo
    MockCodeReviewAssistant.return_value = mock_assistant
    MockGetFileChanges.return_value = {
        "test_file.py": {"before": "old", "after": "new"}
    }

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test_key",
            "--program-language",
            "Python",
            "--result-output-language",
            "English",
            "review",
        ],
    )

    print(f"CLI output: {result.output}")
    print(f"Exit code: {result.exit_code}")

    assert result.exit_code == 0, f"CLI failed with error: {result.exception}"
    assert "Reviewing changes" in result.output
    mock_assistant.review_changes.assert_called_once()


@patch("ai_review_assistant.main.Repo")
@patch("ai_review_assistant.main.CodeReviewAssistant")
@patch("ai_review_assistant.main.get_file_changes")
def test_cli_review_command_no_changes(
    MockGetFileChanges, MockCodeReviewAssistant, MockRepo, mock_repo, mock_assistant
):
    MockRepo.return_value = mock_repo
    MockCodeReviewAssistant.return_value = mock_assistant
    MockGetFileChanges.return_value = {}

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test_key",
            "--program-language",
            "JavaScript",
            "--result-output-language",
            "English",
            "review",
        ],
    )

    assert result.exit_code == 1
    assert "No changes detected or review failed." in result.output


def test_code_review_assistant_init():
    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        temperature=0.5,
        code_depth=2,
        program_language=["Python"],
        result_output_language="English",
    )
    assert assistant.repo_path == "."
    assert assistant.vendor_name == "openai"
    assert assistant.model_name == "gpt-3.5-turbo"
    assert assistant.temperature == 0.5
    assert assistant.code_depth == 2
    assert assistant.program_language == ["Python"]
    assert assistant.result_output_language == "English"


@patch("ai_review_assistant.review.ChatOpenAI")
def test_code_review_assistant_review_changes(MockChatOpenAI):
    mock_llm = Mock()
    mock_llm.invoke.return_value.content = "Mocked AI review"
    MockChatOpenAI.return_value = mock_llm

    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        program_language=["JavaScript"],
        result_output_language="English",
    )

    result = assistant.review_changes("test_file.js", "old code", "new code")
    assert result == "Mocked AI review"
    mock_llm.invoke.assert_called_once()


def test_code_review_assistant_construct_prompt():
    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        program_language=["Python"],
        result_output_language="English",
    )

    prompt = assistant.construct_prompt("test_file.py", "old code", "new code")
    assert "Python" in prompt


def test_code_review_assistant_str_repr():
    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        temperature=0.7,
        code_depth=3,
        program_language=["JavaScript"],
        result_output_language="English",
    )

    assert (
        str(assistant)
        == "Code Review Assistant for JavaScript using Openai with model gpt-3.5-turbo (output in English)"
    )
    assert repr(assistant) == (
        "CodeReviewAssistant(repo_path='.', vendor_name='openai', "
        "model_name='gpt-3.5-turbo', temperature=0.7, code_depth=3, "
        "program_language=['JavaScript'], result_output_language='English')"
    )


def test_cli_missing_api_key():
    runner = CliRunner()
    result = runner.invoke(cli, ["review"])
    assert result.exit_code != 0
    assert "API key must be provided" in result.output


def test_code_review_assistant_invalid_vendor():
    with pytest.raises(ValueError, match="Vendor 'invalid' is not supported"):
        CodeReviewAssistant(
            repo_path=".",
            vendor_name="invalid",
            model_name="gpt-3.5-turbo",
            api_key="test_key",
            program_language=["Python"],
            result_output_language="English",
        )


def test_code_review_assistant_unsupported_language():
    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        program_language=["Unsupported"],
        result_output_language="English",
    )
    prompt = assistant.construct_prompt("test_file.txt", "old code", "new code")
    assert "Unsupported" in prompt


@pytest.mark.parametrize(
    "vendor,model,temperature",
    [
        ("openai", "gpt-4", 0.5),
        ("anthropic", "claude-3", 0.7),
    ],
)
@patch("ai_review_assistant.main.CodeReviewAssistant")
@patch("ai_review_assistant.main.Repo")
@patch("ai_review_assistant.main.get_file_changes")
def test_cli_options(
    MockGetFileChanges, MockRepo, MockCodeReviewAssistant, vendor, model, temperature
):
    MockGetFileChanges.return_value = {
        "test_file.py": {"before": "old code", "after": "new code"}
    }
    mock_assistant = Mock()
    mock_assistant.review_changes.return_value = "Mocked review"
    MockCodeReviewAssistant.return_value = mock_assistant

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--vendor",
            vendor,
            "--model",
            model,
            "--api-key",
            "test_key",
            "--temperature",
            str(temperature),
            "--program-language",
            "Python,JavaScript",
            "--result-output-language",
            "French",
            "review",
        ],
    )
    assert result.exit_code == 0
    assert "Mocked review" in result.output


def test_cli_invalid_option():
    runner = CliRunner()
    result = runner.invoke(cli, ["--invalid-option", "value", "review"])
    assert result.exit_code != 0
    assert "Error: No such option: --invalid-option" in result.output


def test_code_review_assistant_count_tokens():
    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        program_language=["Python"],
        result_output_language="English",
    )
    text = "This is a test sentence."
    token_count = assistant.count_tokens(text)
    assert isinstance(token_count, int)
    assert token_count > 0


@patch("ai_review_assistant.review.Path")
def test_code_review_assistant_get_project_structure(MockPath):
    mock_dir = Mock()
    mock_dir.is_dir.return_value = True
    mock_dir.name = "src"

    mock_file = Mock()
    mock_file.is_dir.return_value = False
    mock_file.name = "README.md"

    MockPath.return_value.iterdir.return_value = [mock_dir, mock_file]

    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        program_language=["Python"],
        result_output_language="English",
    )
    structure = assistant.get_project_structure(".", 1)
    assert "[DIR] src" in structure
    assert "[FILE] README.md" in structure


@patch("ai_review_assistant.review.ChatOpenAI")
def test_code_review_assistant_large_file_handling(MockChatOpenAI):
    mock_llm = Mock()
    mock_llm.invoke.return_value.content = "Mocked AI review"
    MockChatOpenAI.return_value = mock_llm

    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        program_language=["Python"],
        result_output_language="English",
        batch_size=50,
    )

    large_code_before = "print('hello')\n" * 1000  # Create a large code string
    large_code_after = "print('hello')\n" * 1000 + "print('world')\n"

    result = assistant.review_changes(
        "large_file.py", large_code_before, large_code_after
    )
    assert "Mocked AI review" in result
    assert mock_llm.invoke.call_count > 1


@patch("ai_review_assistant.review.ChatAnthropic")
@patch("ai_review_assistant.review.tiktoken.get_encoding")
def test_code_review_assistant_anthropic(MockGetEncoding, MockChatAnthropic):
    mock_llm = Mock()
    mock_llm.invoke.return_value.content = "Mocked Anthropic AI review"
    MockChatAnthropic.return_value = mock_llm

    mock_tokenizer = Mock()
    mock_tokenizer.encode.return_value = [
        1,
        2,
        3,
        4,
        5,
    ]  # This list will have a length of 5
    MockGetEncoding.return_value = mock_tokenizer

    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="anthropic",
        model_name="claude-3",
        api_key="test_key",
        program_language=["Python"],
        result_output_language="English",
    )

    assert assistant.tokenizer == mock_tokenizer
    MockGetEncoding.assert_called_once_with("cl100k_base")

    token_count = assistant.count_tokens("test text")
    assert token_count == 5
    mock_tokenizer.encode.assert_called_once_with("test text")

    result = assistant.review_changes("test_file.py", "old code", "new code")
    assert result == "Mocked Anthropic AI review"
    MockChatAnthropic.assert_called_once()


def test_code_review_assistant_api_key_handling():
    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        program_language=["Python"],
        result_output_language="English",
    )
    assert assistant.api_key == "test_key"
    assert "test_key" not in str(assistant)
    assert "test_key" not in repr(assistant)


def test_parse_languages():
    assert parse_languages("Python") == ["Python"]
    assert parse_languages("Python,JavaScript") == ["Python", "JavaScript"]
    assert parse_languages("Python, JavaScript, TypeScript") == [
        "Python",
        "JavaScript",
        "TypeScript",
    ]


@patch("ai_review_assistant.main.Repo")
@patch("ai_review_assistant.main.CodeReviewAssistant")
@patch("ai_review_assistant.main.get_file_changes")
@patch("ai_review_assistant.main.find_git_root")
def test_cli_review_command_multiple_languages(
    MockFindGitRoot, MockGetFileChanges, MockCodeReviewAssistant, MockRepo
):
    MockFindGitRoot.return_value = "/mock/git/root"
    MockGetFileChanges.return_value = {
        "test_file.py": {"before": "old", "after": "new"}
    }

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--api-key",
            "test_key",
            "--program-language",
            "Python,JavaScript",
            "--result-output-language",
            "English",
            "review",
        ],
    )

    assert result.exit_code == 0
    MockCodeReviewAssistant.assert_called_once_with(
        repo_path="/mock/git/root",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        temperature=0.1,
        code_depth=0,
        program_language=["Python", "JavaScript"],
        result_output_language="English",
    )


def test_version_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "AI Review Assistant version" in result.output
