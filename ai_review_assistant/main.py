import sys
from typing import Literal, cast

import click
from git import Repo
from git.objects import Commit

from ai_review_assistant.review import CodeReviewAssistant


def get_current_and_previous_commit(repo: Repo) -> tuple[Commit, Commit | None]:
    """Get the current commit and its parent."""
    current_commit = repo.head.commit
    previous_commit = current_commit.parents[0] if current_commit.parents else None
    return current_commit, previous_commit


def get_file_changes(
    current_commit: Commit,
    previous_commit: Commit | None,
) -> dict[str, dict[str, str]]:
    """Get the changes for each modified file between two commits."""
    if previous_commit is None:
        return {}
    diff_index = previous_commit.diff(current_commit)
    changes = {}
    for diff in diff_index.iter_change_type("M"):
        changes[diff.a_path] = {
            "before": diff.a_blob.data_stream.read().decode("utf-8"),
            "after": diff.b_blob.data_stream.read().decode("utf-8"),
        }
    return changes


@click.group()
@click.option(
    "--vendor",
    type=click.Choice(["openai", "anthropic"]),
    default="openai",
    help="AI vendor to use",
)
@click.option("--model", default="gpt-3.5-turbo", help="Model name to use")
@click.option("--api-key", envvar="AI_API_KEY", help="API key for the AI vendor")
@click.option(
    "--temperature",
    type=float,
    default=0.7,
    help="Temperature for the AI model",
)
@click.option(
    "--code-depth",
    type=int,
    default=0,
    help="Depth of code structure to include in review",
)
@click.pass_context
def cli(
    ctx: click.Context,
    vendor: str,
    model: str,
    api_key: str,
    temperature: float,
    code_depth: int,
) -> None:
    if not api_key:
        click.echo(
            "API key must be provided either via --api-key option or AI_API_KEY environment variable.",
        )
        sys.exit(1)

    repo = Repo(".")
    current_commit, previous_commit = get_current_and_previous_commit(repo)

    ctx.obj = {
        "assistant": CodeReviewAssistant(
            repo_path=".",
            vendor_name=cast(Literal["openai", "anthropic"], vendor),
            model_name=model,
            api_key=api_key,
            temperature=temperature,
            code_depth=code_depth,
        ),
        "repo": repo,
        "current_commit": current_commit,
        "previous_commit": previous_commit,
    }


@cli.command()
@click.pass_context
def review(ctx: click.Context) -> None:
    """Review changes in the current commit"""
    assistant: CodeReviewAssistant = ctx.obj["assistant"]
    current_commit: Commit = ctx.obj["current_commit"]
    previous_commit: Commit | None = ctx.obj["previous_commit"]

    if not previous_commit:
        click.echo("This is the initial commit. No changes to review.")
        return

    changes = get_file_changes(current_commit, previous_commit)
    reviews: dict[str, str] = {}

    with click.progressbar(changes.items(), label="Reviewing changes") as bar:
        for file_path, file_changes in bar:
            review = assistant.review_changes(
                file_path,
                file_changes["before"],
                file_changes["after"],
            )
            reviews[file_path] = review

    _print_reviews(reviews)


def _print_reviews(reviews: dict[str, str]) -> None:
    if reviews:
        for file_path, review in reviews.items():
            click.echo(click.style(f"File: {file_path}", fg="green", bold=True))
            click.echo(click.style("Review:", fg="yellow", bold=True))
            click.echo(f"{review}\n")
    else:
        click.echo("No changes detected or review failed.")
        sys.exit(1)


if __name__ == "__main__":
    cli()
