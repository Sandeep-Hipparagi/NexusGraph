"""FalkorDB Client & Multi-Tenant Graph Manager for NexusGraph."""

import time
from typing import Any, Dict, List, Optional, Tuple, Union
from falkordb import FalkorDB, Graph, Node, Edge, Path, QueryResult
from backend.config import get_settings


class QueryTraceResult(tuple):
    """Result container supporting both tuple unpacking (rows, trace) and attribute/dict access."""
    def __new__(cls, rows: List[Dict[str, Any]], subgraph_trace: Dict[str, Any]):
        return super().__new__(cls, (rows, subgraph_trace))

    def __init__(self, rows: List[Dict[str, Any]], subgraph_trace: Dict[str, Any]):
        self.rows = rows
        self.subgraph_trace = subgraph_trace

    def __getitem__(self, item: Union[int, str]):
        if isinstance(item, str):
            if item == "rows" or item == "result_rows":
                return self.rows
            if item == "subgraph_trace" or item == "trace":
                return self.subgraph_trace
            raise KeyError(f"Key '{item}' not found. Use 'rows' or 'subgraph_trace'.")
        return super().__getitem__(item)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rows": self.rows,
            "subgraph_trace": self.subgraph_trace,
        }


class FalkorDBManager:
    """Manages isolated tenant graphs and provides explainable query execution tracing."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        username: Optional[str] = None,
    ):
        settings = get_settings()
        self.host = host or settings.falkordb_host
        self.port = port or settings.falkordb_port
        self.password = password if password is not None else settings.falkordb_password
        self.username = username if username is not None else settings.falkordb_username

        self.db = FalkorDB(
            host=self.host,
            port=self.port,
            password=self.password,
            username=self.username,
        )

    def get_graph(self, tenant_id: str) -> Graph:
        """Select an isolated graph for the specified tenant."""
        clean_tenant = str(tenant_id).strip() if tenant_id and str(tenant_id).strip() else "default"
        graph_name = f"nexus_{clean_tenant}" if not clean_tenant.startswith("nexus_") else clean_tenant
        return self.db.select_graph(graph_name)

    def ping(self) -> bool:
        """Verify connectivity to FalkorDB."""
        try:
            return self.db.connection.ping()
        except Exception:
            return False

    def list_tenant_graphs(self) -> List[str]:
        """List all nexus graph keys in FalkorDB."""
        try:
            graphs = self.db.list_graphs()
            return [g for g in graphs if g.startswith("nexus_")]
        except Exception:
            return []

    def delete_tenant_graph(self, tenant_id: str) -> None:
        """Completely drop a tenant's graph."""
        graph = self.get_graph(tenant_id)
        try:
            graph.delete()
        except Exception:
            pass

    def create_index(self, tenant_id: str, label: str, property_name: str) -> None:
        """Create an index on (label.property_name) idempotently."""
        graph = self.get_graph(tenant_id)
        try:
            graph.query(f"CREATE INDEX FOR (n:{label}) ON (n.{property_name})")
        except Exception as e:
            err_msg = str(e).lower()
            if "already indexed" not in err_msg and "already exists" not in err_msg:
                raise

    def _serialize_node(self, node: Node) -> Dict[str, Any]:
        """Convert a FalkorDB Node into a standardized dictionary."""
        return {
            "id": node.id,
            "labels": node.labels if isinstance(node.labels, list) else ([node.labels] if node.labels else []),
            "properties": dict(node.properties) if node.properties else {},
        }

    def _serialize_edge(
        self,
        edge: Edge,
        nodes_map: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Convert a FalkorDB Edge into a standardized dictionary."""
        if isinstance(edge.src_node, Node):
            src_id = edge.src_node.id
            if nodes_map is not None and src_id not in nodes_map:
                nodes_map[src_id] = self._serialize_node(edge.src_node)
        else:
            src_id = edge.src_node

        if isinstance(edge.dest_node, Node):
            dest_id = edge.dest_node.id
            if nodes_map is not None and dest_id not in nodes_map:
                nodes_map[dest_id] = self._serialize_node(edge.dest_node)
        else:
            dest_id = edge.dest_node

        return {
            "id": edge.id,
            "relation": edge.relation,
            "source": src_id,
            "target": dest_id,
            "properties": dict(edge.properties) if edge.properties else {},
        }

    def _serialize_item(
        self,
        item: Any,
        nodes_map: Dict[int, Dict[str, Any]],
        edges_map: Dict[int, Dict[str, Any]],
    ) -> Any:
        """Recursively serialize a query result item and harvest nodes/edges for the trace."""
        if isinstance(item, Node):
            node_dict = self._serialize_node(item)
            nodes_map[item.id] = node_dict
            return node_dict

        if isinstance(item, Edge):
            edge_dict = self._serialize_edge(item, nodes_map)
            edges_map[item.id] = edge_dict
            return edge_dict

        if isinstance(item, Path):
            path_nodes = []
            for n in item.nodes():
                nd = self._serialize_node(n)
                nodes_map[n.id] = nd
                path_nodes.append(nd)

            path_edges = []
            for e in item.edges():
                ed = self._serialize_edge(e, nodes_map)
                edges_map[e.id] = ed
                path_edges.append(ed)

            return {
                "nodes": path_nodes,
                "edges": path_edges,
                "length": len(path_edges),
            }

        if isinstance(item, list):
            return [self._serialize_item(sub, nodes_map, edges_map) for sub in item]

        if isinstance(item, dict):
            return {k: self._serialize_item(v, nodes_map, edges_map) for k, v in item.items()}

        return item

    def query(
        self,
        tenant_id: str,
        cypher: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """Execute a raw Cypher query on the tenant's isolated graph."""
        graph = self.get_graph(tenant_id)
        return graph.query(cypher, params=params)

    def query_with_trace(
        self,
        tenant_id: str,
        cypher: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> QueryTraceResult:
        """
        Execute a Cypher query on a tenant graph and return both:
        1. Structured result rows (list of dictionaries with column names as keys)
        2. Standardized subgraph_trace dictionary (nodes, edges, cypher_executed, execution_time_ms)
        """
        graph = self.get_graph(tenant_id)
        start_time = time.perf_counter()
        
        # Execute query against FalkorDB
        result: QueryResult = graph.query(cypher, params=params)
        end_time = time.perf_counter()

        calc_ms = round((end_time - start_time) * 1000.0, 3)
        execution_time_ms = round(result.run_time_ms, 3) if result.run_time_ms is not None else calc_ms

        # Extract column names from header
        columns: List[str] = []
        if result.header:
            for col in result.header:
                if isinstance(col, (list, tuple)):
                    columns.append(str(col[1]) if len(col) > 1 else str(col[0]))
                else:
                    columns.append(str(col))

        nodes_map: Dict[int, Dict[str, Any]] = {}
        edges_map: Dict[int, Dict[str, Any]] = {}
        rows: List[Dict[str, Any]] = []

        if result.result_set:
            for raw_row in result.result_set:
                row_dict: Dict[str, Any] = {}
                for idx, cell in enumerate(raw_row):
                    col_name = columns[idx] if idx < len(columns) else f"col_{idx}"
                    serialized_cell = self._serialize_item(cell, nodes_map, edges_map)
                    row_dict[col_name] = serialized_cell
                rows.append(row_dict)

        subgraph_trace: Dict[str, Any] = {
            "nodes": list(nodes_map.values()),
            "edges": list(edges_map.values()),
            "cypher_executed": cypher,
            "execution_time_ms": execution_time_ms,
        }

        return QueryTraceResult(rows=rows, subgraph_trace=subgraph_trace)
