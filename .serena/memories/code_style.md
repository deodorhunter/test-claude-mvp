# Code Conventions
Python: type hints on all public functions, SQLAlchemy 2.x (select() not session.query())
Async: asyncio_mode = "auto" — no @pytest.mark.asyncio needed
Tenant: every DB query must include .where(Model.tenant_id == tenant_id)
Commits: type: description (feat/fix/chore/docs/refactor/test)