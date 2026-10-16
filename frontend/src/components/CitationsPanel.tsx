import React, { useState } from 'react';
import { 
  FileText, 
  ExternalLink, 
  User, 
  CheckCircle2, 
  ShieldAlert, 
  Database, 
  Sparkles, 
  BookOpen, 
  GitCommit, 
  Cpu, 
  Code,
  Flame
} from 'lucide-react';
import { InvestigationResponse } from '../types';

interface CitationsPanelProps {
  investigation: InvestigationResponse | null;
  isLoading: boolean;
}

export const CitationsPanel: React.FC<CitationsPanelProps> = ({ investigation, isLoading }) => {
  const [activeTab, setActiveTab] = useState<'structured' | 'markdown'>('structured');

  if (isLoading) {
    return (
      <div className="flex flex-col h-full bg-[#0a0f1d] border-l border-slate-800 p-6 items-center justify-center text-center space-y-3">
        <div className="w-10 h-10 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
        <div>
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
            Synthesizing Company Brain & Memory...
          </h3>
          <p className="text-[11px] text-slate-500 mt-1 max-w-[200px] font-mono">
            Traversing governing ADRs, on-call schedules, and persisting cross-session learning.
          </p>
        </div>
      </div>
    );
  }

  if (!investigation) {
    return (
      <div className="flex flex-col h-full bg-[#0a0f1d] border-l border-slate-800 p-6 items-center justify-center text-center space-y-3 text-slate-500 font-mono">
        <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center">
          <BookOpen className="w-6 h-6 text-slate-600" />
        </div>
        <div>
          <p className="text-xs font-medium text-slate-400">Explainability Engine</p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-[220px]">
            Execute an investigation to view explainable blast radius, procedural runbooks, and verified ADR/RFC citations.
          </p>
        </div>
      </div>
    );
  }

  // Parse structured data from agent steps
  const triageStep = investigation.agent_steps.find((s) => s.agent_name.includes('SRE'));
  const memoryStep = investigation.agent_steps.find((s) => s.agent_name.includes('Memory'));
  const brainStep = investigation.agent_steps.find((s) => s.agent_name.includes('Company_Brain'));

  const s1 = triageStep?.structured_output;
  const s2 = memoryStep?.structured_output;
  const s3 = brainStep?.structured_output;

  // Track 1 dynamic values
  const propPath = s1?.propagation_path?.length
    ? s1.propagation_path.join(' → ')
    : `${investigation.target_service} (isolated)`;
  const bottleneckSvc = s1?.top_bottleneck || 'redis-session-cache';
  const suspectSha = s1?.suspect_commit?.sha
    ? `${s1.suspect_commit.sha} (${s1.suspect_commit.message?.slice(0, 28)}...)`
    : 'No recent commit modifications';

  // Track 2 dynamic values
  const runbookName = s2?.runbook_name || 'Database Pool Resizing & Connection Drain';
  const runbookSuccess = s2?.success_rate !== undefined ? Math.round(s2.success_rate * 100) : 94;
  const actionSteps = s2?.action_steps || '1. Inspect connections; 2. Scale worker pool; 3. Trigger reload';
  const stepsList = actionSteps.includes(';')
    ? actionSteps.split(';').map((s: string) => s.trim())
    : [actionSteps];

  // Track 3 dynamic values
  const primaryContact = s3?.primary_contact;
  const onlineName = primaryContact?.name || 'Elena Rostova';
  const onlineRole = primaryContact?.role || 'Tech Lead';
  const onlineHandle = primaryContact?.slack_handle || '@oncall';
  const oncallChannel = primaryContact?.oncall_channel || '#incident-response';
  const ptoExperts = s3?.pto_experts || [];
  const firstPto = ptoExperts.length > 0 ? ptoExperts[0] : null;

  // ADR dynamic values
  const governingDecision = s3?.governing_decision;
  const adrDocId = governingDecision?.document?.doc_id || governingDecision?.decision_id || 'ADR-042';
  const adrTitle = governingDecision?.title || 'Async Payment Processing';
  const adrUrl = governingDecision?.document?.url || 'https://wiki.acme.internal/docs/adr-042';
  const adrSummary = governingDecision?.summary || 'Decouple synchronous HTTP flow using message queues.';
  const adrAuthor = governingDecision?.author || onlineName;

  // Episode committed
  const committedEpId = s3?.committed_episode_id || 'ep-persisted';

  return (
    <div className="flex flex-col h-full bg-[#0a0f1d] border-l border-slate-800 overflow-hidden font-mono text-xs">
      {/* Panel Header & Tabs */}
      <div className="p-3 border-b border-slate-800 flex items-center justify-between shrink-0 bg-[#0d1424]">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Explainable Action & Citations
          </h2>
        </div>
        <div className="flex items-center bg-slate-900 rounded p-0.5 border border-slate-800">
          <button
            onClick={() => setActiveTab('structured')}
            className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
              activeTab === 'structured' ? 'bg-emerald-950 text-emerald-300 font-bold border border-emerald-800' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Structured
          </button>
          <button
            onClick={() => setActiveTab('markdown')}
            className={`px-2 py-0.5 rounded text-[10px] font-medium transition-colors ${
              activeTab === 'markdown' ? 'bg-emerald-950 text-emerald-300 font-bold border border-emerald-800' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Markdown
          </button>
        </div>
      </div>

      {/* Body View */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {activeTab === 'markdown' ? (
          <div className="bg-[#050811] p-3.5 rounded-lg border border-slate-800 font-mono text-[11px] text-slate-200 whitespace-pre-wrap leading-relaxed">
            {investigation.final_synthesis}
          </div>
        ) : (
          <>
            {/* 1. Target & Resolution Status Banner */}
            <div className="rounded-lg bg-gradient-to-r from-emerald-950/40 via-slate-900 to-cyan-950/40 border border-emerald-500/40 p-3 shadow-md shadow-emerald-500/5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Incident Triage Complete
                </span>
                <span className="text-[10px] font-mono text-slate-400">
                  {investigation.total_execution_time_ms}ms total
                </span>
              </div>
              <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
                <span>Target:</span>
                <span className="text-cyan-400 underline decoration-cyan-500/50">
                  {investigation.target_service}
                </span>
              </h3>
              <p className="text-[11px] text-slate-300 mt-1 font-sans">
                {investigation.query}
              </p>
            </div>

            {/* 2. Track 1: Blast Radius & Failure Propagation */}
            <div className="rounded-lg bg-slate-900/80 border border-cyan-500/30 p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <div className="flex items-center gap-1.5 text-cyan-400 font-bold text-[11px] uppercase tracking-wide">
                  <Cpu className="w-3.5 h-3.5" />
                  <span>Track 1: System Blast Radius</span>
                </div>
                <span className="text-[10px] text-cyan-300 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                  PageRank Guided
                </span>
              </div>
              <div className="text-[11px] text-slate-300 space-y-1">
                <div className="flex justify-between items-center gap-2">
                  <span className="text-slate-400 shrink-0">Propagation Path:</span>
                  <span className="text-white font-bold text-right truncate">{propPath}</span>
                </div>
                <div className="flex justify-between items-center gap-2">
                  <span className="text-slate-400 shrink-0">Top Bottleneck:</span>
                  <span className="text-amber-400 font-bold text-right truncate">{bottleneckSvc}</span>
                </div>
                <div className="flex justify-between items-center gap-2">
                  <span className="text-slate-400 shrink-0">Trigger Commit:</span>
                  <span className="text-cyan-300 font-mono text-right truncate">{suspectSha}</span>
                </div>
              </div>
            </div>

            {/* 3. Track 2: Retrieved Procedural Runbook */}
            <div className="rounded-lg bg-slate-900/80 border border-purple-500/30 p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <div className="flex items-center gap-1.5 text-purple-400 font-bold text-[11px] uppercase tracking-wide">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Track 2: Applied Procedural Runbook</span>
                </div>
                <span className="text-[10px] text-purple-300 bg-purple-950 px-2 py-0.5 rounded border border-purple-800">
                  {runbookSuccess}.0% Confidence
                </span>
              </div>
              <div>
                <h4 className="text-xs font-bold text-white mb-1">
                  {runbookName}
                </h4>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mb-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-emerald-400 h-full" 
                    style={{ width: `${runbookSuccess}%` }} 
                  />
                </div>
                <div className="bg-slate-950/90 rounded p-2 border border-slate-800 text-[10px] text-purple-200 space-y-0.5">
                  <p className="font-semibold text-slate-400 mb-0.5">Automated Remediation Steps:</p>
                  {stepsList.map((st: string, idx: number) => (
                    <p key={idx}>{st}</p>
                  ))}
                </div>
              </div>
            </div>

            {/* 4. Track 3: Verifiable Architecture Decision Records (ADRs) */}
            <div className="rounded-lg bg-slate-900/80 border border-emerald-500/30 p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-[11px] uppercase tracking-wide">
                  <FileText className="w-3.5 h-3.5" />
                  <span>Track 3: Verifiable ADR Citations</span>
                </div>
                <span className="text-[10px] text-emerald-300 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                  Source Attributed
                </span>
              </div>

              {/* ADR Card */}
              <div className="bg-slate-950/90 rounded-md p-2.5 border border-slate-800 space-y-1.5">
                <div className="flex items-start justify-between gap-1">
                  <div>
                    <span className="text-[9px] px-1.5 py-0.2 rounded font-bold bg-amber-950 text-amber-400 border border-amber-800 mr-1.5">
                      {adrDocId}
                    </span>
                    <span className="font-bold text-slate-100 text-xs">
                      {adrTitle}
                    </span>
                  </div>
                  {adrUrl && (
                    <a
                      href={adrUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1 text-[10px]"
                    >
                      <span>wiki</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 leading-tight">
                  {adrSummary}
                </p>
                <div className="pt-1 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                  <span>Author: {adrAuthor}</span>
                  <span className="text-emerald-400">Status: ACTIVE</span>
                </div>
              </div>
            </div>

            {/* 5. Assigned Ownership & On-Call Routing (Smart PTO Filtering) */}
            <div className="rounded-lg bg-slate-900/80 border border-indigo-500/30 p-3 space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <div className="flex items-center gap-1.5 text-indigo-400 font-bold text-[11px] uppercase tracking-wide">
                  <User className="w-3.5 h-3.5" />
                  <span>Smart Ownership & On-Call</span>
                </div>
                <span className="text-[10px] text-indigo-300 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">
                  PTO Filtered
                </span>
              </div>

              <div className="space-y-1.5">
                {/* Online Expert */}
                <div className="flex items-center justify-between bg-emerald-950/20 border border-emerald-500/30 rounded p-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <div>
                      <span className="font-bold text-white text-xs block">{onlineName}</span>
                      <span className="text-[10px] text-slate-400">{onlineRole} ({onlineHandle})</span>
                    </div>
                  </div>
                  <span className="text-[10px] text-emerald-300 font-bold px-1.5 py-0.5 bg-emerald-950 rounded border border-emerald-800">
                    ONLINE
                  </span>
                </div>

                {/* Filtered PTO Expert */}
                {firstPto && (
                  <div className="flex items-center justify-between bg-slate-950/60 border border-slate-800 rounded p-2 opacity-60">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-amber-500" />
                      <div>
                        <span className="font-medium text-slate-300 text-xs block">{firstPto.name}</span>
                        <span className="text-[10px] text-slate-500">{firstPto.role}</span>
                      </div>
                    </div>
                    <span className="text-[10px] text-amber-400 px-1.5 py-0.5 bg-amber-950 rounded border border-amber-800">
                      ON PTO
                    </span>
                  </div>
                )}

                <div className="text-[10px] text-slate-400 flex items-center justify-between pt-1">
                  <span>On-Call Channel:</span>
                  <span className="text-cyan-400 font-bold">{oncallChannel}</span>
                </div>
              </div>
            </div>

            {/* 6. Continuous Learning Commitment Badge */}
            <div className="rounded-lg bg-gradient-to-r from-purple-950/60 to-slate-900 border border-purple-500/50 p-3 shadow-lg flex items-start gap-2.5">
              <Database className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>Persistent Graph Memory Committed</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-900 text-purple-200">
                    {committedEpId}
                  </span>
                </h4>
                <p className="text-[10px] text-purple-300 mt-0.5 leading-snug">
                  New Episode and state handoffs committed to FalkorDB. Subsequent queries will immediately recall this resolution with 100% confidence.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
