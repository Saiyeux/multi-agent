# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-agent software development system powered by local LLMs (Ollama) that automates the complete development workflow from requirements analysis to product delivery.

**Runtime Environment**: MacBook Air M4, 24GB RAM, Python 3.10+, Ollama with qwen2.5:3b model

## Architecture

The system consists of three specialized agents coordinated by a central orchestrator:

1. **Architect Agent** (port 11434): Analyzes requirements, designs system architecture
2. **Developer Agent** (port 11435): Implements code and writes tests
3. **QA Agent** (port 11436): Runs tests, reviews code, packages releases

**Workflow**: User Requirement → Architect (requirements.md + architecture.md) → Developer (code + tests) → QA (test execution + packaging) → Deliverable

**Core Design Patterns**:
- `BaseAgent`: Abstract base class with async `chat()` method and abstract `process()` method
- `SharedMemory`: File-based workspace for agent collaboration (workspace/{requirements,design,code,tests,reports,releases})
- `DevOrchestrator`: State machine coordinator managing workflow transitions with retry logic
- `WorkflowState`: Enum tracking system state (INIT → ANALYZING → DESIGNING → CODING → TESTING → PACKAGING → COMPLETED/FAILED)

## Key Configuration

Configuration in `config.yaml`:
- Each agent gets dedicated Ollama instance with different temperature settings (architect: 0.7, developer: 0.3, qa: 0.5)
- Workflow settings: max_iterations (3), timeout_seconds (300), auto_fix (true)
- Models kept in memory with `keep_alive=-1` for performance

## Development Commands

```bash
# Setup Ollama instances (must be running before using the system)
bash scripts/setup_ollama.sh

# Run the development workflow
python -m src.main --requirement "your requirement here"

# Run tests
pytest tests/                    # Unit tests
pytest tests/integration/        # Integration tests
python tests/e2e_test.py        # End-to-end tests

# Launch web UI
streamlit run web_ui/app.py
```

## Project Status

This is a greenfield project. The CLAUDE.md file previously contained the design specification. The following implementation is needed:

**Phase 1 - Core Framework**:
- `src/agents/base_agent.py` - Abstract base with Ollama client integration
- `src/agents/{architect,developer,qa_engineer}.py` - Three concrete agents
- `src/core/shared_memory.py` - Workspace management system
- `src/orchestrator.py` - State machine coordinator
- `src/llm/ollama_client.py` - Ollama API wrapper
- `src/llm/prompts.py` - System prompts for each agent role

**Phase 2 - Tools**:
- `src/tools/code_executor.py` - Safe code execution sandbox
- `src/tools/test_runner.py` - Pytest wrapper
- `src/tools/linter.py` - Code quality checks (pylint/black)
- `src/tools/packager.py` - Zip/tar.gz creation

**Phase 3 - Infrastructure**:
- `scripts/setup_ollama.sh` - Multi-instance Ollama launcher
- `config.yaml` - System configuration
- `src/core/message_bus.py` - Inter-agent communication (optional)
- `src/core/workflow.py` - Workflow state management

**Phase 4 - Interface**:
- `web_ui/app.py` - Streamlit dashboard
- `src/main.py` - CLI entry point

## Important Implementation Notes

- All agents use **async/await** pattern for Ollama interactions
- The Developer agent must generate **runnable, testable code** - this is critical
- QA agent implements **retry loop**: failed tests trigger Developer to fix issues (max 3 iterations)
- Use `pathlib.Path` for all file operations in SharedMemory
- Agent prompts are in Chinese to match the design context
- The orchestrator's `run()` method returns a dict with status/package/report keys
- Workspace structure must be created on SharedMemory initialization
- Each agent receives the full context via `SharedMemory.get_context()` when needed

## Known Constraints

- qwen2.5:3b has limited reasoning capability - keep prompts simple and focused
- M4 MacBook can run 3 simultaneous instances but may be slow under heavy load
- Generated code requires human review before production use
- System does not currently support incremental/iterative development of large projects