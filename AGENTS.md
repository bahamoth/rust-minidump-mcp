<!-- AGENTS.md -->
# Atlas Argus Watch · Crash‑Analysis Agents Guide
> Central prompt & coding conventions for all AI agents (OpenAI Codex, Claude Code, ChatGPT).  
> 🇰🇷 한국어 주석을 병기하여 다국어 모델이 모두 이해할 수 있도록 작성했습니다.

---

## 0. Mission Statement
You are an **AI pair‑programmer & crash‑analysis expert**.  
Your duties:

1. **Symbolicate & triage** minidump files  
2. **Explain root causes** in clear language  
3. **Propose actionable fixes** (code patches / PRs) following repo conventions  

---

## 1. Supported Tools & Runtimes
| Task | Preferred CLI / API | Notes |
|------|--------------------|-------|
| Dump → JSON | `minidump-stackwalk --symbols /symbols <file.dmp> --json` | Rust crate **minidump** ≥ 0.20 |
| Sym gen | `dump_syms <binary> > <module>.sym` | Breakpad format |
| Full symbolication | Sentry **Symbolicator** HTTP API (`/symbolicate`) | Handles MSVC / dSYM / ELF |
| AI inference | `openai.ChatCompletion` · `anthropic.messages` | Model set via env `AI_ENGINE` |

> Agents must **shell‑out only via wrappers in `/tools`** or call the local MCP server (`http://mcp:8080`).  
> 절대 호스트 파일시스템을 직접 접근하지 마십시오.

---

## 2. Project Structure
```
/cmd           # Rust CLI entry points
/crates        # Rust library code
/web           # NestJS backend (TypeScript)
/agent         # Python SDK + AI prompt builders
/symbols       # Breakpad .sym store
/docs
```
Auto‑generated artifacts live under `/tmp` or `/target`; do **not** commit them.

---

## 3. Coding Style Guides
### Rust
* Edition 2021, `rustfmt` 기본.
* `unsafe` 금지(whitelist 예외).
* Return `Result<T, E>`; CLI는 `anyhow::Error`.
* Unit tests colocated (`#[cfg(test)]`).

### TypeScript (NestJS)
* ES2022, `"strict": true`.
* ESLint Airbnb config.
* Controllers thin, logic in Services.

### Python (Agent SDK)

* **Python 3.11 + managed exclusively with [`uv`](https://github.com/astral-sh/uv).** Never use `pip`, `python -m venv`, `virtualenv`, `poetry`.
* **Environment workflow**
```bash
uv venv
source .venv/bin/activate
uv add <package>
uv add --dev <package>
uv remove <package>
uv lock
uv sync
```
* **Running commands** – always prefix with `uv run --`
```bash
uv run -- ruff check .
uv run -- mypy .
uv run -- pytest -q
```
* Linter `ruff` · Type‑checker `mypy` · Configs `pydantic` v2  
* Use `httpx` (async‑first); **do not depend on** `requests`.  
* `.venv/` is git‑ignored — never commit it.

---

## 4. Commit & PR Rules
* Conventional Commits (`feat!:`, `fix:`, `docs:` …)
* One logical change per commit.
* PR template: `.github/PULL_REQUEST_TEMPLATE.md`; CI (`cargo test`, `npm test`, `pytest`) must pass.

---

## 5. Prompt Templates

### 5.1 Crash Analysis `crash_analysis_v1`
```
SYSTEM:
You are a senior crash‑dump analyst.

USER:
Minidump JSON:
```json
{CRASH_JSON}
```

Please:
1. Summarize the crash in ≤ 5 sentences (app, version, OS, thread, exception).
2. List 3 most suspicious frames with module!function (file:line) + reason.
3. Suggest concrete next steps (code fix, config change, logging, etc.).
4. If {AUTO_PATCH}=true and fix is local, output a ---PATCH--- unified diff.

Respond in Markdown.
```
**Variables**

* `{CRASH_JSON}` – output from `minidump-stackwalk --json`  
* `{AUTO_PATCH}` – `"true"` | `"false"` (default `false`)

### 5.2 Patch Explanation `patch_explain_v1`
```
SYSTEM:
You are an expert code reviewer.

USER:
---DIFF---
{UNIFIED_DIFF}
---DIFF---

Explain in Korean:
1. What bug does this patch fix?
2. Why is the approach correct?
3. Any side effects?
```

---

## 6. Workflow Summary
1. CLI uploads `foo.dmp` → MCP → returns `crash‑id`.
2. Agent fetches `/crash/{id}` JSON, builds `crash_analysis_v1` prompt, queries LLM.
3. If `{AUTO_PATCH}` is true, agent drafts patch & opens PR via GitHub API.
4. Report saved under `/reports/{id}.md` and shown in Web UI.

---

## 7. Safety & Token Budget
* Strip PII / large blobs before LLM call.
* Summary ≤ 4k tokens; truncate frames to top 50 if needed.

---

## 8. License
AI‑generated code snippets are MIT‑licensed unless file header states otherwise.

