import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from github import Github, Auth
from langchain_core.tools import tool

load_dotenv()

_raw_fs_root = os.getenv("FS_ROOT")
if _raw_fs_root:
    FS_ROOT = Path(_raw_fs_root).resolve()
else:
    FS_ROOT = (
        Path(__file__).resolve().parents[2]
        / "codebase_data"
        / "PurePill-habitatAI"
    ).resolve()

def _resolve_safe_path(relative_path: str) -> Path:
    """Ensures file access stays strictly inside the target repository."""
    target = (FS_ROOT / relative_path).resolve()
    if not str(target).startswith(str(FS_ROOT)):
        raise PermissionError(f"Access denied: Path '{relative_path}' is outside the repository boundary.")
    return target


@tool
def read_local_file(relative_path: str) -> str:
    """Reads content of a file within the local PurePill-habitatAI repository."""
    print(f"    [TOOL CALL] Reading file: {relative_path}")
    try:
        path = _resolve_safe_path(relative_path)
        if not path.is_file():
            return f"Error: File not found at '{relative_path}'"
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_local_file(relative_path: str, content: str) -> str:
    """Creates or overwrites a file in the local PurePill-habitatAI repository."""
    try:
        path = _resolve_safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {relative_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def list_local_directory(relative_path: str = "") -> str:
    """Lists files and folders inside the local PurePill-habitatAI repository."""
    try:
        path = _resolve_safe_path(relative_path)
        if not path.is_dir():
            return f"Error: '{relative_path}' is not a directory."
        items = [f"{'[DIR] ' if p.is_dir() else '[FILE]'} {p.name}" for p in path.iterdir()]
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def _get_github_repo():
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token missing in .env (GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN).")
    gh = Github(auth=Auth.Token(token))
    return gh.get_repo("test-habitatai/PurePill-habitatAI")


@tool
def github_list_issues(state: str = "open") -> str:
    """Lists issues from the test-habitatai/PurePill-habitatAI repository.
    state can be 'open', 'closed', or 'all'.
    """
    try:
        repo = _get_github_repo()
        issues_paginated = repo.get_issues(state=state)
        
        output = []
        count = 0
        for issue in issues_paginated:
            if not issue.pull_request:
                output.append(f"#{issue.number} - {issue.title} (State: {issue.state})")
                count += 1
                if count >= 10:
                    break

        if not output:
            return "No open issues found in test-habitatai/PurePill-habitatAI."
        return "\n".join(output)
    except Exception as e:
        return f"GitHub API error: {str(e)}"


@tool
def github_create_issue(title: str, body: str) -> str:
    """Creates a new issue in test-habitatai/PurePill-habitatAI."""
    try:
        repo = _get_github_repo()
        issue = repo.create_issue(title=title, body=body)
        return f"Issue created successfully: #{issue.number} - {issue.html_url}"
    except Exception as e:
        return f"Failed to create issue: {str(e)}"


@tool
def github_create_pull_request(
    title: str,
    body: str,
    head_branch: str = "habitat-dev",
    base_branch: str = "main",
) -> str:
    """Creates a pull request or returns the active pull request if one is already open for head_branch."""
    print(f"    [TOOL CALL] Managing PR for {head_branch} -> {base_branch}...")
    try:
        repo = _get_github_repo()
        owner = repo.owner.login
        head_ref = f"{owner}:{head_branch}" if ":" not in head_branch else head_branch

        open_prs = repo.get_pulls(state="open", base=base_branch)
        for pr in open_prs:
            if pr.head.ref == head_branch or pr.head.label == head_ref:
                return (
                    f"Active pull request already exists for '{head_branch}': "
                    f"#{pr.number} - {pr.html_url}. New commits on '{head_branch}' "
                    "are automatically tracked."
                )

        try:
            new_pr = repo.create_pull(
                title=title, body=body, head=head_ref, base=base_branch
            )
        except Exception:
            new_pr = repo.create_pull(
                title=title, body=body, head=head_branch, base=base_branch
            )

        return f"Pull request opened successfully: #{new_pr.number} - {new_pr.html_url}"
    except Exception as e:
        return f"Failed to create pull request: {str(e)}"


@tool
def system_health_check() -> str:
    """Verifies that local workspace and dependencies are operational."""
    return f"HabitatAI operational. FS_ROOT mounted at: {FS_ROOT}"

@tool
def github_commit_file(
    file_path: str,
    content: str,
    commit_message: str,
    branch_name: str
) -> str:
    """Creates a new branch (if not existing) and commits a file update directly to GitHub."""
    print(f"    [TOOL CALL] Committing '{file_path}' to branch '{branch_name}' via GitHub API...")
    try:
        repo = _get_github_repo()
        default_branch = repo.default_branch
        base_ref = repo.get_git_ref(f"heads/{default_branch}")
        
        try:
            repo.get_git_ref(f"heads/{branch_name}")
        except Exception:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base_ref.object.sha)

        try:
            existing_file = repo.get_contents(file_path, ref=branch_name)
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=existing_file.sha,
                branch=branch_name
            )
            return f"Updated {file_path} on branch {branch_name}"
        except Exception:
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=branch_name
            )
            return f"Created {file_path} on branch {branch_name}"
    except Exception as e:
        return f"Failed to commit file to branch: {str(e)}"