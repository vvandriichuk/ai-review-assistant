import sys
from pathlib import Path
from typing import Literal, cast

import click
from git import InvalidGitRepositoryError, Repo
from git.objects import Commit
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from ai_review_assistant import __version__
from ai_review_assistant.review import CodeReviewAssistant

console = Console()


def find_git_root(path: Path) -> str | None:
    try:
        repo = Repo(path, search_parent_directories=True)
        working_tree_dir = repo.working_tree_dir
        return str(working_tree_dir) if working_tree_dir is not None else None
    except InvalidGitRepositoryError:
        return None


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


def parse_languages(value: str) -> list[str]:
    return [lang.strip() for lang in value.split(",")]


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the version and exit.")
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
    default=0.1,
    help="Temperature for the AI model",
)
@click.option(
    "--code-depth",
    type=int,
    default=0,
    help="Depth of code structure to include in review",
)
@click.option(
    "--program-language",
    default="Python",
    help="Programming language(s) of the code being reviewed (comma-separated for multiple, e.g., 'Python,JavaScript')",
    type=click.UNPROCESSED,
    callback=lambda _, __, value: parse_languages(value),
)
@click.option(
    "--result-output-language",
    default="English",
    help="Language for the output review",
)
@click.pass_context
def cli(
    ctx: click.Context,
    version: bool,
    vendor: str,
    model: str,
    api_key: str,
    temperature: float,
    code_depth: int,
    program_language: list[str],
    result_output_language: str,
) -> None:
    if version:
        click.echo(f"AI Review Assistant version {__version__}")
        ctx.exit()

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit()

    if not api_key:
        click.echo(
            "API key must be provided either via --api-key option or AI_API_KEY environment variable.",
        )
        sys.exit(1)

    git_root = find_git_root(Path.cwd())
    if git_root is None:
        click.echo("Error: Not a git repository (or any of the parent directories).")
        sys.exit(1)

    repo = Repo(git_root)
    current_commit, previous_commit = get_current_and_previous_commit(repo)

    ctx.obj = {
        "assistant": CodeReviewAssistant(
            repo_path=git_root,
            vendor_name=cast(Literal["openai", "anthropic"], vendor),
            model_name=model,
            api_key=api_key,
            temperature=temperature,
            code_depth=code_depth,
            program_language=program_language,
            result_output_language=result_output_language,
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
            console.print(
                Panel(f"[bold green]File:[/bold green] {file_path}", expand=False),
            )
            console.print("[bold yellow]Review:[/bold yellow]")

            # Split the review into parts
            parts = review.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # This is regular text, print as Markdown
                    md = Markdown(part.strip())
                    console.print(md)
                else:
                    # This is code, use Pygments for syntax highlighting
                    # The first word after ``` is typically the language
                    code_lines = part.strip().split("\n")
                    if code_lines:
                        lang = code_lines[0].strip().lower()
                        code = "\n".join(code_lines[1:])
                        syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                        console.print(Panel(syntax, expand=False))

            console.print()
    else:
        console.print(
            Panel(
                "[bold red]No changes detected or review failed.[/bold red]",
                expand=False,
            ),
        )
        sys.exit(1)


if __name__ == "__main__":
    cli()
