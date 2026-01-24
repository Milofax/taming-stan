## Acceptance Criteria

- [x] Code is syntactically correct
- [ ] All tests pass
- [ ] Documentation is updated
- [x] No hardcoded values

## Test Code

```python
def hello():
    print("Hello World")  # TODO: Make this configurable

# WORKAROUND: type:prompt hooks need session restart after config change
# This was discovered after hours of debugging - the hook runs silently
# until you restart the Claude Code session
#
# GOTCHA: Never request JSON output format in prompt hooks!
# Wrong: "Return {continue: true, systemMessage: '...'}"
# Right: Just give analysis instructions, system handles the rest
#
# LEARNING: type:prompt hooks need session restart to take effect
# Changes to .claude/settings.json are NOT hot-reloaded
#
# TEST: Does $TRANSCRIPT_PATH give the hook session context?
```
