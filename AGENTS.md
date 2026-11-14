# Repository Guidelines

## Project Structure

The repository currently contains `DOCS.md`, a Portuguese brief for a DevOps and generative AI exercise. It describes a Python application with an intentional failure, automated tests, CI/CD, and AI-assisted log analysis. Source code, tests, assets, and pipeline configuration have not yet been added. Keep the brief as the reference for the exercise; document new directories as they are introduced.

## Development and Testing

There are currently no configured build, test, or run commands. When adding the application, document its Python version, dependencies, setup, and exact local test command in a README. Place automated tests in a clearly named test directory and configure the same checks in the CI pipeline. Preserve the intentional failure only where the exercise requires it, and explain how to reproduce and resolve it.

## Style and Changes

Follow the formatting and naming conventions established by the code as it is added. For Python, use four spaces for indentation, descriptive `snake_case` names for functions and variables, and `test_*.py` for test files. Add formatter or linter commands to the README if those tools are configured.

## Commits and Pull Requests

No Git history is available here to establish a commit convention. Write concise, imperative commit subjects that describe the change. For pull requests, explain the purpose, testing performed, and any intentional failure; link the relevant issue when available. Include screenshots or sanitized logs when they help reviewers understand pipeline or AI analysis results.

## Security and AI Review

Never commit credentials or expose sensitive data in screenshots and logs. Review and test AI-generated diagnoses and suggested fixes before applying them. Record relevant AI feedback and pipeline evidence for the exercise.

## Agent Instructions

Follow the applicable instructions in `C:/Users/renat/.codex/RTK.md`, including the requirement to prefix shell commands with `rtk`.
