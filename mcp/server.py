"""Read-only project-history search served over MCP stdio."""

import json
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP


logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)
INDEX_PATH = Path(__file__).resolve().with_name("history_index.json")
mcp = FastMCP("project-history")


def _diff_text(value):
    """Flatten summary content without searching JSON property names."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "\n".join(_diff_text(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(_diff_text(item) for item in value)
    return ""


@mcp.tool()
def search_project_history(keyword: str) -> str:
    """Search indexed git history of my earlier projects: inherited-game,
    liar-minesweeper, and market-maker. These projects are outside the current
    repo. Call when needing context on past changes or design decisions in
    those projects. Match a case-insensitive keyword against commit messages,
    changed file names, and diff summary text. Return up to 10 commits with
    repo, short hash, date, message, changed files, and a short diff summary.
    Include only documented prompt-log excerpts; when an excerpt is null,
    report "no documented reason available" and never infer a reason.
    Empty keywords and searches with no matches return clear plain-text
    messages rather than errors.
    """
    needle = keyword.strip().casefold()
    if not needle:
        return "Empty keyword: enter a non-empty keyword to search project history."

    try:
        entries = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.exception("Could not load the project history index")
        return "Project history index is unavailable."

    matches = []
    for entry in entries:
        diff = _diff_text(entry.get("diff_summary", ""))
        files = entry.get("changed_files", [])
        searchable = "\n".join([entry.get("message", ""), *files, diff])
        if needle not in searchable.casefold():
            continue
        excerpt = entry.get("prompt_log_excerpt")
        reason = "no documented reason available" if excerpt is None else excerpt
        summary = diff if len(diff) <= 1200 else diff[:1200] + "\n[summary truncated]"
        matches.append(
            f"repo: {entry['repo']}\n"
            f"short_hash: {entry['short_hash']}\n"
            f"date: {entry['date']}\n"
            f"message: {entry['message']}\n"
            f"changed files: {', '.join(files) or '(none)'}\n"
            f"diff summary:\n{summary or '(none)'}\n"
            f"prompt_log_excerpt: {reason}"
        )
        if len(matches) == 10:
            break

    return "\n\n---\n\n".join(matches) if matches else "No matching project history found."


if __name__ == "__main__":
    mcp.run(transport="stdio")
