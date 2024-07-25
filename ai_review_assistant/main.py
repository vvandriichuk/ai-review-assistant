import os
import sys
import click
from git import Repo
from ai_review_assistant.review import CodeReviewAssistant


def get_current_and_previous_commit(repo):
    """Get the current commit and its parent."""
    current_commit = repo.head.commit
    previous_commit = current_commit.parents[0] if current_commit.parents else None
    return current_commit, previous_commit


def get_file_changes(repo, current_commit, previous_commit):
    """Get the changes for each modified file between two commits."""
    diff_index = previous_commit.diff(current_commit)
    changes = {}
    for diff in diff_index.iter_change_type('M'):
        changes[diff.a_path] = {
            'before': diff.a_blob.data_stream.read().decode('utf-8'),
            'after': diff.b_blob.data_stream.read().decode('utf-8')
        }
    return changes


@click.group()
@click.option('--vendor', default='openai', help='AI vendor to use (e.g., openai)')
@click.option('--api-key', envvar='OPENAI_API_KEY', help='API key for the AI vendor')
@click.pass_context
def cli(ctx, vendor, api_key):
    if not api_key:
        click.echo("API key must be provided either via --api-key option or OPENAI_API_KEY environment variable.")
        sys.exit(1)

    repo = Repo('.')
    current_commit, previous_commit = get_current_and_previous_commit(repo)

    ctx.obj = {
        'assistant': CodeReviewAssistant(
            repo_path='.',
            vendor_name=vendor,
            model_name='gpt-3.5-turbo',
            api_key=api_key,
            temperature=0.7,
            code_depth=3
        ),
        'repo': repo,
        'current_commit': current_commit,
        'previous_commit': previous_commit
    }


@cli.command()
@click.pass_context
def review(ctx):
    """Review changes in the current commit"""
    repo = ctx.obj['repo']
    assistant = ctx.obj['assistant']
    current_commit = ctx.obj['current_commit']
    previous_commit = ctx.obj['previous_commit']

    if not previous_commit:
        click.echo("This is the initial commit. No changes to review.")
        return

    changes = get_file_changes(repo, current_commit, previous_commit)
    reviews = {}

    for file_path, file_changes in changes.items():
        review = assistant.review_changes(file_path, file_changes['before'], file_changes['after'])
        reviews[file_path] = review

    _print_reviews(reviews)


def _print_reviews(reviews):
    if reviews:
        for file_path, review in reviews.items():
            click.echo(f"File: {file_path}\nReview:\n{review}\n")
    else:
        click.echo("No changes detected or review failed.")
        sys.exit(1)


if __name__ == "__main__":
    cli()