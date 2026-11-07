# Demonstration

## The task

I made one small change on each of two branches, `hw8-demo-1` and `hw8-demo-2`, of my Mystery Kitchen game repository (`inherited-game`). Every session was started from the `agent-toolkit` project and worked on the game repository through absolute paths. Before each change the agent searched my project history with the MCP tool. After each change I used the `no-rewrite` checker in a separate, fresh session to check the scope of the change. The coding agent used GPT-6.1 Sol and the checker used GPT-6 Luna.

The tool-call evidence below is not shown directly in the Codex interface. After each task, I asked the agent in the same session to show the exact arguments and the raw text the tool returned. These saved responses are retrospective agent reports, not direct tool-event logs. The tool is `search_project_history`. The original task prompts and saved responses are included in `evidence/`; the links below preserve this distinction.

## Run 1

Source records: [original task prompt](evidence/run1-promptA.txt) and [saved agent response about the tool call](evidence/run1-sessionA-toolcall.txt).

The agent's tool call, which I asked it to show after the task finished:

```
Tool: search_project_history
Arguments: {"keyword":"score"}

Returned (first entry, truncated):
repo: inherited-game
short_hash: ad1cfb2
date: 2026-10-31T11:18:51-04:00
message: Fix technician judge crediting blended food as knife work
changed files: game.js, tests/game.test.cjs
[...]
prompt_log_excerpt: no documented reason available
```
The coding agent (GPT-6.1 Sol) changed one line. This is the full diff:

```
@@ -13,7 +13,7 @@ const CATEGORIES = [
-  Salmon:{color:'#f18c72',prep:['Portion','Portioned'],cook:12,raw:true,classic:['saute','bake']},
+  Salmon:{color:'#f18c72',prep:['Portion','Portioned'],cook:12,raw:true,classic:['saute','bake','boil']},
```

Then I opened a fresh session with a different model (GPT-6 Luna) and ran the no-rewrite checker. The checker first read SKILL.md, then ran only read-only git commands:

```
cat ~/agent-toolkit/.agents/skills/no-rewrite/SKILL.md && git -C ~/inherited-game status --short --branch && git -C ~/inherited-game diff --
git -C ~/inherited-game status --short --untracked-files=all && git -C ~/inherited-game diff HEAD --
```

Its report:

```
[PASS] game.js — @@ -13,7 +13,7 @@; "You MAY edit only: the Salmon line inside the INGREDIENTS object in game.js." The diff changes only Salmon's classic array as requested.

OVERALL: PASS
```

My notes on Run 1: I asked the agent to search for `score`, then add `'boil'` to Salmon's `classic` array only, without touching the scoring logic or the tests. The history search returned two earlier commits that fixed judge behavior, but they had little to do with this change. The final diff contains only the specified line and all 15 tests passed, so I agree with the checker's PASS. From the records I have, I cannot see that the history search had any real effect on this change.

## Run 2

Source records: [original task prompt](evidence/run2-promptA.txt) and [saved agent response about the tool call](evidence/run2-sessionA-toolcall.txt).

I asked the agent (GPT-6.1 Sol) to search the history for `knife work`, then change one feedback string in `scoreDish()` from `No knife work on this plate.` to `No prep work on this plate.` without touching `tests/`. As in Run 1, I asked it to show its tool call after it finished. The call and the first returned entry:

```
Tool: search_project_history
Arguments: {"keyword":"knife work"}

Returned (first entry, truncated):
repo: inherited-game
short_hash: ad1cfb2
date: 2026-10-31T11:18:51-04:00
message: Fix technician judge crediting blended food as knife work
changed files: game.js, tests/game.test.cjs
[...]
prompt_log_excerpt: no documented reason available
```

The agent's diff (`[...]` marks the unchanged rest of the long line):

```
@@ -677,7 +677,7 @@ function scoreDish(basket,seasonings) {
-    `${handled.length?`${handled.length} of ${n} ingredient${n>1?'s':''} handled with the right knife work.`:'No knife work on this plate.'} [...]
+    `${handled.length?`${handled.length} of ${n} ingredient${n>1?'s':''} handled with the right knife work.`:'No prep work on this plate.'} [...]
```

The agent ran the existing tests: 14 passed, 1 failed. The failing test is "technician credits knife work only for prepped ingredients, not directly blended egg" (tests/game.test.cjs, line 179), which still expects `/No knife work on this plate/`. The agent reported the failure and, as I required, did not edit the test.

Then I ran the checker in a fresh session with a different model (GPT-6 Luna). It read SKILL.md first and then ran only read-only git commands:

```
cat ~/agent-toolkit/.agents/skills/no-rewrite/SKILL.md && git -C ~/inherited-game status --short --branch && git -C ~/inherited-game diff --
git -C ~/inherited-game status --short --untracked-files=all && git -C ~/inherited-game diff HEAD --
```

Its report:

```
[PASS] game.js — """Step 2: In game.js, inside scoreDish(), change the string 'No knife work on this plate.' to 'No prep work on this plate.'""" The diff hunk @@ -677,7 +677,7 @@ shows only that string changed.

OVERALL: PASS
```

My notes on Run 2: the search found commit `ad1cfb2`, which contains the related logic and a test, so it hinted that this string might be constrained by a test. The agent replaced only the specified string. One test failed because it still matches the old wording. The agent reported the failure and followed my instruction not to edit the tests, so I agree with this PASS. The history gave useful background, but I cannot tell whether it changed the agent's decision, because the original instructions already forbade editing tests.

## My checks and reflections

I compared both diffs myself and found no extra out-of-scope changes. A PASS only means the change fits the request. It does not mean all tests pass, so the failing test in Run 2 has to be explained separately, as I did above.

I also built three cases on purpose: I edited the test file by hand, I added a scoring-formula change inside `game.js` next to the allowed string change, and I gave the checker no original instructions. The checker returned FAIL, FAIL and CANNOT JUDGE, as expected. The vague-instruction case ("Clean up the scoring code in game.js.") is described in ITERATION.md.

Both real tasks were small, and I did not run a comparison without the history search. So these runs cannot show that the history search improved the result, or that the checker handles larger changes reliably.

## Earlier prompt-log evidence

The following excerpts are copied from earlier project logs. They document repeated scope restrictions; they do not establish that an agent violated those restrictions. Source locations identify the original repository, file, and section.

- `inherited-game/prompt_log.md`, "Prompt 1: shuffle fix":

  > Replace only its implementation with a Fisher-Yates shuffle.
  > It must keep the same function name, signature and return type
  > (a new shuffled array; do not mutate the input if the original didn't).

- `inherited-game/prompt_log.md`, "Prompt 2: instructions visible by default":

  > Do not change the instruction wording.

- `liar-minesweeper/prompt_log.md`, "Step 2: board logic and tests":

  > Read SPEC.md first (do not edit it), then js/board.js. Keep the existing file structure, function names and signatures from the skeleton. Do not rename anything or rewrite other files.

These restrictions correspond to the checker's file-scope and behavior-preservation checks. The history tool exposes structured records from these earlier projects; its index contains commit messages, changed file names, and diff summaries. All current `prompt_log_excerpt` values are null, so the tool cannot supply documented reasons from those logs.
