import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { AgentStream } from './components/AgentStream';
import { GraphCanvas } from './components/GraphCanvas';
import { NodeInspector } from './components/NodeInspector';
import { CitationsPanel } from './components/CitationsPanel';
import { GraphNode, GraphEdge, GraphStats, InvestigationResponse, AgentStep } from './types';
import { Send, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [tenantId, setTenantId] = useState<string>('acme_corp');
  const [selectedTrack, setSelectedTrack] = useState<string | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [stats, setStats] = useState<GraphStats | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const [investigation, setInvestigation] = useState<InvestigationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [queryInput, setQueryInput] = useState<string>('Critical 504 timeouts on checkout-service flow');
  const [sessionId, setSessionId] = useState<string>(() => `sess-ui-${Date.now().toString(36)}`);

  const [activeHighlightedAgent, setActiveHighlightedAgent] = useState<string | null>(null);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<Set<string | number>>(new Set());
  const [highlightedEdgeIds, setHighlightedEdgeIds] = useState<Set<string | number>>(new Set());

  // Fetch full graph topology from backend
  const fetchGraph = useCallback(async (tenant: string) => {
    try {
      const res = await fetch(`/api/graph/${tenant}`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
      setStats(data.stats || null);
    } catch (err) {
      console.error('Failed to load graph topology:', err);
    }
  }, []);

  useEffect(() => {
    fetchGraph(tenantId);
  }, [tenantId, fetchGraph]);

  // Handle investigation query submission
  const executeInvestigation = async (queryText: string, customSession?: string) => {
    setIsLoading(true);
    setSelectedNode(null);
    setActiveHighlightedAgent(null);

    const activeSession = customSession || sessionId;

    try {
      const res = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: tenantId,
          session_id: activeSession,
          query: queryText,
        }),
      });

      if (!res.ok) {
        throw new Error(`Investigation failed with status ${res.status}`);
      }

      const data: InvestigationResponse = await res.json();
      setInvestigation(data);

      // Highlight the traversed subgraph nodes and edges
      const nodeIds = new Set<string | number>();
      const edgeIds = new Set<string | number>();

      for (const n of data.subgraph.nodes) {
        nodeIds.add(n.id);
        nodeIds.add(String(n.id));
      }
      for (const e of data.subgraph.edges) {
        edgeIds.add(e.id);
        edgeIds.add(String(e.id));
      }

      setHighlightedNodeIds(nodeIds);
      setHighlightedEdgeIds(edgeIds);

      // Refresh graph topology to include any newly committed nodes (e.g. episodes, handoffs)
      await fetchGraph(tenantId);
    } catch (err) {
      console.error('Error running investigation:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Run Preset Scenarios
  const handleRunScenario = (num: number) => {
    if (num === 1) {
      const q = 'Checkout API 502/504 Spike: Inspect blast radius, suspect commits, and ADR citations';
      setQueryInput(q);
      const newSess = `sess-sc1-${Date.now().toString(36)}`;
      setSessionId(newSess);
      executeInvestigation(q, newSess);
    } else if (num === 2) {
      const q = 'Recurring latency spikes on checkout-service: Check past incident episodes and runbooks';
      setQueryInput(q);
      // New session ID proves cross-session recall of memory from Scenario 1!
      const newSess = `sess-sc2-recall-${Date.now().toString(36)}`;
      setSessionId(newSess);
      executeInvestigation(q, newSess);
    } else if (num === 3) {
      const q = 'Who owns payment-worker and what breaks if we deprecate redis-session-cache?';
      setQueryInput(q);
      const newSess = `sess-sc3-${Date.now().toString(36)}`;
      setSessionId(newSess);
      executeInvestigation(q, newSess);
    }
  };

  // Reset Demo
  const handleResetDemo = async () => {
    setIsLoading(true);
    try {
      await fetch('/api/reset-demo', { method: 'POST' });
      setInvestigation(null);
      setHighlightedNodeIds(new Set());
      setHighlightedEdgeIds(new Set());
      setSelectedNode(null);
      setActiveHighlightedAgent(null);
      await fetchGraph(tenantId);
    } catch (err) {
      console.error('Failed to reset demo:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Track filter pill toggle
  const handleTrackToggle = (track: string) => {
    if (selectedTrack === track) {
      setSelectedTrack(null);
      // Revert to investigation subgraph if active
      if (investigation) {
        const nodeIds = new Set(investigation.subgraph.nodes.map((n) => n.id));
        const edgeIds = new Set(investigation.subgraph.edges.map((e) => e.id));
        setHighlightedNodeIds(nodeIds);
        setHighlightedEdgeIds(edgeIds);
      } else {
        setHighlightedNodeIds(new Set());
        setHighlightedEdgeIds(new Set());
      }
      return;
    }

    setSelectedTrack(track);
    const trackLabels =
      track === 'Track 1'
        ? ['Service', 'Commit', 'Incident']
        : track === 'Track 2'
        ? ['Episode', 'Procedure', 'AgentHandoff', 'Session', 'Agent']
        : ['Person', 'Team', 'Decision', 'Document'];

    const filteredNodeIds = new Set<string | number>();
    for (const n of nodes) {
      if (n.labels?.some((l) => trackLabels.includes(l))) {
        filteredNodeIds.add(n.id);
        filteredNodeIds.add(String(n.id));
      }
    }
    setHighlightedNodeIds(filteredNodeIds);
    setHighlightedEdgeIds(new Set());
  };

  // Highlight specific agent step
  const handleHighlightAgentStep = (step: AgentStep | null) => {
    if (!step) {
      setActiveHighlightedAgent(null);
      if (investigation) {
        const nodeIds = new Set(investigation.subgraph.nodes.map((n) => n.id));
        const edgeIds = new Set(investigation.subgraph.edges.map((e) => e.id));
        setHighlightedNodeIds(nodeIds);
        setHighlightedEdgeIds(edgeIds);
      }
      return;
    }

    setActiveHighlightedAgent(step.agent_name);

    // Filter nodes and edges by agent step domain
    let domainLabels: string[] = [];
    if (step.agent_name.includes('SRE')) {
      domainLabels = ['Service', 'Commit', 'Incident', 'AgentHandoff'];
    } else if (step.agent_name.includes('Memory')) {
      domainLabels = ['Episode', 'Procedure', 'Service', 'AgentHandoff'];
    } else {
      domainLabels = ['Person', 'Team', 'Decision', 'Document', 'Episode', 'Service'];
    }

    const stepNodeIds = new Set<string | number>();
    for (const n of investigation?.subgraph.nodes || []) {
      if (n.labels?.some((l) => domainLabels.includes(l))) {
        stepNodeIds.add(n.id);
        stepNodeIds.add(String(n.id));
      }
    }
    setHighlightedNodeIds(stepNodeIds);
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#080c14] text-slate-100 font-sans">
      {/* Top Header */}
      <Header
        tenantId={tenantId}
        onTenantChange={(t) => {
          setTenantId(t);
          setInvestigation(null);
          setHighlightedNodeIds(new Set());
          setHighlightedEdgeIds(new Set());
        }}
        selectedTrack={selectedTrack}
        onTrackToggle={handleTrackToggle}
        onRunScenario={handleRunScenario}
        onResetDemo={handleResetDemo}
        stats={stats}
        isLoading={isLoading}
      />

      {/* Query Bar */}
      <div className="bg-[#0c1222] border-b border-slate-800 px-4 py-2 flex items-center gap-3 shrink-0">
        <div className="flex-1 flex items-center gap-2 bg-[#080c14] border border-slate-700/80 rounded-lg px-3 py-1.5 focus-within:border-cyan-500 shadow-inner">
          <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && executeInvestigation(queryInput)}
            placeholder="Describe an incident, symptom, or architectural query (e.g., 'Checkout 504 timeouts')..."
            className="w-full bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none font-mono"
          />
        </div>

        <button
          onClick={() => executeInvestigation(queryInput)}
          disabled={isLoading || !queryInput.trim()}
          className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 disabled:opacity-50 text-white font-mono text-xs font-bold flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all shrink-0 cursor-pointer"
        >
          {isLoading ? (
            <>
              <div className="w-3.5 h-3.5 rounded-full border-2 border-white border-t-transparent animate-spin" />
              <span>Orchestrating...</span>
            </>
          ) : (
            <>
              <Send className="w-3.5 h-3.5" />
              <span>Investigate</span>
            </>
          )}
        </button>
      </div>

      {/* 3-Column Mission Control Grid */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Multi-Agent Execution Stream */}
        <div className="w-[340px] shrink-0 h-full">
          <AgentStream
            steps={investigation?.agent_steps || []}
            isLoading={isLoading}
            onHighlightAgentStep={handleHighlightAgentStep}
            activeHighlightedAgent={activeHighlightedAgent}
          />
        </div>

        {/* Center Column: Live Interactive FalkorDB Graph Canvas */}
        <div className="flex-1 h-full relative">
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            highlightedNodeIds={highlightedNodeIds}
            highlightedEdgeIds={highlightedEdgeIds}
            onNodeClick={(n) => setSelectedNode(n)}
            selectedNode={selectedNode}
            targetServiceName={investigation?.target_service}
          />

          {/* Node Inspector Floating Drawer */}
          <NodeInspector node={selectedNode} onClose={() => setSelectedNode(null)} />
        </div>

        {/* Right Column: Explainable Action & Citations Panel */}
        <div className="w-[360px] shrink-0 h-full">
          <CitationsPanel investigation={investigation} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default App;
