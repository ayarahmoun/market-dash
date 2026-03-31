# Code quality preferences

- Write robust code, as simple as possible
- No emojis, ever
- Always use pre-commit with codespell and ruff
- Keep code consistent across all projects
- Follow Pydantic best practices when possible
- Follow FastAPI best practices (lifespan events, proper response models, dependency injection)
- Use `uv` for dependency management, not pip
- Python 3.9+ compatible (`from __future__ import annotations` when needed)
- Prefer typed code with type hints
