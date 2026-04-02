---
id: rule-017
trigger: "When any agent accesses, queries, or inspects any database or data store"
updated: "2026-04-01"
---

# Rule 017 — No Direct Database Access

<constraint>
Agents MUST NEVER access any database directly. ALL data reads and writes MUST go through the application's ORM, client library, or API layer. This rule applies inside `docker exec` containers as much as on the host — the restriction is on the operation, not the execution environment.
</constraint>

<why>
Direct DB access bypasses tenant isolation (rule-001), audit logging, and RBAC simultaneously. The security perimeter is the application layer, not the database engine.
</why>

<output>
When this rule is triggered, respond to the user with all three of the following:

**1. Why agents cannot do this**
Direct database access simultaneously bypasses three security controls that must hold together: tenant isolation (rule-001 — without it, one tenant can silently read another's data), RBAC (role checks only run through the application layer), and the audit log (writes that bypass the ORM leave no trace). This applies inside `docker exec` as much as on the host — the relevant boundary is the operation, not where it runs.

**2. Commands you can run yourself** (forbidden for agents; safe for you as the developer):
```bash
# PostgreSQL — read-only inspection
docker exec ai-platform-postgres psql -U aiplatform -d aiplatform -c "SELECT * FROM <table> LIMIT 20;"

# Redis — inspect a specific key
docker exec ai-platform-redis redis-cli GET <key>
docker exec ai-platform-redis redis-cli KEYS '<pattern>'

# Qdrant — list collections
curl http://localhost:6333/collections

# Plone — via REST API only (no direct ZODB access)
curl -u admin:admin http://localhost:8080/Plone/@search?portal_type=Document
```
If the data you need is not accessible through an existing API endpoint, ask the agent to add a read-only endpoint for it — that is the correct path.

**3. Before pasting any results into this chat**
Dev/test data and schema shapes are fine to paste: queryset reprs, small JSON objects (≤5 records), column/type descriptions, and data with placeholder values. Do NOT paste results containing: real email addresses, personal names, bulk record dumps (>10 rows), or production UUIDs that map to real users or tenants. That data in the chat window = unnecessary personal data in model context, a data minimisation risk under GDPR Art. 5(1)(c) [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) — which this rule is designed to prevent. Redact it first — replace real values with `<tenant_id>`, `<user_email>`, `<uuid>` before sharing.
</output>

<input_guard>
If the user's message appears to contain raw database output with PII, STOP immediately. Do not read, parse, quote, or process the suspected content further.

Trigger conditions (any one is sufficient):
- One or more email address patterns in the message (e.g. `user@domain.tld` — not in a code string or placeholder)
- Five or more UUID values in a single message (signals a bulk record dump)
- Credential field values: `password`, `secret`, `api_key`, `bearer `, `token` followed by a non-placeholder value (i.e. not `null`, `<placeholder>`, `"test_"...`)

NOT triggered by:
- Django queryset reprs: `<QuerySet [<Plugin object (1)>]>`, `<User: admin>`
- Small JSON with ≤5 records and no PII field values
- Schema/column/type descriptions: `{"columns": ["id", "tenant_id"], "types": ["uuid", "uuid"]}`
- JSON with obvious placeholder values: `<uuid>`, `null`, `0`, `"test_plugin"`
- Code that *queries* a DB (e.g. a Django ORM expression) — that is a code review, not a data paste

Prescribed response when triggered:
> "This message appears to contain unredacted database output with personal or tenant-identifying data. I cannot process this — it would put personal data into the model context unnecessarily — a data minimisation risk under GDPR Art. 5(1)(c) [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) that this rule is designed to prevent. Please redact all real IDs, emails, and personal data before sharing (replace with `<tenant_id>`, `<user_email>`, `<uuid>`), or describe what you need me to reason about in abstract terms."

Do not attempt to auto-redact. Do not quote back any part of the suspected content.
</input_guard>

## Forbidden patterns by database family

**Relational** (PostgreSQL, MySQL, MariaDB, SQLite, MSSQL, Oracle):
```bash
# ❌ All forbidden
psql -U aiplatform -d aiplatform
mysql -u root -p
sqlite3 app.db
sqlcmd -S localhost
pg_dump / pg_restore
make shell-postgres          # opens psql — forbidden for agents
# Reading .sql dump files to inspect live data
```

**Key-value / cache** (Redis, Memcached, DynamoDB):
```bash
# ❌ All data commands forbidden
redis-cli GET key
redis-cli KEYS '*'
redis-cli SCAN 0
redis-cli FLUSHDB
redis-cli MONITOR
memcached-tool localhost:11211 stats
aws dynamodb scan --table-name ...
aws dynamodb query --table-name ...
```

**Vector stores** (Qdrant, Chroma, Weaviate, Pinecone, Milvus):
```bash
# ❌ Direct REST/HTTP calls bypassing ai/rag/store.py are forbidden
curl http://localhost:6333/collections/my_collection/points
curl http://localhost:6333/collections          # data endpoints only
# Permitted: curl http://localhost:6333/health  (liveness probe only)
```

**Document / object stores** (Plone/ZODB, MongoDB, CouchDB, Elasticsearch):
```bash
# ❌ All forbidden
zodbtools info Data.fs
zopectl debug
mongosh / mongo
curl http://localhost:9200/my-index/_search
# Reading .Data.fs or .fs files directly
```

**Graph databases** (Neo4j, ArangoDB):
```bash
# ❌ All forbidden
cypher-shell -u neo4j
arangosh --server.endpoint ...
```

**Time-series** (InfluxDB, TimescaleDB):
```bash
# ❌ All forbidden
influx query 'from(bucket:"metrics") ...'
# psql on TimescaleDB — covered above
```

## Permitted exceptions

```bash
# ✅ Schema migration only — no data inspection
alembic upgrade head    # only via make migrate or docker exec in CI
make migrate

# ✅ ORM/API-mediated test fixtures
# In pytest conftest.py via SQLAlchemy async session
# Via API calls to http://localhost:8000/...

# ✅ Liveness probes only (no data access)
pg_isready -U aiplatform          # CI healthcheck only
curl http://localhost:6333/health  # service up/down only
```

<pattern>
```python
# ✅ Correct — data access through ORM
result = await db.execute(
    select(Plugin).where(Plugin.tenant_id == tenant_id)
)

# ❌ Forbidden — even inside docker exec
# docker exec ai-platform-postgres psql -U aiplatform -c "SELECT * FROM plugins"
# docker exec ai-platform-redis redis-cli KEYS '*'
```
</pattern>
