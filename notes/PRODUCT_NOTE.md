# 📋 Product Note: ParcelPilot Support & Ops AI Agent

## 1. Additional Problem Tackled: Proactive SLA Breach & High-Priority Outage Detection
Beyond reactive question-answering, the agent addresses silent SLA breaches on critical operational incidents:
- **The Challenge**: When large-scale platform errors occur (e.g., ticket TKT-501 where all shipment creation fails), high-priority tickets often breach contract SLAs before agents notice.
- **The Solution**: The agent proactively correlates the customer contract tier (Tier 4 Northstar 15-minute P1 SLA) with the frozen operational clock (11:00 IST vs. 10:30 IST creation), staging escalations to senior support and assigned CSMs before compounding penalties accrue.

## 2. North-Star Metric
- **Metric**: **First-Contact Policy Resolution Rate (FCPR)**
- **Definition**: The percentage of support and operational inquiries resolved accurately in a single interaction without conflicting policy rollbacks, contract misinterpretations, or unauthorized state mutations.
- **Why It Matters**: In high-volume enterprise logistics, inaccurate fee assessments and delayed escalations lead directly to churn and unrecoverable service credit deductions.

## 3. Product Roadmap
- **Phase 1 (Immediate)**: Automated carrier webhook ingestion to dynamically trigger failed-pickup credit staging without requiring manual customer claims.
- **Phase 2 (Short-term)**: Integration with Slack/Teams for one-click interactive approval cards on staged HITL escalations.
- **Phase 3 (Mid-term)**: Proactive carrier reassignment suggestions when a carrier is experiencing pickup delays exceeding 90 minutes.

## 4. Conscious Trade-offs & Out-of-Scope Items
- **Autonomous Write Executions**: Full unguided database writes were explicitly scoped out in favor of a two-phase HITL gatekeeper to eliminate risk of erroneous fee waivers.
- **Dynamic Live Clock vs. Pinned Snapshot**: Live datetime lookups were locked to the reference snapshot timestamp to guarantee reproducible evaluation and strict test determinism.