"""Index local Git history without changing the source repositories."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def git(repo, *arguments):
    """Run only the two read-only Git commands permitted for this indexer."""
    if arguments[0] not in {"log", "show"}:
        raise ValueError("Only git log and git show are permitted")
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def history(repo):
    # NUL separators preserve multiline messages and unusual file names.
    output = git(
        repo, "log", "--all", "-z", "--no-show-signature",
        "--format=%H%x00%h%x00%cI%x00%B%x00%an%x00%ae%x00%cn%x00%ce",
    )
    fields = output.split("\0")
    if fields[-1] == "":
        fields.pop()
    if len(fields) % 8:
        raise ValueError("Unexpected git log record format")
    return [fields[offset:offset + 8] for offset in range(0, len(fields), 8)]


EMAIL = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w.-]+", re.UNICODE)
ABSOLUTE_PATH = re.compile(r"(?<![\w./])(?:[A-Za-z]:[\\/]|/(?!/))[^\s\"'<>|,;]*")
HOME_PATH = re.compile(r"/Users/[^\s\"'<>|,;]*")
AUTHOR_TRAILER = re.compile(
    r"(?im)^\s*(?:co-authored-by|signed-off-by|reviewed-by|acked-by):\s*(.*?)\s*<[^>]*>"
)


def redactor(histories):
    # Identities are used only for redaction and are never serialized.
    identities = set()
    for records in histories:
        for record in records:
            identities.update(value for value in record[4:] if value)
            identities.update(AUTHOR_TRAILER.findall(record[3]))
    identity_pattern = None
    if identities:
        identity_pattern = re.compile(
            r"(?<!\w)(?:"
            + "|".join(re.escape(value) for value in sorted(identities, key=len, reverse=True))
            + r")(?!\w)",
            re.IGNORECASE,
        )

    def redact(value):
        if isinstance(value, str):
            if identity_pattern:
                value = identity_pattern.sub("[redacted identity]", value)
            value = EMAIL.sub("[redacted email]", value)
            value = HOME_PATH.sub("[redacted path]", value)
            return ABSOLUTE_PATH.sub("[redacted path]", value)
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, dict):
            return {key: redact(item) for key, item in value.items()}
        return value

    return redact


def show(repo, commit, *options, paths=()):
    # Merge commits are compared to their first parent; roots to an empty tree.
    return git(
        repo, "show", "--format=", "--no-show-signature", "--no-color",
        "--no-ext-diff", "--no-textconv", "--no-renames", "--root",
        "--diff-merges=first-parent", *options, commit, "--", *paths,
    )


def index_commit(repo, record):
    commit, short_hash, date, message = record[:4]
    files = [name for name in show(repo, commit, "--name-only", "-z").split("\0") if name]
    snippets = []
    for name in files:
        if name.startswith("/") or ".." in name.split("/"):
            raise ValueError("Git returned a non-relative file path")
        if name.lower().endswith((".md", ".txt")):
            stat = show(repo, commit, "--stat", paths=(name,))
            snippets.append({"path": name, "stat": next(iter(stat.splitlines()), "")})
            continue
        patch = show(repo, commit, "--patch", "--unified=0", paths=(name,))
        changed_lines = []
        in_hunk = False
        for line in patch.splitlines():
            if line.startswith("@@ "):
                in_hunk = True
            elif in_hunk and line.startswith(("+", "-")):
                changed_lines.append(line)
                if len(changed_lines) == 8:
                    break
        snippets.append({"path": name, "changed_lines": changed_lines})
    return {
        "repo": repo.name,
        "short_hash": short_hash,
        "date": date,
        "message": message.rstrip("\n"),
        "changed_files": files,
        "diff_summary": {
            "stat": show(repo, commit, "--stat").rstrip("\n"),
            "files": snippets,
        },
        "prompt_log_excerpt": None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repos", nargs="+", type=Path, help="Local repositories to index")
    args = parser.parse_args()
    histories = [history(repo) for repo in args.repos]
    redact = redactor(histories)
    entries = []
    for repo, records in zip(args.repos, histories):
        entries.extend(index_commit(repo, record) for record in records)
    entries = redact(entries)
    # Truncate after redaction so replacement text also fits the length limit.
    for entry in entries:
        for snippet in entry["diff_summary"]["files"]:
            if "changed_lines" in snippet:
                snippet["changed_lines"] = [line[:100] for line in snippet["changed_lines"]]
    output = Path(__file__).resolve().with_name("history_index.json")
    output.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for repo, records in zip(args.repos, histories):
        print(f"{repo.name}: {len(records)} commits indexed", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Indexing failed: {error}", file=sys.stderr)
        sys.exit(1)
