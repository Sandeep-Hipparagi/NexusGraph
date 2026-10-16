import React, { useState } from 'react';
import { 
  Cpu, 
  Brain, 
  Layers, 
  ChevronDown, 
  ChevronUp, 
  Copy, 
  Check, 
  Focus, 
  Terminal, 
  Clock, 
  Sparkles,
  ArrowRight
} from 'lucide-react';
import { AgentStep } from '../types';

interface AgentStreamProps {
  steps: AgentStep[];
  isLoading: boolean;
  onHighlightAgentStep: (step: AgentStep | null) => void;
  activeHighlightedAgent: string | null;
}

export const AgentStream: React.FC<AgentStreamProps> = ({
  steps,
  isLoading,
  onHighlightAgentStep,
  activeHighlightedAgent,
}) => {
  const [expandedCypher, setExpandedCypher] = useState<Record<number, boolean>>({});
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const toggleCypher = (idx: number) => {
    setExpandedCypher((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const copyCypher = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const getAgentTheme = (agentName: string) => {
    if (agentName.includes('SRE') || agentName.includes('Triage')) {
      return {
        border: 'border-cyan-500/40',
        bg: 'bg-cyan-950/20',
        badgeBg: 'bg-cyan-950 text-cyan-300 border-cyan-700/60',
        glow: 'shadow-cyan-500/10',
        icon: <Cpu className="w-4 h-4 text-cyan-400" />,
        accent: 'text-cyan-400',
        track: 'Track 1',
      };
    }
    if (agentName.includes('Memory')) {
      return {
        border: 'border-purple-500/40',
        bg: 'bg-purple-950/20',
        badgeBg: 'bg-purple-950 text-purple-300 border-purple-700/60',
        glow: 'shadow-purple-500/10',
        icon: <Brain className="w-4 h-4 text-purple-400" />,
        accent: 'text-purple-400',
        track: 'Track 2',
      };
    }
    return {
      border: 'border-emerald-500/40',
      bg: 'bg-emerald-950/20',
      badgeBg: 'bg-emerald-950 text-emerald-300 border-emerald-700/60',
      glow: 'shadow-emerald-500/10',
      icon: <Layers className="w-4 h-4 text-emerald-400" />,
      accent: 'text-emerald-400',
      track: 'Track 3',
    };
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0f1d] border-r border-slate-800 overflow-hidden">
      {/* Stream Header */}
      <div className="p-3 border-b border-slate-800 flex items-center justify-between shrink-0 bg-[#0d1424]">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Multi-Agent Execution Stream
          </h2>
        </div>
        {isLoading ? (
          <span className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800 animate-pulse">
            <Sparkles className="w-3 h-3 animate-spin" /> Swarm Active
          </span>
        ) : (
          <span className="text-[11px] font-mono text-slate-400">
            {steps.length} {steps.length === 1 ? 'Step' : 'Steps'} Logged
          </span>
        )}
      </div>

      {/* Stream Body */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {steps.length === 0 && !isLoading && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center">
              <Terminal className="w-6 h-6 text-slate-600" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-400">Swarm Standby</p>
              <p className="text-[11px] text-slate-500 mt-1 max-w-[220px]">
                Select a preset scenario above or submit an investigation query to trigger the 3-agent swarm.
              </p>
            </div>
          </div>
        )}

        {isLoading && steps.length === 0 && (
          <div className="p-6 text-center space-y-3">
            <div className="w-8 h-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin mx-auto" />
            <p className="text-xs font-mono text-cyan-300">Coordinating 3-Agent Swarm...</p>
          </div>
        )}

        {steps.map((step, idx) => {
          const theme = getAgentTheme(step.agent_name);
          const isHighlighted = activeHighlightedAgent === step.agent_name;
          const cypherQuery = step.cypher_executed.filter(Boolean).join('\n\n');

          return (
            <div
              key={idx}
              className={`rounded-lg border transition-all ${theme.border} ${theme.bg} p-3 relative shadow-md ${theme.glow} ${
                isHighlighted ? 'ring-2 ring-cyan-400/80 bg-slate-900/90' : ''
              }`}
            >
              {/* Step Top Bar: Name, Tool, Latency */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-1 rounded bg-slate-900 border border-slate-800">
                    {theme.icon}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-white tracking-wide">
                        {step.agent_name}
                      </span>
                      <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono font-medium border ${theme.badgeBg}`}>
                        {theme.track}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 font-mono">{step.role}</p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-300 border border-slate-800">
                    <Clock className="w-3 h-3 text-slate-400" />
                    {step.execution_time_ms}ms
                  </span>
                </div>
              </div>

              {/* MCP Tool Calls Chips */}
              <div className="flex flex-wrap gap-1 mb-2.5">
                {step.tool_calls.map((tc, tcIdx) => (
                  <span
                    key={tcIdx}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900/90 text-slate-300 border border-slate-800"
                  >
                    <span className="text-cyan-400">mcp::</span>
                    <span className="font-semibold">{tc.tool}</span>
                  </span>
                ))}
              </div>

              {/* Agent Reasoning */}
              <div className="bg-slate-950/70 rounded p-2.5 border border-slate-800/80 text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-line mb-2.5">
                {step.reasoning}
              </div>

              {/* Actions: Highlight on Graph & View Cypher */}
              <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[11px]">
                <button
                  onClick={() => onHighlightAgentStep(isHighlighted ? null : step)}
                  className={`flex items-center gap-1 px-2 py-0.5 rounded transition-all text-xs font-mono ${
                    isHighlighted
                      ? 'bg-cyan-500 text-slate-950 font-bold'
                      : 'bg-slate-900 text-cyan-400 hover:bg-cyan-950/60 border border-cyan-800/60'
                  }`}
                >
                  <Focus className="w-3 h-3" />
                  <span>{isHighlighted ? 'Clear Path' : 'Highlight Path'}</span>
                </button>

                {cypherQuery && (
                  <button
                    onClick={() => toggleCypher(idx)}
                    className="flex items-center gap-1 text-slate-400 hover:text-slate-200 font-mono text-[11px] transition-colors"
                  >
                    <span>Cypher</span>
                    {expandedCypher[idx] ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </button>
                )}
              </div>

              {/* Collapsible Cypher Code View */}
              {expandedCypher[idx] && cypherQuery && (
                <div className="mt-2.5 pt-2 border-t border-slate-800 relative">
                  <div className="flex items-center justify-between mb-1 text-[10px] font-mono text-slate-400">
                    <span>FalkorDB Cypher Trace:</span>
                    <button
                      onClick={() => copyCypher(cypherQuery, idx)}
                      className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300"
                    >
                      {copiedIndex === idx ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                  <pre className="bg-[#050811] p-2.5 rounded border border-slate-800 text-[10px] font-mono text-cyan-300 overflow-x-auto max-h-40 whitespace-pre-wrap leading-tight">
                    {cypherQuery}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
