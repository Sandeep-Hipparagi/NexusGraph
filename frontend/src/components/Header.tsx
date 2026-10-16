import React from 'react';
import { 
  Network, 
  Database, 
  Cpu, 
  Brain, 
  RotateCcw, 
  Zap, 
  ShieldCheck, 
  Layers, 
  Play,
  Activity
} from 'lucide-react';
import { GraphStats } from '../types';

interface HeaderProps {
  tenantId: string;
  onTenantChange: (tenant: string) => void;
  selectedTrack: string | null;
  onTrackToggle: (track: string) => void;
  onRunScenario: (scenarioNumber: number) => void;
  onResetDemo: () => void;
  stats: GraphStats | null;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  tenantId,
  onTenantChange,
  selectedTrack,
  onTrackToggle,
  onRunScenario,
  onResetDemo,
  stats,
  isLoading,
}) => {
  return (
    <header className="border-b border-slate-800 bg-[#0b1120] px-4 py-2.5 flex flex-col gap-2 shrink-0 shadow-lg z-20">
      {/* Top Bar: Title, Tenant Switcher, Stats & Reset */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Logo and Brand */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500/20 via-purple-500/20 to-emerald-500/20 border border-cyan-500/40 text-cyan-400 shadow-md shadow-cyan-500/10">
            <Network className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                <span>NexusGraph</span>
                <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                  v1.0 // FalkorDB Graph Hacks
                </span>
              </h1>
            </div>
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5 font-mono">
              <span>Autonomous SRE & Company Brain Swarm</span>
              <span className="text-slate-600">•</span>
              <span className="text-purple-400 font-semibold flex items-center gap-1">
                <Database className="w-3 h-3 inline" /> Powered by FalkorDB
              </span>
            </p>
          </div>
        </div>

        {/* Center: Track Filter Pills */}
        <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => onTrackToggle('Track 1')}
            className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
              selectedTrack === 'Track 1'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-sm shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Track 1: Connected Action</span>
          </button>

          <button
            onClick={() => onTrackToggle('Track 2')}
            className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
              selectedTrack === 'Track 2'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/50 shadow-sm shadow-purple-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
            }`}
          >
            <Brain className="w-3.5 h-3.5 text-purple-400" />
            <span>Track 2: Episodic Memory</span>
          </button>

          <button
            onClick={() => onTrackToggle('Track 3')}
            className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
              selectedTrack === 'Track 3'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 shadow-sm shadow-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Track 3: Company Brain</span>
          </button>
        </div>

        {/* Right: Tenant Switcher, Live Stats & Reset */}
        <div className="flex items-center gap-2.5">
          {/* Multi-Tenant Switcher */}
          <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-700/80 rounded-md px-2 py-1 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400 font-mono text-[11px]">Tenant:</span>
            <select
              value={tenantId}
              onChange={(e) => onTenantChange(e.target.value)}
              disabled={isLoading}
              className="bg-transparent text-indigo-300 font-mono font-medium focus:outline-none cursor-pointer text-xs"
            >
              <option value="acme_corp" className="bg-slate-900 text-slate-200">
                nexus_acme_corp (Retail)
              </option>
              <option value="finserve_io" className="bg-slate-900 text-slate-200">
                nexus_finserve_io (FinTech)
              </option>
            </select>
          </div>

          {/* Graph Live Stats Pill */}
          {stats && (
            <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900/90 border border-slate-800 font-mono text-[11px] text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>{stats.node_count} nodes</span>
              <span className="text-slate-600">/</span>
              <span>{stats.edge_count} edges</span>
            </div>
          )}

          {/* Reset Demo */}
          <button
            onClick={onResetDemo}
            disabled={isLoading}
            title="Reset and re-seed clean graphs"
            className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs flex items-center gap-1 transition-colors"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="hidden md:inline font-mono text-[11px]">Reset</span>
          </button>
        </div>
      </div>

      {/* Preset Scenarios Strip */}
      <div className="flex items-center gap-2 pt-1 border-t border-slate-800/60 overflow-x-auto text-xs pb-0.5">
        <span className="text-[11px] font-mono text-cyan-400 font-semibold flex items-center gap-1 shrink-0">
          <Zap className="w-3 h-3 text-cyan-400" /> Demo Scenarios:
        </span>

        <button
          onClick={() => onRunScenario(1)}
          disabled={isLoading}
          className="px-2.5 py-1 rounded-md bg-gradient-to-r from-cyan-950/70 to-slate-900 border border-cyan-800/80 hover:border-cyan-500/80 text-cyan-200 hover:text-white transition-all flex items-center gap-1.5 shrink-0 shadow-sm"
        >
          <Play className="w-3 h-3 text-cyan-400 fill-cyan-400" />
          <span className="font-semibold text-cyan-300">Scenario 1:</span>
          <span>Checkout API 502 Spike (3-Agent Swarm + ADR Citations)</span>
        </button>

        <button
          onClick={() => onRunScenario(2)}
          disabled={isLoading}
          className="px-2.5 py-1 rounded-md bg-gradient-to-r from-purple-950/70 to-slate-900 border border-purple-800/80 hover:border-purple-500/80 text-purple-200 hover:text-white transition-all flex items-center gap-1.5 shrink-0 shadow-sm"
        >
          <Brain className="w-3 h-3 text-purple-400" />
          <span className="font-semibold text-purple-300">Scenario 2:</span>
          <span>Cross-Session Memory Recall (Tests Learned Episode From Scenario 1)</span>
        </button>

        <button
          onClick={() => onRunScenario(3)}
          disabled={isLoading}
          className="px-2.5 py-1 rounded-md bg-gradient-to-r from-emerald-950/70 to-slate-900 border border-emerald-800/80 hover:border-emerald-500/80 text-emerald-200 hover:text-white transition-all flex items-center gap-1.5 shrink-0 shadow-sm"
        >
          <Activity className="w-3 h-3 text-emerald-400" />
          <span className="font-semibold text-emerald-300">Scenario 3:</span>
          <span>Payment-Worker Ownership & Redis Deprecation Impact</span>
        </button>
      </div>
    </header>
  );
};
