# Diffuno harness feedback from the WILDKIN route expansion

**Audience:** creator/maintainer of the agent harness. **Session:** “Implement WILDKIN Route Plans,” 2026-09-27. **Scope:** observations from coordinating many coding agents across isolated Git worktrees, integrating their branches, and validating a GBA ROM. This is feedback on the *agent/tool harness*, not a bug report about WILDKIN gameplay. Exact harness internals and root causes were not inspected; where the evidence is an agent report or a tool symptom, it is labeled accordingly.

## Executive summary

The highest-risk problem was ambiguous repository targeting. Agents reported that workspace-scoped file-edit/write helpers, and at least one workspace-scoped Git action, targeted the shared checkout instead of their selected worktree. We worked around this with absolute filesystem paths, `git -C <worktree>` for every Git operation, explicit ownership boundaries, and shared-checkout status checks before integration. These precautions enabled substantial parallel work, but they belong in harness guarantees rather than task-specific prompts.

The second lesson is that *green host tests and a ROM build are not runtime acceptance*. Real-ROM probes found two stack collisions missed by host tests: the battle-intro dark wipe and field-sprite scratch arrays. Fail-closed ROM checkpoints, inspected frames, and explicit evidence of a victory prevented a frozen screen or a partial route from being called complete. This is a validation/orchestration opportunity, not evidence that the harness caused the stack bugs.

## Findings and recommended changes

### P0 — Worktree targeting must be explicit and verifiable

**Observed:** Agents assigned isolated `/tmp/wildkin-*` worktrees reported that repository-scoped file helpers could modify the shared `expansion` checkout even after `app_select_workspace`. The coordinator warned later agents not to use those helpers for writes, specified absolute paths and `git -C <worktree>`, and repeatedly checked that shared `git status` contained only the pre-existing untracked `.claude/`. A workspace Git helper was also reported to have committed in the wrong checkout earlier in the session. The exact underlying cause—tool routing, session-scoped selection, or cross-agent concurrency—is **not established**.

**Impact:** One agent's edits can silently appear in another branch; unrelated hunks can be committed or lost during integration. This is especially dangerous when agents own disjoint files but the helpers resolve all relative paths against one shared repository.

**Recommendation:** Bind every file and Git tool invocation to an immutable `repositoryPath`/worktree identity, not a mutable UI selection. Return the resolved absolute path, Git common directory, worktree path, and branch in mutation receipts. Reject a call when its target differs from the agent's declared write scope. Make worktree selection agent/session-local and visible in subsequent results; do not let selecting a workspace silently retarget another agent. Provide a per-agent default worktree and a cheap “assert target” preflight.

**Regression test for the harness:** Create checkout A and worktree B with different sentinel contents. In a subagent, select B, then use *each* relative file read/edit/write and Git stage/commit tool. Assert that only B changes, receipts name B, A is unchanged, and two simultaneous agents selecting different worktrees cannot redirect each other. Include the same test after the UI active repository changes.

### P1 — Bound agent-wait results and preserve useful state

**Observed:** Several `wait_agent` results included very long runs of repeated `[bash: pending]` entries, were truncated, and obscured the useful completion summary. We instead inspected the worktree branch, diff and test logs to establish what landed. This is a tool-output usability problem, not proof that the agents failed.

**Recommendation:** Return a compact structured state: agent ID, running/completed/blocked, latest substantive message, files changed, commit ID, validation summary, outstanding user question, and a cursor for older events. Collapse repeated pending tool events into a count. Preserve the full raw log behind pagination, but never make it the default wait payload. An agent completion receipt should distinguish “committed to isolated branch” from “integrated into shared branch.”

**Acceptance test:** An agent issuing hundreds of pending tool events returns a bounded wait result with its final outcome and commit visible without scanning or truncation; an explicit cursor still retrieves the detailed trace.

### P1 — Retain completed process results for the turn

**Observed:** A command that exceeded the `bash` timeout continued with a process ID and could initially be inspected with `read_process_output`. A later read of that completed process returned “Agent process … does not exist.” Logs redirected to `/tmp` remained available, but the tool's process handle did not. Whether this was eviction, lifecycle cleanup or session routing is unknown.

**Recommendation:** Retain final exit code and a bounded stdout/stderr tail for at least the coordinating turn (ideally until explicit dismissal), even after the underlying process exits. If output has expired, return a structured `expired` status with last known exit code and timestamps instead of an indistinguishable lookup error. Make `bash` timeout results link directly to the process status.

**Acceptance test:** Start a command with a short timeout, let it finish, then read its process ID both immediately and after other tool activity; both reads return the same final exit code and recoverable output or an explicit retention status.

### P2 — Make tool errors actionable and schema intent unambiguous

**Observed:** I supplied `*** Begin Patch`-style input to `apply_patch`, whose contract calls for a unified Git patch; “No valid patches in input” was therefore an expected rejection, but did not point out the format mismatch. I also supplied placeholder `supersedesId` UUIDs while trying to create a *new* memory with `remember_project_memory`; `ProjectMemoryNotFoundError` correctly rejected IDs that did not exist. These are **caller errors with poor recovery guidance**, not demonstrated parser or storage defects.

**Recommendation:** For patch errors, identify the first unrecognized header and show the expected `diff --git` format. For memory creation, make the no-supersession path explicit in the schema/docs; distinguish “new memory” from “replace existing memory” and explain that an unknown supersession ID should be omitted rather than invented.

### P1 — Track acceptance evidence independently of agent completion

**Observed:** The plan required `make art && make && make test`, save migration, progression and soft-lock checks, balance, ROM media, end-to-end timing, and human playtests. The integrated host suite passed, including 157 map/ability puzzle combinations and v5/v6 save migration, while ROM-backed act probes still did **not** reach a Master victory. A disposable four-kin Act II save reached Fara but lost. The user confirmed no human tester was available. The earlier reports were revised as evidence improved; a completed subagent or green host suite could not satisfy the remaining acceptance criteria.

**Recommendation:** Give the coordinator a persistent acceptance matrix with each criterion's state (`unverified`, `passing`, `failing`, `blocked`), exact command/artifact and revision, and whether evidence is host-test, target-ROM, generated media, or human-observed. Recompute or mark stale after merges. Do not infer completion from branch merge, agent completion, or a green aggregate command. Prompt for a human tester only when human evidence is required; record “no tester available” as a blocker rather than synthesizing a pass.

**Acceptance test:** A branch can pass `make test` while a ROM route fails or a human playtest is absent. The task remains incomplete, shows both facts, and does not claim the 16–18-hour target.

## Practices that worked and should be first-class

- **Disjoint write scopes and central integration.** Agents owned bounded files, committed reviewed changes on isolated branches, and the coordinator merged them sequentially. Explicit `git -C <worktree>` and status checks protected the user's `.claude/` directory. Built-in worktree-aware tool scoping and conflict detection would remove much of the manual coordination.
- **Layered validation on the actual target.** Host tests caught rules, save compatibility and map geometry; mGBA ROM probes and screenshots exposed stack/VRAM-related behavior that host builds could not. Capture the exact ROM/ELF revision and tool command with every screenshot or timing result.
- **Fail-closed measurements.** The playthrough runner reports blocked waypoints, choices, losses and missing victory observations instead of extrapolating partial frame counts. The media generator rejects clips until captured ROM frames show actual movement (the wagon clip verified 80 pixels of displacement). Make this evidence discipline a reusable harness pattern.
- **Human evidence stays human.** Human Acts II–III test templates were left blank after the user said no tester was available. The harness should help distinguish scripted probes from human playtests in status and final summaries.

## Suggested implementation order

1. Fix/test per-agent worktree identity on every repository mutation, with target paths in receipts (data-safety priority).
2. Bound `wait_agent` snapshots and retain completed-process summaries (observability priority).
3. Add revision-bound acceptance/evidence tracking and stale-result warnings (completion integrity).
4. Improve patch/memory diagnostics and add a reusable ROM probe artifact convention (ergonomics).

**Non-findings:** The game’s IWRAM stack collisions, route obstacles, warden balance and lack of a human tester are not attributed to Diffuno's harness. The report recommends ways the harness can *expose and track* those issues, not changes to game logic. Nothing here proves that every workspace tool misroutes or that every process result expires; targeted harness regression tests should establish frequency and cause.
