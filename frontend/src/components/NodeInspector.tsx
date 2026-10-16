import React from 'react';
import { X, Hash, Tag, Layers, Database, ExternalLink } from 'lucide-react';
import { GraphNode } from '../types';

interface NodeInspectorProps {
  node: GraphNode | null;
  onClose: () => void;
}

export const NodeInspector: React.FC<NodeInspectorProps> = ({ node, onClose }) => {
  if (!node) return null;

  const primaryLabel = node.labels?.[0] || 'Node';
  const props = node.properties || {};

  const getTrackBadge = (label: string) => {
    if (['Service', 'Commit', 'Incident'].includes(label)) {
      return { text: 'Track 1: Connected Systems', color: 'bg-cyan-950 text-cyan-300 border-cyan-800' };
    }
    if (['Episode', 'Procedure', 'AgentHandoff', 'Session', 'Agent'].includes(label)) {
      return { text: 'Track 2: Agent Memory', color: 'bg-purple-950 text-purple-300 border-purple-800' };
    }
    return { text: 'Track 3: Company Brain', color: 'bg-emerald-950 text-emerald-300 border-emerald-800' };
  };

  const badge = getTrackBadge(primaryLabel);

  return (
    <div className="absolute bottom-3 right-3 w-80 max-h-[420px] bg-[#0d1424]/95 backdrop-blur-md rounded-xl border border-slate-700/80 shadow-2xl p-4 flex flex-col z-20 overflow-hidden font-mono text-xs">
      {/* Drawer Header */}
      <div className="flex items-start justify-between pb-2.5 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <span className={`text-[10px] px-2 py-0.5 rounded font-medium border ${badge.color}`}>
              {badge.text}
            </span>
            <span className="text-slate-500 text-[10px]">ID: {node.id}</span>
          </div>
          <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-cyan-400" />
            <span>{props.name || props.sha || props.id || props.title || `Node #${node.id}`}</span>
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Node Labels */}
      <div className="py-2 flex items-center gap-1.5 flex-wrap">
        <span className="text-[10px] text-slate-400">Labels:</span>
        {node.labels?.map((lbl, idx) => (
          <span
            key={idx}
            className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-200 border border-slate-700"
          >
            :{lbl}
          </span>
        ))}
      </div>

      {/* Properties Table */}
      <div className="flex-1 overflow-y-auto mt-1 border-t border-slate-800/80 pt-2 space-y-1.5">
        <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
          FalkorDB Properties
        </div>
        {Object.keys(props).length === 0 ? (
          <p className="text-slate-500 italic text-[11px]">No properties stored.</p>
        ) : (
          Object.entries(props).map(([key, value]) => {
            const isUrl = typeof value === 'string' && (value.startsWith('http://') || value.startsWith('https://'));
            return (
              <div key={key} className="bg-slate-900/80 rounded p-1.5 border border-slate-800/60">
                <span className="text-[10px] text-cyan-400 font-semibold block">{key}:</span>
                {isUrl ? (
                  <a
                    href={value}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] text-indigo-400 hover:underline flex items-center gap-1 break-all"
                  >
                    <span>{String(value)}</span>
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                ) : (
                  <span className="text-[11px] text-slate-200 break-words font-sans">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
