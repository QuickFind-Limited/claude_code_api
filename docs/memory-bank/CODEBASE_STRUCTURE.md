# Codebase Structure

## Directory Structure

```
/
├── .claude/                    # Claude Code configuration
├── .cursor/                    # Cursor IDE configuration
├── docs/
│   ├── flows/                  # Workflow documentation
│   ├── memory-bank/           # AIDD memory bank files
│   ├── rules/                 # Coding standards and rules
│   └── tasks/                 # Implementation task files
├── src/
│   └── claude_sdk_server/     # Main Python package
│       ├── __init__.py        # Package initialization
│       └── py.typed           # Type checking marker
├── test-aidd-project/         # Workspace member project
├── .gitignore                 # Git exclusion patterns
├── .mcp.json                  # MCP configuration
├── .python-version            # Python version specification
├── CLAUDE.md                  # Project instructions
├── README.md                  # Project documentation
├── pyproject.toml             # Project configuration
└── uv.lock                    # Dependency lock file
```

## Module Organization

- Main package: @src/claude_sdk_server/
- Single module structure with @__init__.py entry point
- Type checking enabled via @py.typed marker
- Workspace-based organization with @test-aidd-project member

## Key Files

- @pyproject.toml: Project metadata, dependencies, build system
- @uv.lock: Locked dependency versions
- @src/claude_sdk_server/__init__.py: Main module entry point
- @CLAUDE.md: AIDD development configuration
- @.python-version: Python 3.13 requirement
- @.mcp.json: MCP server configuration

## Dependencies

- Core: requests >= 2.32.4
- Build system: hatchling
- Package manager: uv
- Python version: >= 3.13

## Configuration Files

- @pyproject.toml: Project and build configuration
- @.python-version: Python version pinning
- @.mcp.json: MCP integration settings
- @.gitignore: Git exclusion patterns
- @uv.lock: Dependency lock file

## Test Structure

- No test directory currently present
- Tests should follow @tests/ structure
- Workspace member @test-aidd-project for testing scenarios

## Documentation Structure

- @docs/memory-bank/: AIDD memory files (ARCHITECTURE.md, PROJECT_BRIEF.md)
- @docs/rules/: Coding standards and constraints
- @docs/tasks/: Implementation task breakdowns
- @docs/flows/: Workflow documentation
- @README.md: Main project documentation
- @CLAUDE.md: AIDD configuration and commands

## Build Artifacts

- @__pycache__/: Compiled Python bytecode
- @build/: Build output directory
- @dist/: Distribution packages
- @wheels/: Wheel packages
- @*.egg-info: Package metadata
- @.venv: Virtual environment (if created)