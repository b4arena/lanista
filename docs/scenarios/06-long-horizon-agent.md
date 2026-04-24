# Scenario 06 — 8-hour autonomous coding agent

**TASK**: `run an autonomous coding agent for 8 hours of continuous refactoring work without human intervention`

**Dominant dimension**: long-horizon reliability (`gkisokay` T1 notes, `lm_hard`).
**Expected shape**: GLM-5.1 explicitly mentioned for 8-hour runs, Opus 4.7, GPT-5.x Codex.

## The isolated subagent's answer

---

### 1. claude-opus-4-7
Top-ranked on `lm_coding` (1527) and with a 1,000,000 `ctx` window, this model is well-suited to 8 hours of continuous autonomous refactoring where large context and code quality matter most [hn-47793411]. Recent reports about Claude Code quality issues were traced to harness bugs rather than the model itself, restoring confidence in Opus 4.7 for long-running agentic work [willison-2026-Apr-24-recent-claude-code-quality-reports].

### 2. gemini-3-1-pro
Strong `lm_coding` score of 1495 combined with the largest `ctx` of 1,048,576 and a relatively modest `price_$/Mtok` of 2.0/12.0 makes it ideal for 8-hour unattended runs where token volume compounds. Practitioner benchmarks positioned it as a Muse Spark / Opus 4.6 / GPT-5.4 peer on selected benchmarks [willison-2026-Apr-8-muse-spark].

### 3. claude-sonnet-4-6
Competitive `lm_coding` (1499) and `lm_long` (1485) at roughly half the `price_$/Mtok` (3.0/15.0) of the Opus tier, with a 1,000,000 `ctx` window that supports long refactor sessions without truncation. [no-opinion-match]

---

## Verdict

⚠️ GLM-5.1 is a **Tier 1 curated model explicitly flagged for "8-hour autonomous execution"** (per `lanista tier 1`), yet it did not surface here. The curated `gkisokay` tier notes are present in `lanista show` / `lanista tier` but are NOT injected into the `pick` prompt. This is a real picker gap — the T1 use-case notes are arguably the strongest signal for this exact question and they're missing from the prompt body.

## After batch 1 — gap closure

The `pick` prompt now carries `modalities`, `caps`, `tier` CATALOG columns
plus a dedicated **TIER 1/2 USE-CASE NOTES** block. Re-running the same
task with an isolated subagent (cold read of `/tmp/lanista-prompts/06.txt`):

### 1. claude-opus-4-7
Tier 1 note explicitly calls this out for "Complex external dev via Claude Code, multi-file refactoring" (`tier` 1) which aligns with 8-hour autonomous refactoring, and it has the top `lm_coding` score of 1527 in the catalog along with `caps` including `think` and `fn` for agentic tool use. Recent reports [willison-2026-Apr-24-recent-claude-code-quality-reports] confirm Claude Code harness issues (not the model) have been addressed, reinforcing confidence for long unattended runs.

### 2. glm-5-1
The `tier` 1 use-case note literally reads "Long-horizon agentic coding, sustained optimization loops" — a direct match for 8 hours of continuous unattended refactoring. It also posts a strong `lm_coding` of 1496 at moderate price (1.05/3.5 `price_$/Mtok`). [no-opinion-match]

### 3. mimo-v2-pro
The `tier` 2 note identifies this as an "Agent orchestration brain, custom OpenClaw workflows, long-context agent sessions" which fits an 8-hour autonomous loop, backed by a 1,048,576 `ctx` window for sustained refactoring over large codebases. Its `lm_coding` of 1477 is competitive among tier 2 options. [no-opinion-match]

**Verdict**: ✓ gap closed. GLM-5.1 now surfaces at #2, cited directly via
the TIER NOTES block. The picker still favors Opus 4.7 at #1 (defensible
given its top `lm_coding` score), but GLM-5.1 is no longer invisible.
