export interface GraphNode {
  id: number | string;
  labels: string[];
  properties: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  isHighlighted?: boolean;
  isDimmed?: boolean;
  isTarget?: boolean;
}

export interface GraphEdge {
  id: number | string;
  relation: string;
  source: any;
  target: any;
  properties?: Record<string, any>;
  isHighlighted?: boolean;
  isDimmed?: boolean;
}

export interface AgentToolCall {
  tool: string;
  args: Record<string, any>;
}

export interface AgentStep {
  agent_name: string;
  role: string;
  reasoning: string;
  tool_calls: AgentToolCall[];
  cypher_executed: (string | null)[];
  execution_time_ms: number;
  structured_output?: Record<string, any>;
}

export interface SubgraphTrace {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface InvestigationResponse {
  session_id: string;
  tenant_id: string;
  target_service: string;
  query: string;
  total_execution_time_ms: number;
  agent_steps: AgentStep[];
  subgraph: SubgraphTrace;
  final_synthesis: string;
}

export interface GraphStats {
  node_count: number;
  edge_count: number;
  service_count: number;
  active_episodes: number;
  teams_count: number;
  decisions_count: number;
}

export interface GraphTopologyResponse {
  tenant_id: string;
  isolated_tenant_name: string;
  stats: GraphStats;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
