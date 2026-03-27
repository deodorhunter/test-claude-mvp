## 1. Overview

This is an **enterprise-grade AI orchestration platform MVP** designed for multi-tenant organizations. Key features include:

- Multi-model support (Anthropic Claude, GitHub Copilot/Enterprise models)
- Plugin-based architecture (hot-pluggable per tenant)
- Retrieval-Augmented Generation (RAG) via LlamaIndex
- MCP (Model Context Protocol) integration with **trust scoring**
- Multi-tenant isolation with **user-level RBAC**
- Dockerized and Kubernetes-ready deployment
- Cost-aware model selection and multi-model fallback
- Token quota and cost control per tenant
- Audit logging for compliance with GDPR and EU AI Act

This system is designed to be modular, extensible, and future-proof for enterprise adoption.

For MVP purposes, the system will interact with a Ollama inside the container for demo mode. External providers should be nonetheless mocked and potentially usable. We restrict the providers to Claude with optional API key configuration for demo-api mode.

The system must integrate a working demo with a Plone 6 backend and Volto frontend on the same docker network. Use cookiecutter for this.

The demo mvp is considered complete when:

- A logged in Plone user in Volto can chat with an agent that builds blocks for him in a given Page Content Type.
- A logged in Plone user in Volto can chat with an agent for getting help integrating blocks and things from site specific documentation with RAG, hosted in a non core plugin addon
- A logged in Plone user in volto can upload a document to a chat agent, that builds for him a Page Content type with just text from the document.

---

## 2. Technical Stack

**Backend:** Python, FastAPI , Plone
**Frontend:** Volto, React, Typescript
**AI Framework:** LlamaIndex (for RAG and document ingestion)  
**Infra:** Docker, Kubernetes, Redis (rate limiting and queueing), PostgreSQL (main DB), Qdrant (vector database)  

---

## 3. High-Level Architecture

User Request
↓
Authentication (JWT / OAuth)
↓
Tenant Resolver
↓
RBAC Enforcement (user-level)
↓
Planner (cost-aware + multi-model fallback)
↓
Execution Graph (nodes: tools, models)
↓
Orchestrator
↓
Model Execution + Plugins + MCP Servers
↓
Response to User

---

## 4. Multi-Tenancy

Challenges: this has to integrate with virtually any third party auth. For the mvp goal, you have to be able to ratelimit specific plone users, that log in with username and password from the Plone site. Each user has to communicate its Plone role to the tenant specific plugin and each user in Plone will have a rate limit based on role.

- Tenants correspond to organizations, each with multiple users.
- All entities (documents, queries, plugins, MCP results, tokens) are tenant-scoped.
- Isolated runtime environments per tenant for plugins and models.
- Database schema examples:

```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name TEXT,
    plan TEXT
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email TEXT,
    role TEXT -- admin, member, guest
);

CREATE TABLE tenant_plugins (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    plugin_name TEXT,
    enabled BOOLEAN,
    config JSONB
);

CREATE TABLE tenant_token_quota (
    tenant_id UUID REFERENCES tenants(id),
    max_tokens INT,
    tokens_used INT,
    reset_date TIMESTAMP
);

````

---

## 5. Authentication

- JWT-based with OAuth integration for Slack, GitHub, etc.
- Token payload includes:

  - user_id
  - tenant_id
  - roles
- Expiration and refresh tokens enforced
- All traffic over HTTPS

---

## 6. RBAC (Role-Based Access Control)

Challenges: this has to integrate with virtually any third party auth. For the mvp goal, you have to be able to ratelimit specific plone users, that log in with username and password from the Plone site. Each user has to communicate its Plone role to the tenant specific plugin and each user in Plone will have a rate limit based on role. You will likely have to write a specific plugin named PloneIntegration or something similar.

- Permissions applied **per user per tenant**
- Examples:

  - `plugin.enable` / `plugin.disable`
  - `query.execute`
  - `admin`
  - `mcp.query`
- Enforced at API level **before executing requests or plugin actions**

---

## 7. Plugin System

- Plugins are **hot-pluggable per tenant**, can be enabled/disabled at runtime without global reload.
- Plugin runtime manager is **tenant-aware**:

  - Each tenant has its own active plugin instances
  - Plugins cannot access other tenants’ data
- Manifest required (`manifest.yaml`) with:

  - id
  - version
  - capabilities
  - entrypoint
- MVP assumption: **plugins are trusted** (whitelisted)
- Future enterprise: sandbox execution or container isolation

---

## 8. Model Layer

- Supported providers:

  - Anthropic Claude
  - GitHub Copilot / Enterprise models
- Each model must implement `generate(prompt, context)`
- Multi-model fallback:

  - Primary model chosen per tenant and request
  - Fallback model automatically selected if primary unavailable, over budget, or rate-limited

---

## 9. Planner (Cost-Aware & Multi-Model Fallback)

- Creates execution graph with nodes of type `model` or `tool`
- **Cost-aware**:

  - Evaluates token cost and licensing per model
  - Selects optimal model according to tenant budget and quota
- **Fallback logic**:

  - Secondary or specialized models used if primary unavailable or over cost
  - MCP servers and plugins injected according to trust and cost
- Parallelization supported with tenant isolation

---

## 10. MCP Integration & Trust Layer

- MCP servers registered in **MCPRegistry**
- Each MCP server has trust score (0–1):

  - `internal_docs`: 0.95
  - `official_api`: 0.9
  - `github`: 0.7
  - `web`: 0.4
- Context builder:

  - Queries MCP servers
  - Filters results below minimum confidence
  - Formats context with source attribution
- Audit logging for all MCP queries
- Sanitization applied to prevent prompt injection or malicious content

Example:

```python
class DocsMCP(MCPServer):
    async def query(self, input_text):
        results = search_docs(input_text)
        return {"data": results, "source": "internal_docs", "confidence": 0.95}
```

---

## 11. Context Assembly

- Combines:

  - MCP server output
  - Plugin/tool responses
  - RAG embeddings
- Formats context as plain text including:

  - source
  - confidence
- Sanitizes outputs to prevent:

  - malicious code execution
  - prompt injection

---

## 12. Token Quota & Cost Control

- Token usage tracked per tenant and users under tenant
- Limits applied per model and request
- Planner adjusts model selection to respect quota
- Optional alerting if tenant approaches limit

---

## 13. Audit Logging

- All actions logged with:

  - user_id, tenant_id, action, resource, timestamp, metadata
- Includes:

  - Plugin activation/deactivation
  - Model query execution
  - MCP server queries

---

## 14. Rate Limiting

- Redis-based per user and tenant
- Prevents abuse and API overload, or double same/similar propmt submission
- Integrated with token quota enforcement

---

## 15. Security

- HTTPS required
- Secrets never stored in code
- RBAC enforced across all operations
- Plugin isolation:

  - subprocess execution
  - CPU/memory/time limits
- Sanitization and validation for MCP output
- Multi-tenant isolation enforced at runtime

---

## 16. Docker & Kubernetes Deployment

- Services:

  - API server
  - Worker / Orchestrator
  - Redis
  - PostgreSQL
  - Qdrant
- Resource limits per tenant for CPU/memory
- Supports hot-plug plugins and tenant-aware orchestration

---

## 17. Non-Goals (MVP)

- User-uploaded plugins
- Fine-tuning of models
- Advanced agent loops
- Full MCP ecosystem beyond trusted sources

---

## 18. Roadmap / Next Steps

1. Enterprise MCP server deployment (cost-aware and delegation)
2. OAuth integrations (Slack, GitHub)
3. Plugin sandboxing / isolation
4. Billing system per tenant
5. Multi-model fallback improvements
6. Token quota enforcement per tenant and user
7. Policy engine for source filtering and trust

---

## 19. Output Specification

- Responses must include:

  - Context from MCP, plugins, and RAG
  - Source attribution
  - Confidence
  - Fallback model indication if primary model unavailable
- Example output format:

Response:
[Fonte: internal_docs | confidence: 0.95]
...
[Fonte: github | confidence: 0.7]
...

---

## 20. Notes on Security & Compliance

- Docker hardening alone is insufficient
- Trusted plugin assumption for MVP
- Enterprise requires sandboxed plugin execution
- All tenant data isolated in runtime and storage
- Logging and source attribution required for GDPR and EU AI Act compliance
