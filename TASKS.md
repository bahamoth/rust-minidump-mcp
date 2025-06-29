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