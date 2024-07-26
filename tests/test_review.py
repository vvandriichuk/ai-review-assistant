import pytest
from click.testing import CliRunner
from git import Repo
from unittest.mock import Mock, patch

from ai_review_assistant.main import (
    cli,
    get_current_and_previous_commit,
    get_file_changes,
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
def test_cli_review_command(
    MockGetFileChanges, MockCodeReviewAssistant, MockRepo, mock_repo, mock_assistant
):
    MockRepo.return_value = mock_repo
    MockCodeReviewAssistant.return_value = mock_assistant
    MockGetFileChanges.return_value = {
        "test_file.py": {"before": "old", "after": "new"}
    }

    mock_assistant.review_changes.return_value = "Mocked review result"

    runner = CliRunner()
    result = runner.invoke(cli, ["--api-key", "test_key", "review"])

    assert result.exit_code == 0
    assert "Reviewing changes" in result.output
    assert "Mocked review result" in result.output


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
    result = runner.invoke(cli, ["--api-key", "test_key", "review"])

    assert result.exit_code == 1
    assert "No changes detected or review failed." in result.output


@patch("ai_review_assistant.main.Repo")
def test_cli_missing_api_key(MockRepo, mock_repo):
    MockRepo.return_value = mock_repo

    runner = CliRunner()
    result = runner.invoke(cli, ["review"])

    assert result.exit_code == 1
    assert "API key must be provided" in result.output


def test_code_review_assistant_init():
    assistant = CodeReviewAssistant(
        repo_path=".",
        vendor_name="openai",
        model_name="gpt-3.5-turbo",
        api_key="test_key",
        temperature=0.5,
        code_depth=2,
    )
    assert assistant.repo_path == "."
    assert assistant.vendor_name == "openai"
    assert assistant.model_name == "gpt-3.5-turbo"
    assert assistant.temperature == 0.5
    assert assistant.code_depth == 2


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
    )

    result = assistant.review_changes("test_file.py", "old code", "new code")
    assert result == "Mocked AI review"
    mock_llm.invoke.assert_called_once()
