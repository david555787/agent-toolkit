# agent-toolkit

Two small tools for working with coding agents, built for CMU 15-114 HW8.

- **`no-rewrite`** (a skill): a read-only checker. After a coding agent finishes a task, it compares the agent's changes with the instructions I gave and reports which changes were allowed and which were not.
- **`search_project_history`** (an MCP tool): lets an agent search the git history of my earlier projects, which it cannot see from the repository it is working in.

Other documents: [DEMONSTRATION.md](DEMONSTRATION.md) (two real runs and what the checker caught) and [ITERATION.md](ITERATION.md) (a failure of version 1 and how I fixed it).

## The skill: `no-rewrite`

**What it does.** It takes two inputs: the original instructions I gave the coding agent (verbatim) and the working-tree diff. It reports one line per changed file:

```
[PASS | WARNING | FAIL] <path> — <quoted instruction sentence and the diff hunk it refers to>
OVERALL: PASS | WARNING | FAIL
```

Main rules: it never modifies anything; a change to a file the instructions forbid is FAIL; every verdict must cite a diff hunk; if no instructions are given it answers `CANNOT JUDGE: instructions missing` instead of guessing; vague instructions such as "clean up" never authorize behavior changes (added in v2, see ITERATION.md).

**When it triggers.** The description tells the agent to use it after a coding agent finishes a task, or when I ask whether the agent touched anything it should not have. I always ran it in a separate, fresh session, on a different model from the one that did the work.

**Why I built it.** I kept repeating the same boundaries in my own prompts:

- Liar Minesweeper: "Do not touch SPEC.md, index.html, style.css, game.js, ui.js or main.js."
- Mystery Kitchen: "don't touch scoring formulas or the other judges"
- Market Maker: "Do NOT write or touch README.md (I write it myself)."

Each time I had to check by hand whether the agent had obeyed.

## The MCP tool: `search_project_history`

**What it does.** `search_project_history(keyword: str) -> str` searches an index of the git history of three of my earlier projects (`inherited-game`, which is my Mystery Kitchen repo, `liar-minesweeper` and `market-maker`; 46 commits in total). It matches the keyword, case-insensitively, against commit messages, changed file names and short diff summaries, and returns up to 10 commits with repo, short hash, date, message, changed files and diff summary. If there is no documented reason for a change it says so and never invents one. It runs locally over stdio.

**Why I built it.** During previous project work, I often reminded the AI to only modify the specified parts. Therefore, "no-rewrite" was implemented to check whether the modifications exceeded the requirements. MCP was used to search the submission history of the old projects, enabling the new session to find relevant code and tests, thereby reducing the hassle of repeatedly explaining the background.

## Install

Paths marked **(machine-specific)** are examples from my computer. Replace them with yours.

### The skill

Copy the folder `.agents/skills/no-rewrite/` into one of:

- your project: `<your-project>/.agents/skills/no-rewrite/` (it is only loaded in sessions started from that project), or
- your user directory: `~/.agents/skills/no-rewrite/` (available in all projects).

Restart Codex if the skill does not appear.

### The MCP server

1. Clone this repository and create an environment with the dependency (Python 3.12 worked for me):

   ```
   python3 -m venv ~/.venvs/agent-toolkit
   ~/.venvs/agent-toolkit/bin/pip install -r mcp/requirements.txt
   ```

   `requirements.txt` pins `mcp<2`, because MCP 2.x no longer has the `FastMCP` import that `server.py` uses.

2. The repository already contains `mcp/history_index.json`, built from my own repositories. To index yours instead, run `mcp/build_index.py` with the paths of your repositories as arguments. 

3. Register the server in `~/.codex/config.toml`:

   ```toml
   [mcp_servers.project-history]
   command = "/Users/YOUR_NAME/.venvs/agent-toolkit/bin/python"   # machine-specific
   args = ["/Users/YOUR_NAME/agent-toolkit/mcp/server.py"]        # machine-specific
   ```

   Use absolute paths. On Windows use forward slashes.

4. Restart Codex, start a new session, and ask something only this tool can answer, for example: "Use the search_project_history tool with the keyword `SPEC` and list the repo, hash, date and message of every match." Then check that the tool was actually called.

If the tool does not show up: check the paths, check that the Python you registered has `mcp` installed, and make sure the server never prints to stdout (it logs to stderr), since stdout is the protocol channel.

## What I tested

I tested it twice on Mystery Kitchen: once only modifying the classic cooking method of Salmon, and the other time only modifying the comments. In both cases, I first called MCP to query the history, and then ran the checker in a separate new session. The checker gave PASS results, which were consistent with the actual diff. In the second test, one of the tests failed due to the old comments assertion, and this has been recorded separately. Additionally, when I used fuzzy instructions for testing, I found that the checker was not strict enough in its judgment. After modifying the rules and rerunning twice, it returned FAIL correctly both times.

## Limitations

- The returned diff text sometimes contains `[redacted path]` where my index builder replaced a path-like string, which also damaged some closing HTML tags. Retrieval works, but that text is not exact.
- The checker only sees the diff. It cannot know whether tests passed.
- The index includes commit messages and a few changed lines (at most 8 per file, 100 characters each, none from `.md` files) from my own repositories.
- Only one MCP tool, and I tested the checker on a small number of cases.

## What I borrowed

I referred to the checker design in HW8 assignment and the FastMCP example, and used the `mcp` Python library to set up the service. The specific modification scope rules and project history search function were designed according to my own project requirements.

## How I used AI

- I used Codex (GPT-6.1 Sol) to write `mcp/build_index.py`, `mcp/server.py` and the first version of `SKILL.md` from prompts I wrote, and I read and tested the results.
- I used GPT-6 Luna in separate Codex sessions as the checker.
- I used Claude to plan the steps, to draft the prompts I gave Codex, and to check my documents against the assignment. I wrote `DEMONSTRATION.md` and `ITERATION.md` in Chinese first and translated them into English.