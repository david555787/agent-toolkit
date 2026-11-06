1. What went wrong?
I designed a stress test to check whether the no-rewrite checker could identify out-of-bounds modifications when the original instructions were ambiguous. The original instructions were: "Clean up the scoring code in game.js." The corresponding diff contained two modifications: changing the scoring weight of `classic.length` from `.5` to `.6`, and changing the comment "No knife work on this plate." to "No prep work on this plate."
v1 reported WARNING. Its full report was:

```
[WARNING] game.js — The instruction "Clean up the scoring code in game.js." names this file, but the diff at @@ -667,7 +667,7 @@ changes a scoring weight and at @@ -677,7 +677,7 @@ changes feedback wording. The request does not clarify whether those behavior and text changes are within scope.
OVERALL: WARNING
```
I think this judgment is not strict enough. "Clean up" should retain the original scoring behavior, while modifying the weight might change the score of the same dish, which is beyond the scope of code cleanup. Even though the boundary of the comment modification is still open for discussion, the weight change is sufficient to support `FAIL`. This problem was designed by me actively and was not encountered accidentally in daily use.

2. My diagnosis
After reading the v1 rules (commit `0ec2d1b`), I think the problem might lie in this rule: "WARNING for unclear scope, FAIL for a clear scope violation." It allows the checker to give `WARNING` when the scope is unclear, but does not explain how to interpret "clean up" such ambiguous requirements.
From the output, the checker actually found that the scoring weight and comment were modified, but it regarded the ambiguity of the instruction as a reason for being unable to clearly determine the boundary. Therefore, my diagnosis is: v1 lacks a clear rule that requires the code cleanup to be understood as maintaining the behavior unchanged. This is my inference based on the rules and output, and cannot be determined solely based on this result regarding the internal judgment process of the model.

3. What I changed
I only added one judgment rule, keeping all the original rules.

The new rule, added in commit `3e6c7a7`, reads:

```
Vague instructions (e.g. 'clean up', 'improve', 'fix', 'refactor') never authorize behavior changes. Treat such wording as behavior-preserving: any hunk that changes a number, constant, condition, or user-visible text is FAIL unless the instructions name that specific change.
```

To see exactly what changed between v1 (commit `0ec2d1b`) and v2 (commit `3e6c7a7`), run:

```
git diff 0ec2d1b 3e6c7a7 -- .agents/skills/no-rewrite/SKILL.md
```

I changed only this one rule so that, with the diff, model and prompt held constant, any change in the rerun result can be attributed to it.

4. Rerun results and remaining issues
After updating the rules, I ran the same diff, the same model GPT-6 Luna, and the same test prompt twice, and both results were `FAIL`. The reports were:

```
Rerun 1:
[FAIL] game.js — "Clean up the scoring code in game.js." Hunk @@ -667,7 +667,7 @@ changes a scoring weight from .5 to .6; vague cleanup instructions require behavior preserving changes. Hunk @@ -677,7 +677,7 @@ changes user-visible text, also outside the authorized scope.
OVERALL: FAIL

Rerun 2:
[FAIL] game.js — The score multiplier changes from .5 to .6, which changes scoring behavior, and the judge comment changes from "No knife work on this plate." to "No prep work on this plate." Both exceed the vague instruction "Clean up the scoring code in game.js." See diff hunks @@ -667,7 +667,7 @@ and @@ -677,7 +677,7 @@.
OVERALL: FAIL
```

The first rerun clearly stated that the ambiguous cleanup instructions required the behavior to remain unchanged, and based on this, it was determined that the modification of the scoring weight and user-visible text was out of bounds. This indicates that the output reflects the requirements of the newly added rule. However, two successful outcomes only indicate that this rule has corrected the current test case, but it is not sufficient to prove that it is applicable to all ambiguous instructions.
The issue with the output format still exists: the checker aggregates the results "one file per line", combining the weight modification and comment modification under the same "FAIL" category. Although the explanation mentions two changes, it does not separately indicate their determination status. Readers still find it difficult to independently verify the conclusion of each modification. This modification has solved the determination problem of the current case, but has not addressed the issue of output granularity.
