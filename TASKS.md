# PyPI Publishing Tasks

## ✅ Phase 1: TestPyPI Publishing Setup (COMPLETED)
- [x] Create GitHub issue #20 for PyPI publishing
- [x] Create and checkout branch `feature/pypi-publishing`
- [x] Update pyproject.toml with PyPI metadata
  - [x] Add license field
  - [x] Add project URLs
  - [x] Add keywords
  - [x] Add classifiers
  - [x] Add TestPyPI index configuration
- [x] Build package with `uv build`
- [x] Publish to TestPyPI with `uv publish`
- [x] Verify installation from TestPyPI
- [x] Test uvx execution from TestPyPI

## ✅ Phase 1.5: Prompt System Refactoring (COMPLETED)
- [x] Rename existing prompt files for clarity
  - [x] crash_analyzer.md → analyze_stackwalk_result.md
  - [x] stack_interpreter.md → interpret_stack_frames.md
  - [x] exception_decoder.md → decode_exception_info.md
  - [x] symbol_advisor.md → evaluate_symbol_quality.md
- [x] Update crash_analysis_provider.py method names
- [x] Modify evaluate_symbol_quality.md to remove Windows-specific content
- [x] Create new prompts
  - [x] Create symbol_preparation_provider.py
  - [x] Create prepare_symbols_for_analysis.md
  - [x] Create crash_workflow_provider.py
  - [x] Create analyze_crash_end_to_end.md
- [x] Update server.py with new providers and method names
- [x] Update documentation (CLAUDE.md, README.md)
- [x] Test all prompts functionality

## ✅ Phase 1.6: CLI Enhancement - MCP Client Features (COMPLETED)
- [x] Create client.py with MCPClient class
  - [x] Implement list_tools/list_prompts methods
  - [x] Implement describe_tool/describe_prompt methods
  - [x] Implement call_tool/call_prompt methods
  - [x] Implement interactive_session method
- [x] Update cli.py with new subcommand structure
  - [x] Add client subcommands (list-tools, list-prompts, etc.)
  - [x] Maintain backward compatibility with existing client command
  - [x] Add parameter parsing for tool/prompt calls
- [x] Improve settings configuration
  - [x] Add settings_customise_sources to ServerSettings
  - [x] Add settings_customise_sources to ClientSettings
  - [x] Remove manual environment variable manipulation
- [x] Add rich output formatting
  - [x] Format tool/prompt listings
  - [x] Format execution results
  - [x] Add progress indicators
- [x] Test new client functionality
  - [x] Test all new commands
  - [x] Verify prompt execution (especially new ones)
  - [x] Test error handling

## 🚀 Phase 2: Release Please Integration
- [x] Install and configure release-please-action
  - [x] Create `.github/workflows/release-please.yml`
  - [x] Configure for Python project type
  - [x] Set up conventional commits parsing
  - [x] Configure changelog generation
- [x] Update pyproject.toml version to use release-please
- [x] Configure version bumping in `pyproject.toml` and `uv.lock`
- [ ] Test release creation with different commit types
  - [ ] feat: minor version bump
  - [ ] fix: patch version bump  
  - [ ] feat!: major version bump
- [ ] Verify automated PR creation and merging

## 📋 Phase 3: GitHub Actions for Publishing
- [ ] Create `.github/workflows/publish.yml` workflow
  - [ ] Trigger on release published (created by release-please)
  - [ ] Build package on multiple Python versions
  - [ ] Generate SBOM (Software Bill of Materials)
  - [ ] Upload artifacts
  - [ ] Publish to TestPyPI first (with `TESTPYPI_API_TOKEN` secret)
  - [ ] Publish to PyPI (with `PYPI_API_TOKEN` secret)
- [ ] Add GitHub repository secrets
  - [ ] Add `TESTPYPI_API_TOKEN`
  - [ ] Add `PYPI_API_TOKEN`
- [ ] Test workflow with release-please generated release
- [ ] Verify both TestPyPI and PyPI deployment

## 📦 Phase 4: Production PyPI Publishing
- [ ] Create PyPI account at https://pypi.org
- [ ] Generate PyPI API token
- [ ] Add `PYPI_API_TOKEN` to GitHub secrets
- [ ] Update release workflow to publish to PyPI
  - [ ] Add production PyPI publishing step
  - [ ] Configure to run only on release tags
- [ ] Test complete release cycle
  - [ ] Create release via release-please
  - [ ] Verify GitHub Actions builds and publishes
  - [ ] Confirm package available on PyPI
- [ ] Update documentation
  - [ ] Update README with PyPI installation instructions
  - [ ] Remove TestPyPI references from user docs
  - [ ] Add badge for PyPI version

## 🔧 Phase 5: Post-Release Improvements
- [ ] Add automated testing of published package
- [ ] Set up vulnerability scanning
- [ ] Configure Dependabot for dependency updates
- [ ] Add download statistics tracking
- [ ] Create announcement template for releases

## 📝 Notes
- Current version: 0.1.0
- Package name: `rust-minidump-mcp`
- TestPyPI URL: https://test.pypi.org/project/rust-minidump-mcp/
- Dependencies require `--extra-index-url https://pypi.org/simple/` for TestPyPI

## 🔑 Environment Variables
- `UV_PUBLISH_TOKEN`: API token for publishing
- `UV_PUBLISH_URL`: Custom publishing URL (for TestPyPI)
- `UV_INDEX_URL`: Package index URL

## 📚 Resources
- [uv publish documentation](https://docs.astral.sh/uv/guides/publish/)
- [release-please documentation](https://github.com/googleapis/release-please)
- [PyPI publishing guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)