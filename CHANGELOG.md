# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-21

### Added
- Initial release consolidating three projects:
  - `claude-hooks-core` - Base library for session state management
  - `graphiti-claude-integration` - Graphiti memory hooks
  - `shared-claude-rules` - Guards and STAN.FLUX rules
- 14 hooks across 4 event types (session-start, user-prompt-submit, pre-tool-use, post-tool-use)
- 30+ rules including STAN.FLUX, git workflows, and MCP configurations
- Unified installer with global and project-specific installation
- Comprehensive test suite (Python pytest + Bash installer tests)
- Credential detection with 903 patterns
- Citation and version validation for technical learnings

### Migration from Previous Projects
- `npx graphiti-claude-integration` -> `npx taming-stan`
- `npx shared-claude-rules` -> `npx taming-stan`
- All hooks and rules merged into single installation
