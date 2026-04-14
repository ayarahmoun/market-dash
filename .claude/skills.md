# Code quality preferences

- Write robust code, as simple as possible
- No emojis, ever
- Use `uv` for dependency management, not pip -- dependencies go in `pyproject.toml`
- Never create `requirements.txt` files
- Always use pre-commit with ruff and codespell: `uv run pre-commit install`
- Python 3.9+ compatible (`from __future__ import annotations` when needed)
- Prefer typed code with type hints

## Naming conventions

- Use `snake_case` for variables, functions, methods, modules
- Use `CamelCase` (PascalCase) for class names
- Use `UPPER_SNAKE_CASE` for constants
- No abbreviations unless universally understood (e.g. `df`, `idx`, `config`)

## Error handling

- Never use bare `except:` or broad `except Exception:`
- Catch specific exceptions (`except ValueError:`, `except KeyError:`, `except requests.HTTPError:`)
- Only add error handling where it adds value -- don't wrap every call

## Code style

- Keep it simple -- no premature abstractions, no over-engineering
- No unnecessary comments or docstrings on obvious code
- Follow Pydantic best practices when using data models
- Follow FastAPI best practices (lifespan events, response models, dependency injection)
- Keep functions short and focused
- Prefer flat code over deeply nested logic
