"""Deterministic Multi-Tenant Graph Seeding Script for NexusGraph.

Seeds two isolated tenant graphs:
1. nexus_acme_corp (Full multi-track production topology)
2. nexus_finserve_io (Isolated fintech topology proving multi-tenant separation)

Validates all 3 Hackathon tracks:
- Track 1: Agents That Act on Connected Data (Dependency topology, Commits, Incidents, PageRank)
- Track 2: Agent Memory & Coordination (Episodes, Procedures, Multi-agent Handoffs)
- Track 3: Company Brain (People, Teams, Expertise, ADR/RFC Decisions, Source Attribution)
"""

import logging
import sys
from typing import Dict, Any
from backend.db.client import FalkorDBManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_graph")


def seed_acme_corp(manager: FalkorDBManager) -> Dict[str, Any]:
    """Seed the primary tenant graph nexus_acme_corp."""
    tenant = "acme_corp"
    logger.info(f"--- Seeding graph: nexus_{tenant} ---")

    # Clear any previous data for deterministic repeatability
    manager.delete_tenant_graph(tenant)
    graph = manager.get_graph(tenant)

    # -------------------------------------------------------------
    # TRACK 1: CONNECTED SYSTEMS (Services, Dependencies, Commits, Incidents)
    # -------------------------------------------------------------
    logger.info("Creating Track 1: 8 Microservices and dependency topology...")
    services_cypher = """
    CREATE (gw:Service {name: 'api-gateway', tier: 1, language: 'Go', repo: 'acme/api-gateway', health: 'HEALTHY'}),
           (auth:Service {name: 'auth-service', tier: 1, language: 'Rust', repo: 'acme/auth-service', health: 'HEALTHY'}),
           (checkout:Service {name: 'checkout-service', tier: 1, language: 'TypeScript', repo: 'acme/checkout-service', health: 'DEGRADED'}),
           (pay:Service {name: 'payment-worker', tier: 1, language: 'Python', repo: 'acme/payment-worker', health: 'DEGRADED'}),
           (redis:Service {name: 'redis-session-cache', tier: 2, language: 'C', repo: 'acme/redis-cluster', health: 'HEALTHY'}),
           (ledger:Service {name: 'ledger-db', tier: 1, language: 'PostgreSQL', repo: 'acme/ledger-db', health: 'HEALTHY'}),
           (inv:Service {name: 'inventory-service', tier: 2, language: 'Java', repo: 'acme/inventory-service', health: 'HEALTHY'}),
           (notif:Service {name: 'notification-worker', tier: 3, language: 'Python', repo: 'acme/notification-worker', health: 'HEALTHY'}),

           (gw)-[:DEPENDS_ON {latency_ms: 12, criticality: 'CRITICAL'}]->(auth),
           (gw)-[:DEPENDS_ON {latency_ms: 28, criticality: 'CRITICAL'}]->(checkout),
           (gw)-[:DEPENDS_ON {latency_ms: 2, criticality: 'HIGH'}]->(redis),
           (checkout)-[:DEPENDS_ON {latency_ms: 35, criticality: 'HIGH'}]->(inv),
           (checkout)-[:DEPENDS_ON {latency_ms: 45, criticality: 'CRITICAL'}]->(pay),
           (checkout)-[:DEPENDS_ON {latency_ms: 15, criticality: 'LOW'}]->(notif),
           (pay)-[:DEPENDS_ON {latency_ms: 18, criticality: 'CRITICAL'}]->(ledger),
           (auth)-[:DEPENDS_ON {latency_ms: 3, criticality: 'HIGH'}]->(redis)
    """
    graph.query(services_cypher)

    logger.info("Creating Track 1: Commits and Incidents...")
    commits_incidents_cypher = """
    MATCH (pay:Service {name: 'payment-worker'}),
          (auth:Service {name: 'auth-service'}),
          (checkout:Service {name: 'checkout-service'}),
          (gw:Service {name: 'api-gateway'}),
          (ledger:Service {name: 'ledger-db'}),
          (inv:Service {name: 'inventory-service'}),
          (redis:Service {name: 'redis-session-cache'})

    CREATE (c1:Commit {sha: 'c8f1a23', message: 'refactor(payment): update stripe v3 webhooks', timestamp: '2026-10-15T09:20:00Z', files_changed: 4}),
           (c2:Commit {sha: 'b29e011', message: 'feat(auth): add biometric token refresh endpoint', timestamp: '2026-10-14T14:10:00Z', files_changed: 6}),
           (c3:Commit {sha: '77d4c82', message: 'fix(checkout): add circuit breaker on inventory timeout', timestamp: '2026-10-15T11:45:00Z', files_changed: 3}),
           (c4:Commit {sha: '41a0e5b', message: 'perf(gateway): tune HTTP2 keepalive and max concurrency', timestamp: '2026-10-13T16:00:00Z', files_changed: 2}),
           (c5:Commit {sha: 'e3d99fa', message: 'chore(db): create compound index on ledger_entries(account_id, tx_date)', timestamp: '2026-10-12T08:30:00Z', files_changed: 1}),
           (c6:Commit {sha: '11ac89b', message: 'fix(inventory): stock decrement race condition under load', timestamp: '2026-10-15T13:15:00Z', files_changed: 5}),

           (c1)-[:MODIFIED]->(pay),
           (c2)-[:MODIFIED]->(auth),
           (c3)-[:MODIFIED]->(checkout),
           (c4)-[:MODIFIED]->(gw),
           (c5)-[:MODIFIED]->(ledger),
           (c6)-[:MODIFIED]->(inv),

           (inc1:Incident {id: 'inc-401', severity: 'SEV-1', symptom: 'Checkout 504 Gateway Timeout during flash sale', status: 'RESOLVED'}),
           (inc2:Incident {id: 'inc-402', severity: 'SEV-2', symptom: 'Payment webhook delivery delayed by 45s', status: 'INVESTIGATING'}),
           (inc3:Incident {id: 'inc-403', severity: 'SEV-3', symptom: 'Redis eviction spikes causing intermittent session logout', status: 'MONITORING'}),

           (inc1)-[:AFFECTED]->(checkout),
           (inc2)-[:AFFECTED]->(pay),
           (inc3)-[:AFFECTED]->(redis)
    """
    graph.query(commits_incidents_cypher)

    # -------------------------------------------------------------
    # TRACK 2: AGENT MEMORY & COORDINATION (Episodes, Procedures, Handoffs)
    # -------------------------------------------------------------
    logger.info("Creating Track 2: Episodic Memory, Procedures, and Multi-Agent Handoffs...")
    agent_memory_cypher = """
    MATCH (pay:Service {name: 'payment-worker'}),
          (auth:Service {name: 'auth-service'}),
          (checkout:Service {name: 'checkout-service'}),
          (notif:Service {name: 'notification-worker'})

    CREATE (p1:Procedure {id: 'proc-pool-resize', name: 'Database Pool Resizing & Connection Drain', action_steps: '1. Inspect max_connections; 2. Scale worker pool from 20 to 50; 3. Trigger graceful reload', success_rate: 0.94, execution_count: 18}),
           (p2:Procedure {id: 'proc-redis-failover', name: 'Redis Memory Defrag & Sentinel Failover', action_steps: '1. Check info memory; 2. Enable active defragmentation; 3. Verify replication sync', success_rate: 0.89, execution_count: 12}),
           (p3:Procedure {id: 'proc-circuit-trip', name: 'Dynamic Circuit Breaker Tripping & Fallback Cache', action_steps: '1. Trip circuit on downstream inventory timeouts; 2. Serve optimistic reservation; 3. Re-probe health', success_rate: 0.96, execution_count: 27}),
           (p4:Procedure {id: 'proc-throttle-worker', name: 'Exponential Backoff & Dead Letter Queue Re-routing', action_steps: '1. Pause partition consumption; 2. Apply jittered backoff; 3. Flush stale events to DLQ', success_rate: 0.91, execution_count: 14}),

           (ep1:Episode {id: 'ep-101', session_id: 'sess-agent-001', symptom: 'High P99 latency (>2000ms) on /checkout/pay', root_cause: 'Connection pool exhaustion in payment-worker connecting to ledger-db', timestamp: '2026-09-28T14:30:00Z', outcome: 'SUCCESS'}),
           (ep2:Episode {id: 'ep-102', session_id: 'sess-agent-002', symptom: 'Auth token validation failure rate 18%', root_cause: 'Redis memory fragmentation and key TTL race on token refresh', timestamp: '2026-10-02T08:15:00Z', outcome: 'SUCCESS'}),
           (ep3:Episode {id: 'ep-103', session_id: 'sess-agent-003', symptom: 'Cascading 503 errors across checkout-service', root_cause: 'Inventory service lock contention during bulk stock update', timestamp: '2026-10-08T19:40:00Z', outcome: 'SUCCESS'}),
           (ep4:Episode {id: 'ep-104', session_id: 'sess-agent-004', symptom: 'Notification queue backlog exceeding 50,000 messages', root_cause: 'Third-party push provider rate limiting without backoff', timestamp: '2026-10-12T11:20:00Z', outcome: 'SUCCESS'}),

           (ep1)-[:AFFECTED]->(pay),
           (ep1)-[:RESOLVED_BY]->(p1),
           (ep2)-[:AFFECTED]->(auth),
           (ep2)-[:RESOLVED_BY]->(p2),
           (ep3)-[:AFFECTED]->(checkout),
           (ep3)-[:RESOLVED_BY]->(p3),
           (ep4)-[:AFFECTED]->(notif),
           (ep4)-[:RESOLVED_BY]->(p4),

           (agTriage:Agent {id: 'agent-triage', name: 'TriageAgent', role: 'Anomaly Detection & Initial Assessment'}),
           (agRootCause:Agent {id: 'agent-rootcause', name: 'RootCauseAgent', role: 'Topology Diagnostics & Correlation'}),
           (agRemediation:Agent {id: 'agent-remediation', name: 'RemediationAgent', role: 'Automated Recovery & Verification'}),

           (h1:AgentHandoff {id: 'handoff-01', session_id: 'sess-coord-2026', state_summary: 'High error rate isolated to payment-worker; verified network connectivity', timestamp: '2026-10-16T11:00:00Z', status: 'COMPLETED'}),
           (h2:AgentHandoff {id: 'handoff-02', session_id: 'sess-coord-2026', state_summary: 'Identified connection leak in commit c8f1a23; proposed procedure proc-pool-resize', timestamp: '2026-10-16T11:05:00Z', status: 'ACTIVE'}),

           (agTriage)-[:INITIATED_HANDOFF]->(h1),
           (h1)-[:HANDED_OFF_TO]->(agRootCause),
           (h1)-[:TARGETS_SERVICE]->(pay),

           (agRootCause)-[:INITIATED_HANDOFF]->(h2),
           (h2)-[:HANDED_OFF_TO]->(agRemediation),
           (h2)-[:TARGETS_SERVICE]->(pay)
    """
    graph.query(agent_memory_cypher)

    # -------------------------------------------------------------
    # TRACK 3: COMPANY BRAIN (People, Teams, Expertise, Decisions, Documents)
    # -------------------------------------------------------------
    logger.info("Creating Track 3: People, Teams, Expertise, ADR/RFC Decisions, and Documents...")
    company_brain_cypher = """
    MATCH (gw:Service {name: 'api-gateway'}),
          (auth:Service {name: 'auth-service'}),
          (checkout:Service {name: 'checkout-service'}),
          (pay:Service {name: 'payment-worker'}),
          (redis:Service {name: 'redis-session-cache'}),
          (ledger:Service {name: 'ledger-db'}),
          (inv:Service {name: 'inventory-service'}),
          (notif:Service {name: 'notification-worker'}),
          (c1:Commit {sha: 'c8f1a23'}),
          (c2:Commit {sha: 'b29e011'}),
          (c3:Commit {sha: '77d4c82'}),
          (c4:Commit {sha: '41a0e5b'}),
          (c5:Commit {sha: 'e3d99fa'}),
          (c6:Commit {sha: '11ac89b'})

    CREATE (u1:Person {id: 'usr-1', name: 'Sarah Chen', role: 'Principal SRE', slack_handle: '@schen', status: 'ONLINE'}),
           (u2:Person {id: 'usr-2', name: 'Alex Rivera', role: 'Staff Backend Engineer', slack_handle: '@arivera', status: 'ONLINE'}),
           (u3:Person {id: 'usr-3', name: 'Elena Rostova', role: 'Tech Lead - Payments', slack_handle: '@erostova', status: 'ONLINE'}),
           (u4:Person {id: 'usr-4', name: 'David Kim', role: 'Senior Infrastructure Engineer', slack_handle: '@dkim', status: 'PTO'}),
           (u5:Person {id: 'usr-5', name: 'Maya Patel', role: 'Security Architect', slack_handle: '@mpatel', status: 'ONLINE'}),
           (u6:Person {id: 'usr-6', name: 'Liam O Connor', role: 'Senior Fullstack Engineer', slack_handle: '@loconnor', status: 'ONLINE'}),
           (u7:Person {id: 'usr-7', name: 'Zoe Washington', role: 'Database Reliability Engineer', slack_handle: '@zwashington', status: 'PTO'}),
           (u8:Person {id: 'usr-8', name: 'Marcus Brody', role: 'Staff Platform Engineer', slack_handle: '@mbrody', status: 'ONLINE'}),

           (t1:Team {id: 'team-platform', name: 'Core Platform & Infrastructure', oncall_channel: '#oncall-platform'}),
           (t2:Team {id: 'team-payments', name: 'Payments & Commerce Engine', oncall_channel: '#oncall-payments'}),
           (t3:Team {id: 'team-security', name: 'Product Security & Identity', oncall_channel: '#oncall-secops'}),

           (u1)-[:MEMBER_OF {lead: true}]->(t1),
           (u4)-[:MEMBER_OF {lead: false}]->(t1),
           (u8)-[:MEMBER_OF {lead: false}]->(t1),

           (u3)-[:MEMBER_OF {lead: true}]->(t2),
           (u2)-[:MEMBER_OF {lead: false}]->(t2),

           (u5)-[:MEMBER_OF {lead: true}]->(t3),
           (u6)-[:MEMBER_OF {lead: false}]->(t3),
           (u7)-[:MEMBER_OF {lead: false}]->(t3),

           (u3)-[:HAS_EXPERTISE {score: 0.95, commits_count: 84}]->(pay),
           (u3)-[:HAS_EXPERTISE {score: 0.88, commits_count: 42}]->(ledger),
           (u2)-[:HAS_EXPERTISE {score: 0.92, commits_count: 112}]->(checkout),
           (u2)-[:HAS_EXPERTISE {score: 0.81, commits_count: 56}]->(inv),
           (u5)-[:HAS_EXPERTISE {score: 0.96, commits_count: 73}]->(auth),
           (u8)-[:HAS_EXPERTISE {score: 0.94, commits_count: 91}]->(gw),
           (u7)-[:HAS_EXPERTISE {score: 0.97, commits_count: 68}]->(ledger),
           (u1)-[:HAS_EXPERTISE {score: 0.93, commits_count: 49}]->(redis),
           (u1)-[:HAS_EXPERTISE {score: 0.89, commits_count: 62}]->(gw),
           (u6)-[:HAS_EXPERTISE {score: 0.85, commits_count: 38}]->(notif),

           (u3)-[:AUTHORED_COMMIT]->(c1),
           (u5)-[:AUTHORED_COMMIT]->(c2),
           (u2)-[:AUTHORED_COMMIT]->(c3),
           (u8)-[:AUTHORED_COMMIT]->(c4),
           (u7)-[:AUTHORED_COMMIT]->(c5),
           (u2)-[:AUTHORED_COMMIT]->(c6),

           (d1:Decision {id: 'dec-01', title: 'ADR-042: Migrate Payment Processing to Asynchronous Worker Model', summary: 'Decouple synchronous HTTP checkout flow from payment gateway I/O using message queues and idempotent ledger entries', timestamp: '2026-07-15T10:00:00Z', status: 'ACTIVE'}),
           (d2:Decision {id: 'dec-02', title: 'ADR-051: Adopt Redis Cluster for Distributed Session & Idempotency Storage', summary: 'Standardize session tokens and payment idempotency keys on Redis with active replication and 24h sliding TTL', timestamp: '2026-08-01T14:30:00Z', status: 'ACTIVE'}),
           (d3:Decision {id: 'dec-03', title: 'RFC-108: Multi-Region Circuit Breaker Thresholds for Downstream Dependencies', summary: 'Define fallback contracts and max retry limits for payment-worker and inventory-service calls', timestamp: '2026-09-10T16:00:00Z', status: 'ACTIVE'}),
           (d4:Decision {id: 'dec-04', title: 'Postmortem-2026-09: Remediation of Ledger Connection Pool Lockout', summary: 'Root cause analysis and mitigation for connection leak during batch settlement', timestamp: '2026-10-01T09:00:00Z', status: 'ACTIVE'}),

           (u3)-[:AUTHORED_DECISION]->(d1),
           (u1)-[:AUTHORED_DECISION]->(d2),
           (u2)-[:AUTHORED_DECISION]->(d3),
           (u7)-[:AUTHORED_DECISION]->(d4),

           (doc1:Document {id: 'doc-01', doc_id: 'ADR-042', title: 'ADR-042: Async Payment Processing', type: 'ADR', url: 'https://wiki.acme.internal/docs/adr-042'}),
           (doc2:Document {id: 'doc-02', doc_id: 'ADR-051', title: 'ADR-051: Redis Cluster Architecture', type: 'ADR', url: 'https://wiki.acme.internal/docs/adr-051'}),
           (doc3:Document {id: 'doc-03', doc_id: 'RFC-108', title: 'RFC-108: Circuit Breaker Specifications', type: 'RFC', url: 'https://wiki.acme.internal/docs/rfc-108'}),
           (doc4:Document {id: 'doc-04', doc_id: 'PM-2026-09', title: 'Postmortem: September Ledger Connection Exhaustion', type: 'Postmortem', url: 'https://wiki.acme.internal/postmortems/2026-09-ledger'}),

           (d1)-[:DOCUMENTED_IN]->(doc1),
           (d2)-[:DOCUMENTED_IN]->(doc2),
           (d3)-[:DOCUMENTED_IN]->(doc3),
           (d4)-[:DOCUMENTED_IN]->(doc4),

           (d1)-[:GOVERNS]->(pay),
           (d1)-[:GOVERNS]->(ledger),
           (d2)-[:GOVERNS]->(redis),
           (d2)-[:GOVERNS]->(auth),
           (d3)-[:GOVERNS]->(checkout),
           (d3)-[:GOVERNS]->(inv),
           (d4)-[:GOVERNS]->(ledger)
    """
    graph.query(company_brain_cypher)

    # -------------------------------------------------------------
    # INDICES CREATION
    # -------------------------------------------------------------
    logger.info("Executing FalkorDB indices on key lookup properties...")
    indices = [
        ("Service", "name"),
        ("Person", "id"),
        ("Episode", "id"),
        ("Decision", "id"),
        ("Commit", "sha"),
        ("Incident", "id"),
        ("Team", "id"),
        ("Procedure", "id"),
        ("Document", "id"),
    ]
    for label, prop in indices:
        manager.create_index(tenant, label, prop)

    # Count nodes and edges
    node_count = graph.query("MATCH (n) RETURN count(n) AS cnt").result_set[0][0]
    edge_count = graph.query("MATCH ()-[r]->() RETURN count(r) AS cnt").result_set[0][0]
    logger.info(f"Seeded nexus_{tenant} successfully: {node_count} nodes, {edge_count} edges.")

    return {
        "tenant": tenant,
        "nodes": node_count,
        "edges": edge_count,
    }


def seed_finserve_io(manager: FalkorDBManager) -> Dict[str, Any]:
    """Seed the second isolated tenant graph nexus_finserve_io to prove multi-tenancy."""
    tenant = "finserve_io"
    logger.info(f"--- Seeding graph: nexus_{tenant} ---")

    # Clear previous graph
    manager.delete_tenant_graph(tenant)
    graph = manager.get_graph(tenant)

    # Microservices & Dependencies for FinServe
    finserve_cypher = """
    CREATE (edge:Service {name: 'api-edge', tier: 1, language: 'Go', repo: 'finserve/api-edge', health: 'HEALTHY'}),
           (core:Service {name: 'core-banking', tier: 1, language: 'Java', repo: 'finserve/core-banking', health: 'HEALTHY'}),
           (fraud:Service {name: 'fraud-detection', tier: 1, language: 'Python', repo: 'finserve/fraud-engine', health: 'HEALTHY'}),
           (wire:Service {name: 'wire-transfer', tier: 1, language: 'Kotlin', repo: 'finserve/wire-transfer', health: 'HEALTHY'}),
           (kyc:Service {name: 'kyc-service', tier: 2, language: 'Go', repo: 'finserve/kyc-service', health: 'HEALTHY'}),
           (risk:Service {name: 'risk-engine', tier: 1, language: 'Scala', repo: 'finserve/risk-engine', health: 'HEALTHY'}),
           (audit:Service {name: 'compliance-audit', tier: 2, language: 'Python', repo: 'finserve/compliance-audit', health: 'HEALTHY'}),
           (swift:Service {name: 'swift-gateway', tier: 1, language: 'C++', repo: 'finserve/swift-gateway', health: 'HEALTHY'}),

           (edge)-[:DEPENDS_ON {latency_ms: 8, criticality: 'CRITICAL'}]->(core),
           (edge)-[:DEPENDS_ON {latency_ms: 15, criticality: 'HIGH'}]->(fraud),
           (core)-[:DEPENDS_ON {latency_ms: 30, criticality: 'CRITICAL'}]->(wire),
           (wire)-[:DEPENDS_ON {latency_ms: 120, criticality: 'CRITICAL'}]->(swift),
           (wire)-[:DEPENDS_ON {latency_ms: 22, criticality: 'CRITICAL'}]->(risk),
           (fraud)-[:DEPENDS_ON {latency_ms: 18, criticality: 'HIGH'}]->(risk),
           (core)-[:DEPENDS_ON {latency_ms: 10, criticality: 'MEDIUM'}]->(audit),
           (kyc)-[:DEPENDS_ON {latency_ms: 40, criticality: 'HIGH'}]->(audit),

           (c1:Commit {sha: 'f71a001', message: 'feat(fraud): ML inference latency optimization', timestamp: '2026-10-15T10:00:00Z', files_changed: 8}),
           (c2:Commit {sha: 'd88b022', message: 'fix(swift): ISO 20022 message parser update', timestamp: '2026-10-16T08:30:00Z', files_changed: 3}),
           (c1)-[:MODIFIED]->(fraud),
           (c2)-[:MODIFIED]->(swift),

           (inc1:Incident {id: 'inc-fs-901', severity: 'SEV-1', symptom: 'Swift gateway heartbeat timeout during international clearing', status: 'RESOLVED'}),
           (inc1)-[:AFFECTED]->(swift),

           (p1:Procedure {id: 'proc-fs-rebalance', name: 'Kafka Consumer Re-assignment & Offset Reset', action_steps: '1. Pause wire group; 2. Seek to last committed offset; 3. Resume stream', success_rate: 0.98, execution_count: 22}),
           (ep1:Episode {id: 'ep-fs-01', session_id: 'sess-fs-801', symptom: 'Wire transfer queue saturation', root_cause: 'Kafka consumer group rebalance delay', timestamp: '2026-10-11T14:00:00Z', outcome: 'SUCCESS'}),
           (ep1)-[:AFFECTED]->(wire),
           (ep1)-[:RESOLVED_BY]->(p1),

           (u1:Person {id: 'fs-usr-1', name: 'David Vance', role: 'Chief Risk Officer', slack_handle: '@dvance', status: 'ONLINE'}),
           (u2:Person {id: 'fs-usr-2', name: 'Chloe Martin', role: 'Lead Core Architect', slack_handle: '@cmartin', status: 'ONLINE'}),
           (team:Team {id: 'team-fin-core', name: 'FinServe Core Banking', oncall_channel: '#fin-oncall'}),

           (u1)-[:MEMBER_OF]->(team),
           (u2)-[:MEMBER_OF]->(team),
           (u2)-[:HAS_EXPERTISE {score: 0.98, commits_count: 140}]->(core),
           (u2)-[:HAS_EXPERTISE {score: 0.94, commits_count: 95}]->(wire),
           (u2)-[:AUTHORED_COMMIT]->(c2),

           (dec:Decision {id: 'fs-dec-01', title: 'ADR-FS-01: Zero Trust Service Mesh for Banking APIs', summary: 'Mandate mTLS and SPIFFE identity validation across all inter-service financial communications', timestamp: '2026-06-20T12:00:00Z', status: 'ACTIVE'}),
           (u2)-[:AUTHORED_DECISION]->(dec),
           (dec)-[:GOVERNS]->(core),
           (dec)-[:GOVERNS]->(wire),

           (doc:Document {id: 'fs-doc-01', doc_id: 'ADR-FS-01', title: 'ADR-FS-01: Zero Trust Banking Architecture', type: 'ADR', url: 'https://docs.finserve.internal/adr/01'}),
           (dec)-[:DOCUMENTED_IN]->(doc)
    """
    graph.query(finserve_cypher)

    # Indices for FinServe
    for label, prop in [("Service", "name"), ("Person", "id"), ("Episode", "id"), ("Decision", "id")]:
        manager.create_index(tenant, label, prop)

    node_count = graph.query("MATCH (n) RETURN count(n) AS cnt").result_set[0][0]
    edge_count = graph.query("MATCH ()-[r]->() RETURN count(r) AS cnt").result_set[0][0]
    logger.info(f"Seeded nexus_{tenant} successfully: {node_count} nodes, {edge_count} edges.")

    return {
        "tenant": tenant,
        "nodes": node_count,
        "edges": edge_count,
    }


def verify_seeded_graphs(manager: FalkorDBManager) -> None:
    """Run verification checks on both graphs and test native graph algorithms."""
    logger.info("=== VERIFICATION GATE: EXECUTING MULTI-TENANT & ALGORITHM CHECKS ===")

    # 1. Multi-Tenant Graph Existence & Isolation
    graphs = manager.list_tenant_graphs()
    logger.info(f"Discovered tenant graphs in FalkorDB: {graphs}")
    assert "nexus_acme_corp" in graphs, "Missing nexus_acme_corp graph!"
    assert "nexus_finserve_io" in graphs, "Missing nexus_finserve_io graph!"

    # 2. Strict Tenant Isolation Verification
    # Service 'api-gateway' MUST exist in acme_corp and MUST NOT exist in finserve_io
    acme_gw = manager.query("acme_corp", "MATCH (s:Service {name: 'api-gateway'}) RETURN s.name").result_set
    assert len(acme_gw) == 1, "api-gateway not found in acme_corp!"

    finserve_gw = manager.query("finserve_io", "MATCH (s:Service {name: 'api-gateway'}) RETURN s.name").result_set
    assert len(finserve_gw) == 0, "ISOLATION BREACH: api-gateway leaked into finserve_io!"

    # Service 'core-banking' MUST exist in finserve_io and MUST NOT exist in acme_corp
    finserve_cb = manager.query("finserve_io", "MATCH (s:Service {name: 'core-banking'}) RETURN s.name").result_set
    assert len(finserve_cb) == 1, "core-banking not found in finserve_io!"

    acme_cb = manager.query("acme_corp", "MATCH (s:Service {name: 'core-banking'}) RETURN s.name").result_set
    assert len(acme_cb) == 0, "ISOLATION BREACH: core-banking leaked into acme_corp!"

    logger.info("✓ Multi-tenant graph isolation verified strictly (zero data leakage).")

    # 3. Track 1, 2, 3 Entity Counts in nexus_acme_corp
    services = manager.query("acme_corp", "MATCH (s:Service) RETURN count(s) AS cnt").result_set[0][0]
    episodes = manager.query("acme_corp", "MATCH (e:Episode) RETURN count(e) AS cnt").result_set[0][0]
    procedures = manager.query("acme_corp", "MATCH (p:Procedure) RETURN count(p) AS cnt").result_set[0][0]
    people = manager.query("acme_corp", "MATCH (p:Person) RETURN count(p) AS cnt").result_set[0][0]
    teams = manager.query("acme_corp", "MATCH (t:Team) RETURN count(t) AS cnt").result_set[0][0]
    decisions = manager.query("acme_corp", "MATCH (d:Decision) RETURN count(d) AS cnt").result_set[0][0]
    documents = manager.query("acme_corp", "MATCH (d:Document) RETURN count(d) AS cnt").result_set[0][0]
    commits = manager.query("acme_corp", "MATCH (c:Commit) RETURN count(c) AS cnt").result_set[0][0]
    incidents = manager.query("acme_corp", "MATCH (i:Incident) RETURN count(i) AS cnt").result_set[0][0]
    handoffs = manager.query("acme_corp", "MATCH (h:AgentHandoff) RETURN count(h) AS cnt").result_set[0][0]

    logger.info(
        f"Entity validation (nexus_acme_corp):\n"
        f"  - Microservices: {services} (expected: 8)\n"
        f"  - Commits: {commits} (expected: 6)\n"
        f"  - Incidents: {incidents} (expected: 3)\n"
        f"  - Episodes: {episodes} (expected: 4)\n"
        f"  - Procedures: {procedures} (expected: 4)\n"
        f"  - Agent Handoffs: {handoffs} (expected: 2)\n"
        f"  - People: {people} (expected: 8)\n"
        f"  - Teams: {teams} (expected: 3)\n"
        f"  - Decisions: {decisions} (expected: 4)\n"
        f"  - Documents: {documents} (expected: 4)"
    )

    assert services == 8, f"Expected 8 services, found {services}"
    assert episodes == 4, f"Expected 4 episodes, found {episodes}"
    assert people == 8, f"Expected 8 people, found {people}"
    assert teams == 3, f"Expected 3 teams, found {teams}"
    assert decisions == 4, f"Expected 4 decisions, found {decisions}"
    assert documents == 4, f"Expected 4 documents, found {documents}"

    # 4. Native Graph Algorithm Verification: PageRank
    logger.info("Testing native graph algorithm: CALL algo.pageRank('Service', 'DEPENDS_ON')...")
    algo_query = "CALL algo.pageRank('Service', 'DEPENDS_ON')"
    trace_result = manager.query_with_trace("acme_corp", algo_query)

    rows, trace = trace_result
    assert len(rows) > 0, "PageRank returned no rows!"
    logger.info(f"✓ Native PageRank executed cleanly in {trace['execution_time_ms']} ms! Top services by PageRank:")
    
    # Sort by score descending
    sorted_ranks = sorted(rows, key=lambda x: x.get("score", 0), reverse=True)
    for rank in sorted_ranks[:5]:
        svc_props = rank.get("node", {}).get("properties", {})
        logger.info(f"    * {svc_props.get('name', 'unknown')}: score = {rank.get('score'):.5f}")

    # Also test PageRank on the second tenant to ensure algorithms work on both graphs
    fs_algo = manager.query_with_trace("finserve_io", "CALL algo.pageRank('Service', 'DEPENDS_ON')")
    assert len(fs_algo.rows) > 0, "FinServe PageRank failed!"
    logger.info(f"✓ Native PageRank on nexus_finserve_io executed cleanly in {fs_algo.subgraph_trace['execution_time_ms']} ms.")

    logger.info("=== VERIFICATION GATE PASSED: ZERO ERRORS ===")


def main():
    manager = FalkorDBManager()
    if not manager.ping():
        logger.error(f"Cannot connect to FalkorDB at {manager.host}:{manager.port}!")
        sys.exit(1)

    logger.info(f"Connected to FalkorDB successfully at {manager.host}:{manager.port}.")
    acme_stats = seed_acme_corp(manager)
    finserve_stats = seed_finserve_io(manager)

    verify_seeded_graphs(manager)
    print("\nPhase 1 Seeding Complete!")
    print(f"  * nexus_acme_corp: {acme_stats['nodes']} nodes, {acme_stats['edges']} edges")
    print(f"  * nexus_finserve_io: {finserve_stats['nodes']} nodes, {finserve_stats['edges']} edges")


if __name__ == "__main__":
    main()
