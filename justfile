PORT := "8000"

default:
   just --list

# Install all dependencies including dev tools
@dev:
    uv sync

# Install pre-commit hooks
@hooks:
    pre-commit install

# Run formatting and linting checks
@check:
    pre-commit run --all-files

# Start development server with auto-reload
run port=PORT:
    uv run --frozen uvicorn src.main:app --reload --host 0.0.0.0 --port {{port}}

# Run tests
@test:
    uv run --frozen pytest -xvs tests

alias r := run
alias t := test
alias c := check
