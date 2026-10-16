"""Standardized MCP Tool Functions and Direct Python Registry for NexusGraph.

All tools accept `tenant_id: str = "acme_corp"` to guarantee multi-tenant graph isolation,
and return both structured domain `data` and an explainable `subgraph_trace`
(nodes, edges, cypher_executed, execution_time_ms) for AI reasoning and UI graph rendering.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.db.client import FalkorDBManager

# Shared manager instance for direct invocations
_manager: Optional[FalkorDBManager] = None


def get_db_manager() -> FalkorDBManager:
    """Lazy initialize FalkorDBManager."""
    global _manager
    if _manager is None:
        _manager = FalkorDBManager()
    return _manager


# =============================================================================
# TOOL 1: analyze_blast_radius_and_commits (Track 1)
# =============================================================================
def analyze_blast_radius_and_commits(
    tenant_id: str = "acme_corp",
    service_name: str = "checkout-service",
    max_hops: int = 3,
) -> Dict[str, Any]:
    """
    Traverses upstream and downstream [:DEPENDS_ON*1..max_hops] relationships
    from `service_name` and joins any (:Commit)-[:MODIFIED]->(:Service) and
    (:Person)-[:AUTHORED_COMMIT]->(:Commit).
    """
    manager = get_db_manager()
    clean_tenant = (tenant_id or "acme_corp").strip()
    svc_name = (service_name or "checkout-service").strip()
    try:
        hops = max(1, min(int(max_hops), 5))
    except (ValueError, TypeError):
        hops = 3

    cypher = f"""
    MATCH (target:Service {{name: $service_name}})
    OPTIONAL MATCH (target)-[dep:DEPENDS_ON*1..{hops}]-(connected:Service)
    WITH target, collect(DISTINCT connected) + [target] AS all_services
    UNWIND all_services AS svc
    OPTIONAL MATCH (c:Commit)-[m:MODIFIED]->(svc)
    OPTIONAL MATCH (author:Person)-[auth_rel:AUTHORED_COMMIT]->(c)
    RETURN svc, c, author, m, auth_rel
    """
    try:
        trace_res = manager.query_with_trace(clean_tenant, cypher, {"service_name": svc_name})
        rows, trace = trace_res
    except Exception as e:
        return {
            "data": {
                "service_name": svc_name,
                "max_hops": hops,
                "connected_services_count": 0,
                "recent_commits_count": 0,
                "impacted_services": [],
                "recent_commits": [],
                "error": str(e),
                "summary": f"Error traversing blast radius on '{svc_name}': {e}",
            },
            "subgraph_trace": {
                "nodes": [],
                "edges": [],
                "cypher_executed": cypher,
                "execution_time_ms": 0.0,
                "error": str(e),
            },
        }

    services_map: Dict[str, Dict[str, Any]] = {}
    commits_map: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        svc_dict = row.get("svc")
        if svc_dict and "properties" in svc_dict:
            s_name = svc_dict["properties"].get("name")
            if s_name and s_name not in services_map:
                services_map[s_name] = {
                    "name": s_name,
                    "tier": svc_dict["properties"].get("tier"),
                    "language": svc_dict["properties"].get("language"),
                    "health": svc_dict["properties"].get("health", "UNKNOWN"),
                    "repo": svc_dict["properties"].get("repo"),
                    "is_target": (s_name == service_name),
                }

        c_dict = row.get("c")
        if c_dict and "properties" in c_dict:
            sha = c_dict["properties"].get("sha")
            if sha and sha not in commits_map:
                author_dict = row.get("author")
                author_name = (
                    author_dict["properties"].get("name")
                    if author_dict and "properties" in author_dict
                    else "Unknown"
                )
                svc_mod = (
                    svc_dict["properties"].get("name")
                    if svc_dict and "properties" in svc_dict
                    else "Unknown"
                )
                commits_map[sha] = {
                    "sha": sha,
                    "message": c_dict["properties"].get("message"),
                    "timestamp": c_dict["properties"].get("timestamp"),
                    "files_changed": c_dict["properties"].get("files_changed"),
                    "modified_service": svc_mod,
                    "author": author_name,
                }

    impacted_services = list(services_map.values())
    recent_commits = list(commits_map.values())

    data = {
        "service_name": service_name,
        "max_hops": hops,
        "connected_services_count": len(impacted_services),
        "recent_commits_count": len(recent_commits),
        "impacted_services": impacted_services,
        "recent_commits": recent_commits,
        "summary": (
            f"Blast radius analysis for '{service_name}' identified {len(impacted_services)} connected "
            f"services within {hops} hops and {len(recent_commits)} recent commits."
        ),
    }

    return {
        "data": data,
        "subgraph_trace": trace,
    }


# =============================================================================
# TOOL 2: run_graph_criticality_and_path (Track 1)
# =============================================================================
def run_graph_criticality_and_path(
    tenant_id: str = "acme_corp",
    source_service: str = "api-gateway",
    target_service: str = "ledger-db",
) -> Dict[str, Any]:
    """
    Executes FalkorDB's native PageRank algorithm (`CALL algo.pageRank('Service', 'DEPENDS_ON')`)
    to identify bottleneck services AND computes the shortest failure propagation path
    (`shortestPath`) between source_service and target_service.
    """
    manager = get_db_manager()
    clean_tenant = (tenant_id or "acme_corp").strip()
    src_svc = (source_service or "api-gateway").strip()
    tgt_svc = (target_service or "ledger-db").strip()

    # Step 1: Execute Native PageRank
    pagerank_cypher = "CALL algo.pageRank('Service', 'DEPENDS_ON')"
    try:
        pr_rows, pr_trace = manager.query_with_trace(clean_tenant, pagerank_cypher)
    except Exception as e:
        pr_rows, pr_trace = [], {
            "nodes": [],
            "edges": [],
            "cypher_executed": pagerank_cypher,
            "execution_time_ms": 0.0,
            "error": str(e),
        }

    rankings: List[Dict[str, Any]] = []
    for r in pr_rows:
        node = r.get("node", {})
        props = node.get("properties", {})
        score = r.get("score", 0.0)
        s_name = props.get("name")
        if s_name:
            rankings.append({
                "service": s_name,
                "pagerank_score": round(score, 6),
                "tier": props.get("tier"),
                "health": props.get("health", "UNKNOWN"),
            })

    rankings.sort(key=lambda x: x["pagerank_score"], reverse=True)
    bottlenecks = [r["service"] for r in rankings[:3]]

    # Step 2: Compute Shortest Propagation Path
    # Note: FalkorDB syntax requires shortestPath in WITH or RETURN clause with directed edges
    shortest_path_cypher = """
    MATCH (src:Service {name: $source}), (tgt:Service {name: $target})
    RETURN shortestPath((src)-[:DEPENDS_ON*]->(tgt)) AS path
    """
    try:
        sp_rows, sp_trace = manager.query_with_trace(
            clean_tenant,
            shortest_path_cypher,
            {"source": src_svc, "target": tgt_svc},
        )
    except Exception as e:
        sp_rows, sp_trace = [], {
            "nodes": [],
            "edges": [],
            "cypher_executed": shortest_path_cypher,
            "execution_time_ms": 0.0,
            "error": str(e),
        }

    path_nodes: List[str] = []
    path_edges: List[Dict[str, Any]] = []
    has_path = False

    # Check if a directed path was found; if not, check reverse direction
    if sp_rows and sp_rows[0].get("path") is not None:
        has_path = True
        path_obj = sp_rows[0]["path"]
        if isinstance(path_obj, dict):
            for n in path_obj.get("nodes", []):
                p_name = n.get("properties", {}).get("name")
                if p_name:
                    path_nodes.append(p_name)
            for e in path_obj.get("edges", []):
                path_edges.append({
                    "relation": e.get("relation"),
                    "properties": e.get("properties", {}),
                })
    else:
        # Try reverse propagation check (tgt -> src)
        rev_cypher = """
        MATCH (src:Service {name: $source}), (tgt:Service {name: $target})
        RETURN shortestPath((tgt)-[:DEPENDS_ON*]->(src)) AS path
        """
        try:
            rev_rows, rev_trace = manager.query_with_trace(
                clean_tenant,
                rev_cypher,
                {"source": src_svc, "target": tgt_svc},
            )
        except Exception:
            rev_rows, rev_trace = [], sp_trace

        if rev_rows and rev_rows[0].get("path") is not None:
            has_path = True
            sp_trace = rev_trace
            path_obj = rev_rows[0]["path"]
            if isinstance(path_obj, dict):
                for n in path_obj.get("nodes", []):
                    p_name = n.get("properties", {}).get("name")
                    if p_name:
                        path_nodes.append(p_name)
                for e in path_obj.get("edges", []):
                    path_edges.append({
                        "relation": e.get("relation"),
                        "properties": e.get("properties", {}),
                    })

    # Combine traces from both algorithm calls
    combined_nodes = {n["id"]: n for n in (pr_trace.get("nodes", []) + sp_trace.get("nodes", []))}
    combined_edges = {e["id"]: e for e in (pr_trace.get("edges", []) + sp_trace.get("edges", []))}
    total_time = round(pr_trace.get("execution_time_ms", 0) + sp_trace.get("execution_time_ms", 0), 3)

    combined_trace = {
        "nodes": list(combined_nodes.values()),
        "edges": list(combined_edges.values()),
        "cypher_executed": f"{pagerank_cypher}\n{shortest_path_cypher.strip()}",
        "execution_time_ms": total_time,
    }

    data = {
        "source_service": source_service,
        "target_service": target_service,
        "path_found": has_path,
        "propagation_path": path_nodes,
        "propagation_hops": len(path_edges),
        "path_edge_details": path_edges,
        "top_bottleneck_services": bottlenecks,
        "pagerank_rankings": rankings,
        "summary": (
            f"Path from '{source_service}' to '{target_service}' spans {len(path_edges)} hops: "
            f"{' -> '.join(path_nodes) if path_nodes else 'No direct dependency path'}. "
            f"Top network bottleneck is '{bottlenecks[0] if bottlenecks else 'N/A'}'."
        ),
    }

    return {
        "data": data,
        "subgraph_trace": combined_trace,
    }


# =============================================================================
# TOOL 3: recall_episodic_and_procedural_memory (Track 2)
# =============================================================================
def recall_episodic_and_procedural_memory(
    tenant_id: str = "acme_corp",
    service_name: str = "payment-worker",
    symptom_keyword: str = "",
) -> Dict[str, Any]:
    """
    Queries past incidents on the specified service or its connected neighbors:
    `(:Service)<-[:AFFECTED]-(ep:Episode)-[:RESOLVED_BY]->(proc:Procedure)`
    Returns historical root causes and the highest-confidence procedural runbooks
    ordered by `proc.success_rate DESC`.
    """
    manager = get_db_manager()
    clean_tenant = (tenant_id or "acme_corp").strip()
    svc_name = (service_name or "payment-worker").strip()
    kw = (symptom_keyword or "").strip()

    cypher = """
    MATCH (svc:Service)
    WHERE svc.name = $service_name OR (svc)-[:DEPENDS_ON*1..2]-(:Service {name: $service_name})
    MATCH (svc)<-[aff:AFFECTED]-(ep:Episode)-[res_by:RESOLVED_BY]->(proc:Procedure)
    WHERE toLower(ep.symptom) CONTAINS toLower($keyword) 
       OR toLower(ep.root_cause) CONTAINS toLower($keyword)
       OR toLower(proc.name) CONTAINS toLower($keyword)
       OR $keyword = ''
    RETURN ep, proc, svc, aff, res_by
    ORDER BY proc.success_rate DESC, proc.execution_count DESC
    """
    try:
        trace_res = manager.query_with_trace(
            clean_tenant,
            cypher,
            {"service_name": svc_name, "keyword": kw},
        )
        rows, trace = trace_res
    except Exception as e:
        return {
            "data": {
                "service_name": svc_name,
                "symptom_keyword": kw,
                "episodes_found": 0,
                "episodes": [],
                "recommended_runbook": None,
                "error": str(e),
                "summary": f"Failed to recall episodic memory on '{svc_name}': {e}",
            },
            "subgraph_trace": {
                "nodes": [],
                "edges": [],
                "cypher_executed": cypher,
                "execution_time_ms": 0.0,
                "error": str(e),
            },
        }

    episodes: List[Dict[str, Any]] = []
    seen_episodes = set()

    for r in rows:
        ep_dict = r.get("ep", {})
        proc_dict = r.get("proc", {})
        svc_dict = r.get("svc", {})

        ep_props = ep_dict.get("properties", {})
        proc_props = proc_dict.get("properties", {})
        svc_props = svc_dict.get("properties", {})

        ep_id = ep_props.get("id")
        if ep_id and ep_id not in seen_episodes:
            seen_episodes.add(ep_id)
            episodes.append({
                "episode_id": ep_id,
                "session_id": ep_props.get("session_id"),
                "service_affected": svc_props.get("name"),
                "symptom": ep_props.get("symptom"),
                "root_cause": ep_props.get("root_cause"),
                "outcome": ep_props.get("outcome"),
                "timestamp": ep_props.get("timestamp"),
                "resolved_by_procedure": {
                    "procedure_id": proc_props.get("id"),
                    "name": proc_props.get("name"),
                    "action_steps": proc_props.get("action_steps"),
                    "success_rate": proc_props.get("success_rate"),
                    "execution_count": proc_props.get("execution_count"),
                },
            })

    recommended_runbook = episodes[0]["resolved_by_procedure"] if episodes else None

    data = {
        "service_name": service_name,
        "symptom_keyword": symptom_keyword,
        "episodes_found": len(episodes),
        "episodes": episodes,
        "recommended_runbook": recommended_runbook,
        "summary": (
            f"Found {len(episodes)} relevant historical episodes for '{service_name}'. "
            f"Top recommended runbook: '{recommended_runbook['name']}' "
            f"(success rate: {recommended_runbook['success_rate'] * 100:.1f}%)"
            if recommended_runbook
            else f"No historical episodes matched '{symptom_keyword}' on '{service_name}'."
        ),
    }

    return {
        "data": data,
        "subgraph_trace": trace,
    }


# =============================================================================
# TOOL 4: query_company_brain_context (Track 3)
# =============================================================================
def query_company_brain_context(
    tenant_id: str = "acme_corp",
    service_name: str = "payment-worker",
) -> Dict[str, Any]:
    """
    Traverses company brain context for `service_name`:
    1. Engineers and Teams: `(:Service)<-[:HAS_EXPERTISE]-(p:Person)-[:MEMBER_OF]->(t:Team)`
    2. Architecture Decisions & Documents: `(:Service)<-[:GOVERNS]-(d:Decision)-[:DOCUMENTED_IN]->(doc:Document)`
    3. Flags experts who are "ONLINE" vs "PTO", returning exact ADR/RFC citations and author source attribution.
    """
    manager = get_db_manager()
    clean_tenant = (tenant_id or "acme_corp").strip()
    svc_name = (service_name or "payment-worker").strip()

    cypher = """
    MATCH (svc:Service {name: $service_name})
    OPTIONAL MATCH (svc)<-[exp:HAS_EXPERTISE]-(p:Person)-[m:MEMBER_OF]->(t:Team)
    OPTIONAL MATCH (svc)<-[gov:GOVERNS]-(d:Decision {status: 'ACTIVE'})-[doc_rel:DOCUMENTED_IN]->(doc:Document)
    OPTIONAL MATCH (author:Person)-[auth_doc:AUTHORED_DECISION]->(d)
    RETURN svc, p, exp, t, d, doc, author, gov, doc_rel, auth_doc
    """
    try:
        trace_res = manager.query_with_trace(clean_tenant, cypher, {"service_name": svc_name})
        rows, trace = trace_res
    except Exception as e:
        return {
            "data": {
                "service_name": svc_name,
                "primary_contact": None,
                "online_experts": [],
                "pto_experts": [],
                "governing_decisions": [],
                "error": str(e),
                "summary": f"Failed to query company brain context for '{svc_name}': {e}",
            },
            "subgraph_trace": {
                "nodes": [],
                "edges": [],
                "cypher_executed": cypher,
                "execution_time_ms": 0.0,
                "error": str(e),
            },
        }

    online_experts: List[Dict[str, Any]] = []
    pto_experts: List[Dict[str, Any]] = []
    seen_people = set()

    decisions_map: Dict[str, Dict[str, Any]] = {}

    for r in rows:
        p_dict = r.get("p")
        exp_dict = r.get("exp")
        t_dict = r.get("t")

        if p_dict and "properties" in p_dict:
            p_props = p_dict["properties"]
            p_id = p_props.get("id")
            if p_id and p_id not in seen_people:
                seen_people.add(p_id)
                exp_props = exp_dict.get("properties", {}) if exp_dict else {}
                t_props = t_dict.get("properties", {}) if t_dict else {}

                expert_info = {
                    "id": p_id,
                    "name": p_props.get("name"),
                    "role": p_props.get("role"),
                    "slack_handle": p_props.get("slack_handle"),
                    "status": p_props.get("status", "OFFLINE"),
                    "team_name": t_props.get("name", "Unknown"),
                    "oncall_channel": t_props.get("oncall_channel", "Unknown"),
                    "expertise_score": exp_props.get("score", 0.0),
                    "commits_count": exp_props.get("commits_count", 0),
                }
                if p_props.get("status") == "ONLINE":
                    online_experts.append(expert_info)
                else:
                    pto_experts.append(expert_info)

        d_dict = r.get("d")
        doc_dict = r.get("doc")
        author_dict = r.get("author")

        if d_dict and "properties" in d_dict:
            d_props = d_dict["properties"]
            d_id = d_props.get("id")
            if d_id and d_id not in decisions_map:
                doc_props = doc_dict.get("properties", {}) if doc_dict else {}
                author_props = author_dict.get("properties", {}) if author_dict else {}

                decisions_map[d_id] = {
                    "decision_id": d_id,
                    "title": d_props.get("title"),
                    "summary": d_props.get("summary"),
                    "status": d_props.get("status"),
                    "timestamp": d_props.get("timestamp"),
                    "author": author_props.get("name", "Architecture Council"),
                    "document": {
                        "doc_id": doc_props.get("doc_id"),
                        "title": doc_props.get("title"),
                        "type": doc_props.get("type"),
                        "url": doc_props.get("url"),
                    },
                }

    online_experts.sort(key=lambda x: x["expertise_score"], reverse=True)
    pto_experts.sort(key=lambda x: x["expertise_score"], reverse=True)

    primary_contact = online_experts[0] if online_experts else (pto_experts[0] if pto_experts else None)

    data = {
        "service_name": service_name,
        "primary_contact": primary_contact,
        "online_experts": online_experts,
        "pto_experts": pto_experts,
        "governing_decisions": list(decisions_map.values()),
        "summary": (
            f"Service '{service_name}' has {len(online_experts)} online experts and "
            f"{len(pto_experts)} on PTO. Primary contact: "
            f"{primary_contact['name'] + ' (' + primary_contact['slack_handle'] + ')' if primary_contact else 'None'}. "
            f"Governed by {len(decisions_map)} active architecture decisions."
        ),
    }

    return {
        "data": data,
        "subgraph_trace": trace,
    }


# =============================================================================
# TOOL 5: record_agent_handoff (Track 2)
# =============================================================================
def record_agent_handoff(
    tenant_id: str = "acme_corp",
    session_id: str = "sess-default",
    from_agent: str = "TriageAgent",
    to_agent: str = "RemediationAgent",
    summary: str = "Investigating elevated error rate",
    target_service: str = "payment-worker",
) -> Dict[str, Any]:
    """
    Mutates the graph in real time by creating an (:AgentHandoff) node and linking it via:
    - [:HANDOFF_IN_SESSION]->(:Session)
    - [:INVESTIGATING]->(:Service)
    - (:Agent)-[:INITIATED_HANDOFF]->(:AgentHandoff)
    - (:AgentHandoff)-[:HANDED_OFF_TO]->(:Agent)
    """
    manager = get_db_manager()
    clean_tenant = (tenant_id or "acme_corp").strip()
    clean_sess = (session_id or "sess-default").strip()
    from_ag = (from_agent or "TriageAgent").strip()
    to_ag = (to_agent or "RemediationAgent").strip()
    tgt_svc = (target_service or "payment-worker").strip()
    handoff_id = f"handoff-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    cypher = """
    MERGE (sess:Session {id: $session_id})
    ON CREATE SET sess.created_at = $timestamp, sess.status = 'ACTIVE'
    MERGE (svc:Service {name: $target_service})
    MERGE (ag_from:Agent {name: $from_agent})
    MERGE (ag_to:Agent {name: $to_agent})
    CREATE (h:AgentHandoff {
        id: $handoff_id,
        session_id: $session_id,
        from_agent: $from_agent,
        to_agent: $to_agent,
        summary: $summary,
        timestamp: $timestamp,
        status: 'COMPLETED'
    })
    CREATE (h)-[r_sess:HANDOFF_IN_SESSION]->(sess)
    CREATE (h)-[r_svc:INVESTIGATING]->(svc)
    CREATE (ag_from)-[r_from:INITIATED_HANDOFF]->(h)
    CREATE (h)-[r_to:HANDED_OFF_TO]->(ag_to)
    RETURN h, sess, svc, ag_from, ag_to, r_sess, r_svc, r_from, r_to
    """
    params = {
        "session_id": clean_sess,
        "target_service": tgt_svc,
        "from_agent": from_ag,
        "to_agent": to_ag,
        "handoff_id": handoff_id,
        "summary": summary,
        "timestamp": now_iso,
    }
    try:
        trace_res = manager.query_with_trace(clean_tenant, cypher, params)
        rows, trace = trace_res
    except Exception as e:
        return {
            "data": {
                "handoff_id": handoff_id,
                "session_id": clean_sess,
                "from_agent": from_ag,
                "to_agent": to_ag,
                "target_service": tgt_svc,
                "summary": summary,
                "timestamp": now_iso,
                "status": "FAILED",
                "error": str(e),
                "message": f"Failed to record state handoff from {from_ag} to {to_ag}: {e}",
            },
            "subgraph_trace": {
                "nodes": [],
                "edges": [],
                "cypher_executed": cypher,
                "execution_time_ms": 0.0,
                "error": str(e),
            },
        }

    data = {
        "handoff_id": handoff_id,
        "session_id": clean_sess,
        "from_agent": from_ag,
        "to_agent": to_ag,
        "target_service": tgt_svc,
        "summary": summary,
        "timestamp": now_iso,
        "status": "COMPLETED",
        "message": f"Successfully recorded state handoff from {from_ag} to {to_ag} on {tgt_svc}.",
    }

    return {
        "data": data,
        "subgraph_trace": trace,
    }


# =============================================================================
# TOOL 6: commit_new_episode_memory (Track 2)
# =============================================================================
def commit_new_episode_memory(
    tenant_id: str = "acme_corp",
    session_id: str = "sess-default",
    service_name: str = "payment-worker",
    symptom: str = "Elevated latency on checkout flow",
    root_cause: str = "Gunicorn worker connection pool exhaustion",
    procedure_name: str = "Database Pool Resizing & Connection Drain",
    action_steps: str = "1. Scale worker connections; 2. Reload pool",
) -> Dict[str, Any]:
    """
    Persists cross-session learning by writing a new (:Episode) node and merging/updating
    the (:Procedure) node's `execution_count` and `success_rate`, linking it to the affected
    (:Service) and active (:Session).
    """
    manager = get_db_manager()
    clean_tenant = (tenant_id or "acme_corp").strip()
    clean_sess = (session_id or "sess-default").strip()
    svc_name = (service_name or "payment-worker").strip()
    proc_name = (procedure_name or "Database Pool Resizing & Connection Drain").strip()
    episode_id = f"ep-{uuid.uuid4().hex[:8]}"
    proc_id = f"proc-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    cypher = """
    MERGE (sess:Session {id: $session_id})
    ON CREATE SET sess.created_at = $timestamp, sess.status = 'ACTIVE'
    MERGE (svc:Service {name: $service_name})
    MERGE (proc:Procedure {name: $procedure_name})
    ON CREATE SET proc.id = $proc_id,
                  proc.action_steps = $action_steps,
                  proc.execution_count = 1,
                  proc.success_rate = 1.0
    ON MATCH SET proc.execution_count = proc.execution_count + 1,
                 proc.action_steps = CASE WHEN $action_steps <> '' THEN $action_steps ELSE proc.action_steps END
    CREATE (ep:Episode {
        id: $episode_id,
        session_id: $session_id,
        symptom: $symptom,
        root_cause: $root_cause,
        timestamp: $timestamp,
        outcome: 'SUCCESS'
    })
    CREATE (ep)-[r_svc:AFFECTED]->(svc)
    CREATE (ep)-[r_proc:RESOLVED_BY]->(proc)
    CREATE (ep)-[r_sess:RECORDED_IN_SESSION]->(sess)
    RETURN ep, proc, svc, sess, r_svc, r_proc, r_sess
    """
    params = {
        "session_id": clean_sess,
        "service_name": svc_name,
        "procedure_name": proc_name,
        "proc_id": proc_id,
        "action_steps": action_steps,
        "episode_id": episode_id,
        "symptom": symptom,
        "root_cause": root_cause,
        "timestamp": now_iso,
    }
    try:
        trace_res = manager.query_with_trace(clean_tenant, cypher, params)
        rows, trace = trace_res
    except Exception as e:
        return {
            "data": {
                "episode_id": episode_id,
                "session_id": clean_sess,
                "service_name": svc_name,
                "symptom": symptom,
                "root_cause": root_cause,
                "timestamp": now_iso,
                "outcome": "FAILED",
                "procedure": {
                    "name": proc_name,
                    "execution_count": 0,
                    "success_rate": 0.0,
                    "action_steps": action_steps,
                },
                "status": "FAILED",
                "error": str(e),
                "message": f"Failed to commit episode {episode_id}: {e}",
            },
            "subgraph_trace": {
                "nodes": [],
                "edges": [],
                "cypher_executed": cypher,
                "execution_time_ms": 0.0,
                "error": str(e),
            },
        }

    proc_info = {}
    if rows and "proc" in rows[0]:
        proc_info = rows[0]["proc"].get("properties", {})

    data = {
        "episode_id": episode_id,
        "session_id": clean_sess,
        "service_name": svc_name,
        "symptom": symptom,
        "root_cause": root_cause,
        "timestamp": now_iso,
        "outcome": "SUCCESS",
        "procedure": {
            "name": proc_name,
            "execution_count": proc_info.get("execution_count", 1),
            "success_rate": proc_info.get("success_rate", 1.0),
            "action_steps": proc_info.get("action_steps", action_steps),
        },
        "status": "COMMITTED",
        "message": f"Successfully committed episode {episode_id} and reinforced procedure '{proc_name}'.",
    }

    return {
        "data": data,
        "subgraph_trace": trace,
    }


# =============================================================================
# TOOL REGISTRY: Direct Python access for internal multi-agent orchestrator
# =============================================================================
TOOL_REGISTRY = {
    "analyze_blast_radius_and_commits": {
        "func": analyze_blast_radius_and_commits,
        "track": "Track 1: Agents That Act on Connected Data",
        "description": "Traverse upstream/downstream dependency blast radius and join recent commits and authors.",
    },
    "run_graph_criticality_and_path": {
        "func": run_graph_criticality_and_path,
        "track": "Track 1: Agents That Act on Connected Data",
        "description": "Execute native PageRank centrality and compute shortest failure propagation path.",
    },
    "recall_episodic_and_procedural_memory": {
        "func": recall_episodic_and_procedural_memory,
        "track": "Track 2: Agent Memory & Coordination",
        "description": "Recall past incidents and ranked procedural runbooks by symptom similarity and success rate.",
    },
    "query_company_brain_context": {
        "func": query_company_brain_context,
        "track": "Track 3: Company Brain",
        "description": "Query team ownership, online vs PTO experts, and governing ADR/RFC documentation.",
    },
    "record_agent_handoff": {
        "func": record_agent_handoff,
        "track": "Track 2: Agent Memory & Coordination",
        "description": "Mutate graph to record state transition and handoff between autonomous agents.",
    },
    "commit_new_episode_memory": {
        "func": commit_new_episode_memory,
        "track": "Track 2: Agent Memory & Coordination",
        "description": "Persist resolved incident learning, linking new Episode and reinforcing Procedure.",
    },
}
