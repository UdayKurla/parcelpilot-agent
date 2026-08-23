# 📦 ParcelPilot Support & Operations AI Agent

An enterprise AI support and operational intelligence system built for multi-tenant parcel logistics, authoritative contract-governed policy enforcement, SLA breach detection, and guarded human-in-the-loop actions.

---

## 🌟 Key System Capabilities

* **Strict Multi-Tenant Scoping**: Enforces tenant-level data isolation for customer roles (`ACCT-001` through `ACCT-004`) while granting elevated, multi-account analytical visibility to internal operations staff.
* **Deterministic Structured Data Engine**: Employs an embedded analytical DuckDB engine querying operational tables (`orders`, `accounts`, `tickets`). All duration deltas, delays, and SLA calculations are anchored to the fixed dataset snapshot timestamp (`2026-08-16 11:00 IST`).
* **Tiered Authority Conflict Resolution**: Evaluates operational and legal documents through an explicit precedence hierarchy:
  * **Tier 4 (Highest Authority)**: Customer-Specific Enterprise Agreements (custom waivers override baseline policies).
  * **Tier 3**: Active SOPs & Policies (`Support_Policy_v3_CURRENT`, `Cancellation_and_Service_Credit_SOP_v4`).
  * **Tier 2**: Product Operations Guide & Known Issues.
  * **Tier 1 (Context Only)**: Historical ticket resolutions.
  * **Tier 0 (Excluded)**: Deprecated policies (`Support_Policy_v2_DEPRECATED`) are excluded from active retrieval.
* **Two-Phase Human-in-the-Loop (HITL) Gatekeeper**: State-changing modifications (ticket escalations, fee waivers, cancellations) are staged with complete justifications and require explicit confirmation (`Confirm`) before execution.
* **Auditable Tool Execution Tracing**: Provides collapsible execution traces showing exact SQL parameters, returned data rows, and document excerpts.

---

## 🏗️ Technical Architecture

```text
                  +--------------------------------+
                  |    Streamlit Chat Interface    |
                  +--------------------------------+
                                  |
                   +--------------v---------------+
                   |    Agent Orchestrator Loop   |
                   |   (LangChain / Gemini Flash) |
                   +--------------+---------------+
                                  |
         +------------------------+------------------------+
         |                        |                        |
+--------v---------+    +---------v--------+    +----------v---------+
| Document Search  |    | SQL Operational  |    |   Staged Action    |
| (Tiered Authority|    | Data Engine      |    |   (2-Phase HITL    |
|  Precedence RAG) |    | (DuckDB Scoped)  |    |    Gatekeeper)     |
+------------------+    +------------------+    +--------------------+
```

---

## 📁 Repository Structure

```text
parcelpilot-agent/
├── app/
│   ├── __init__.py
│   ├── database.py         # DuckDB ingestion, tenant filtering & time calculations
│   ├── rag_engine.py       # PDF extraction & tiered precedence chunk ranker
│   ├── tools.py            # LangChain tool bindings (SQL, RAG, Action Staging)
│   └── ui.py               # Streamlit UI & multi-turn conversational loop
├── data/
│   ├── docs/               # Standard SOPs, customer agreements & operational guides
│   │   ├── 01_Support_Policy_v3_CURRENT.pdf
│   │   ├── 02_Support_Policy_v2_DEPRECATED.pdf
│   │   ├── 03_Cancellation_and_Service_Credit_SOP_v4.pdf
│   │   ├── 04_Product_Operations_Guide_and_Known_Issues.pdf
│   │   ├── 05_Northstar_Logistics_Enterprise_Agreement.pdf
│   │   └── 06_LumenWorks_Service_Agreement.pdf
│   └── ParcelPilot_Assessment_Data.xlsx # Operational orders, accounts & tickets dataset
├── notes/
│   ├── ARCHITECTURE_NOTE.md # Architectural decisions, data handling & isolation
│   └── PRODUCT_NOTE.md      # Problem selection, roadmap & North-Star metric
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Setup & Local Execution

### 1. Clone the repository
```bash
git clone https://github.com/UdayKurla/parcelpilot-agent.git
cd parcelpilot-agent
```

### 2. Set up virtual environment & dependencies
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure API Key
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 4. Launch the Streamlit application
```bash
streamlit run app/ui.py
```
Open `http://localhost:8501` in your browser.

---

## 🧪 Verification & Assessment Test Scenarios

* **Scenario 1: Contract Authority Precedence & Cancellation Waiver**
  * **Query**: `Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.`
  * **Result**: Checks the database status (`BOOKED`), evaluates standard SOP v4 (₹250 fee after 30 mins), and applies Tier 4 Enterprise Agreement Section 2 to waive the cancellation fee entirely.

* **Scenario 2: Carrier Fault SLA Delay & Credit Calculation**
  * **Query**: `A pickup is three hours late because of carrier fault. Should I get a service credit?`
  * **Result**: Confirms eligibility under SOP v4 (>2-hour carrier delay threshold) and identifies the applicable account-level monthly credit limit (₹5,000).

* **Scenario 3: Human-in-the-Loop Action Execution**
  * **Query**: `Please escalate ticket TKT-501 due to missed SLA.`
  * **Turn 1**: Calculates elapsed time relative to `2026-08-16 11:00 IST` (30 mins vs. 15-min P1 SLA), stages the escalation, and pauses for explicit user confirmation.
  * **Turn 2 (`Confirm`)**: Executes the escalation and logs notifications to senior management and the dedicated CSM.

---

## 🤖 AI Tool Usage Disclosure

* **Scaffolding & Architecture**: Used LLM coding assistance for initial DuckDB schema loaders, multi-turn LangChain tool execution handlers, and Streamlit session state management.
* **Validation**: Generated test edge cases to verify JSON parameter sanitation, NaN/null payload safety, and tenant data scoping.
