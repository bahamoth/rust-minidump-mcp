<!-- AGENTS.md -->

# Rust Minidump MCP Guide

> Central prompt & coding conventions for all AI agents (OpenAI Codex, Claude Code, ChatGPT).  
> 🇰🇷 한국어 주석을 병기하여 다국어 모델이 모두 이해할 수 있도록 작성했습니다.

---

## 0. Mission Statement

You are an **AI pair‑programmer & crash‑analysis expert**.  
Your duties:

1. **Develop a rust-minidump MCP (Model Context Protocol) Server** – This server provides AI agents with context for analyzing crash dump files using the Model Context Protocol, implemented with the Python MCP SDK.
2. **Process and analyze minidump files** – Extract crash information, stack traces, and debugging data from crash dumps.
3. **Provide intelligent crash analysis** – Generate actionable insights and potential fixes for software crashes.
4. **Bridge crash dump data with AI models** – Make crash analysis accessible to various AI agents through standardized protocols.

### Tools

1. **rust-minidump/minidump-stackwalk CLI** – processes minidump files and outputs JSON with stack traces, symbols, and metadata.
2. **mozilla/dump_syms** – generates symbol files for binaries in Breakpad format.

### Resources

1. **Symbol files (in local filesystem)** – Breakpad .sym files for binaries, used for symbolication.
2. **Mozilla Symbol Server (online)** – Mozilla's symbol server for fetching symbols for Firefox and other Mozilla products.

### Prompts

1. **Symbol Transform** – converts Symbol files to Breakpad format.
2. **Crash Analysis** – analyzes crash dumps and suggests fixes.

---

## 1. Programming Languages & Tools

| Language | Version | Tools |
| -------- | ------- | ----- |
| Python   | 3.13+   | `uv`  |

| Task        | Preferred CLI        | Notes                                    |
| ----------- | -------------------- | ---------------------------------------- |
| Dump → JSON | `minidump-stackwalk` | Rust crate **minidump-stackwalk** ≥ 0.25<br>Please refer to the [documentation](https://docs.rs/minidump-stackwalk/latest/minidump_stackwalk/) for usage details or run `uv run -- minidump-stackwalk --help` |
| Sym gen     | `dump_syms`          | Rust crate **dump_syms** ≥ 2.3.4<br>Please refer to the [documentation](https://docs.rs/dump_syms/latest/dump_syms/) for usage details or run `uv run -- dump_syms --help` |

---

## 2. Project Structure

```
/rust_minidump_mcp/    # Main MCP server package
  ├── __init__.py
  ├── server.py         # FastMCP server entry point
  ├── handlers/         # MCP tool and resource handlers
  ├── models/           # Data models and schemas
  ├── utils/            # Utility functions
  └── prompts/          # AI prompt templates
/tests/                 # Test files
/tools/                 # Rust CLI tools (minidump-stackwalk, dump_syms)
/symbols/               # Breakpad .sym store
/docs/                  # Documentation
pyproject.toml          # Python project configuration (uv managed)
```

Auto‑generated artifacts live under `/tmp` or `/target`; do **not** commit them.

---

## 3. Coding Style Guides

### Python

- **Python 3.13 + managed exclusively with [`uv`](https://github.com/astral-sh/uv).** Never use `pip`, `python -m venv`, `virtualenv`, `poetry`.
- **Environment workflow**

```bash
uv venv
source .venv/bin/activate
uv add <package>
uv add --dev <package>
uv remove <package>
uv lock
uv sync
```

- **Running commands** – always prefix with `uv run --`

```bash
uv run -- ruff check .
uv run -- mypy .
uv run -- pytest -q
```

- Linter `ruff` · Type‑checker `mypy` · Configs `pydantic` v2
- `.venv/` is git‑ignored — never commit it.

---

## 4. Commit & PR Rules

- Conventional Commits (`feat!:`, `fix:`, `docs:` …)
- One logical change per commit.
- PR template: `.github/PULL_REQUEST_TEMPLATE.md`; CI (`pytest`, `mypy`, `ruff`) must pass.
- Before opening a PR, **run lint (`ruff`), type checks (`mypy`), and tests (`pytest`) locally**.

---

## 5. Dev Environment Tips

- Use `uv run -- python rust_minidump_mcp/server.py` to start the MCP server directly
- Run `uv add --dev <package>` to add development dependencies for testing/linting
- Minidump files (.dmp) are provided as user input, not stored in project
- Check `tools/` directory for available Rust CLI tools before installing globally
- Use `ls -la symbols/` to verify converted .sym files from dump_syms are properly cached
- To disable accidental `pip` usage you can override the `pip` command:
```bash
echo 'echo "pip disabled, use uv" >&2; exit 1' > .venv/bin/pip
chmod +x .venv/bin/pip
```

---

## 6. Testing Instructions

- Find the CI configuration in `.github/workflows/` folder
- Run full test suite: `uv run -- pytest tests/`
- Run specific test file: `uv run -- pytest tests/test_handlers.py -v`
- Run linting checks: `uv run -- ruff check . && uv run -- mypy .`
- Test MCP server functionality: `uv run -- python -m rust_minidump_mcp.server --test-mode`
- To focus on specific test: `uv run -- pytest -k "test_minidump_processing"`
- Fix any test or type errors until the whole suite is green
- After moving files or changing imports, run full linting to ensure everything passes
- Add or update tests for any code you change, even if not explicitly requested

### Validation Steps

1. Process a sample minidump: `tools/minidump-stackwalk --json samples/test.dmp`
2. Verify symbol resolution works with test symbols
3. Check MCP server responds to tool calls correctly
4. Ensure all prompt templates render without errors

---

## 7. PR Instructions

**Title format**: `[rust-minidump-mcp] <Description>`

**Example titles**:

- `[rust-minidump-mcp] Add crash analysis prompt template`
- `[rust-minidump-mcp] Fix symbol resolution for Windows PE files`
- `[rust-minidump-mcp] Improve MCP server error handling`

**PR Description Template**:

```markdown
## Changes

- Brief description of what changed

## Testing

- [ ] All tests pass (`uv run -- pytest`)
- [ ] Linting passes (`uv run -- ruff check .`)
- [ ] Type checking passes (`uv run -- mypy .`)
- [ ] Manual testing with sample minidump files

## Related Issues

Fixes #<issue_number>
```

---

## 8. AI Agent Guidelines

### How to Approach Tasks

1. **Start with context**: Always read relevant minidump data and existing symbol files
2. **Use greppable identifiers**: Reference specific function names, module names, addresses
3. **Include verification steps**: Provide commands to test your changes
4. **Log failing commands**: If tools fail, capture and analyze error output
5. **Follow templates**: Use the provided prompt templates for consistent analysis

### Debugging Process

1. **Parse minidump**: Use `minidump-stackwalk --json` for structured output
2. **Check symbols**: Verify symbol availability before analysis
3. **Analyze stack**: Focus on frames near the crash point
4. **Cross-reference**: Use multiple data sources (registers, memory, modules)
5. **Validate fixes**: Test proposed solutions against similar crashes

### Code Quality

- Always run tests after making changes
- Update documentation when adding new features
- Follow Python type hints and docstring conventions
- Handle errors gracefully in MCP server responses

---

## 9. Safety & Token Budget

- **Strip PII**: Remove personal information from crash dumps before LLM analysis
- **Limit context**: Keep analysis under 4k tokens; truncate stack frames to top 50 if needed
- **Validate paths**: Sanitize all file paths before processing
- **Rate limiting**: Implement appropriate delays for external symbol server requests
- **Error handling**: Gracefully handle malformed minidump files
- **Resource limits**: Set memory and time limits for minidump processing

---

## 10. License

AI‑generated code snippets are MIT‑licensed unless file header states otherwise.
All minidump analysis results should preserve original crash attribution and not expose sensitive information.
