# 🏛️ Architecture Note: ParcelPilot Support & Ops AI Agent

## 1. System Topology & Component Interactions
The ParcelPilot AI Agent integrates an LLM-driven reasoning loop with deterministic data access and structured document retrieval:
- **Presentation Layer (`app/ui.py`)**: Built with Streamlit, handling session state, chat rendering, dynamic tenant/role selector context, and execution trace auditing.
- **Orchestration Layer (`app/tools.py`)**: Defines deterministic tool bindings consumed by Gemini via LangChain function calling.
- **Data Ingestion & Analytical Engine (`app/database.py`)**: DuckDB analytical store ingesting `ParcelPilot_Assessment_Data.xlsx` on launch. Provides fast in-memory SQL querying with tenant-level multi-account isolation.
- **Hierarchical Knowledge Engine (`app/rag_engine.py`)**: PDF text extractor and metadata ranker managing tiered source precedence.

## 2. Data Handling & Temporal Consistency
- **Snapshot Reference Pinning**: The operational state is strictly anchored to **2026-08-16 11:00 IST**. All relative duration calculations (delay times, SLA breaches, pickup windows) evaluate against this pinned timestamp rather than host system time.
- **JSON Serialization & Payload Sanitization**: DuckDB outputs convert empty timestamps and missing values into standard JSON-compliant formats (`None` / `null`), preventing NaN-related deserialization failures.

## 3. Conflict Resolution & Source Authority Model
The retrieval pipeline strictly resolves contradictions across company documentation using an explicit four-tier authority hierarchy:
1. **Tier 4 (Highest Precedence) – Customer Enterprise Agreements**: Overrides baseline SOPs (e.g., Northstar Enterprise Agreement Section 2 fully waives cancellation fees for booked shipments regardless of time elapsed).
2. **Tier 3 – Active SOPs & Policies**: Defines default operations rules (`Support_Policy_v3_CURRENT`, `Cancellation_and_Service_Credit_SOP_v4`).
3. **Tier 2 – Product Operations & Known Issues**: Explains temporary system bugs and operational workarounds.
4. **Tier 1 – Historical Tickets**: Used purely as conversational resolution reference; cannot override formal policies.
5. **Tier 0 – Deprecated Policies**: `Support_Policy_v2_DEPRECATED` is quarantined and excluded from active retrieval.

## 4. Multi-Tenant Scoping & Security Isolation
- When `Active Role Context` is set to `customer`, query parameters automatically append tenant filters (`WHERE account_id = ?`).
- Customer tenants are prevented from querying or viewing unauthorized account data, orders, or tickets.
- Internal `operations` and `support_lead` roles bypass single-tenant filters to perform cross-account impact assessments and queue-wide triage.

## 5. Human-in-the-Loop (HITL) State Mutation Guardrails
- State-changing operations (such as ticket escalations, policy overrides, or fee waivers) use a two-phase staging workflow.
- **Phase 1 (Staging)**: The agent computes the rationale, identifies SLA breaches, and presents a structured confirmation proposal.
- **Phase 2 (Execution)**: The action is only dispatched once the human user explicitly responds with `Confirm`.