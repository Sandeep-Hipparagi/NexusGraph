import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  RotateCcw, 
  Search, 
  Eye, 
  EyeOff, 
  Sparkles,
  Info
} from 'lucide-react';
import { GraphNode, GraphEdge } from '../types';

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNodeIds: Set<string | number>;
  highlightedEdgeIds: Set<string | number>;
  onNodeClick: (node: GraphNode) => void;
  selectedNode: GraphNode | null;
  targetServiceName?: string;
}

// Domain colors
const LABEL_COLORS: Record<string, { fill: string; stroke: string; track: string }> = {
  Service: { fill: '#0891b2', stroke: '#06b6d4', track: 'Track 1' },
  Commit: { fill: '#ea580c', stroke: '#f97316', track: 'Track 1' },
  Incident: { fill: '#dc2626', stroke: '#ef4444', track: 'Track 1' },
  Episode: { fill: '#7e22ce', stroke: '#a855f7', track: 'Track 2' },
  Procedure: { fill: '#c026d3', stroke: '#e879f9', track: 'Track 2' },
  AgentHandoff: { fill: '#e11d48', stroke: '#fb7185', track: 'Track 2' },
  Agent: { fill: '#4f46e5', stroke: '#818cf8', track: 'Track 2' },
  Session: { fill: '#334155', stroke: '#64748b', track: 'Track 2' },
  Person: { fill: '#059669', stroke: '#10b981', track: 'Track 3' },
  Team: { fill: '#4338ca', stroke: '#6366f1', track: 'Track 3' },
  Decision: { fill: '#0284c7', stroke: '#38bdf8', track: 'Track 3' },
  Document: { fill: '#d97706', stroke: '#fbbf24', track: 'Track 3' },
};

const DEFAULT_COLOR = { fill: '#475569', stroke: '#94a3b8', track: 'Other' };

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes,
  edges,
  highlightedNodeIds,
  highlightedEdgeIds,
  onNodeClick,
  selectedNode,
  targetServiceName,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Viewport transformation: scale (zoom) and translation (pan)
  const [transform, setTransform] = useState({ scale: 0.9, x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [draggedNode, setDraggedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showLegend, setShowLegend] = useState(true);

  // Physics simulation nodes
  const simNodesRef = useRef<GraphNode[]>([]);
  const animFrameRef = useRef<number | null>(null);
  const glowTickRef = useRef<number>(0);

  // Synchronize incoming nodes into local simulation nodes preserving positions
  useEffect(() => {
    const existingMap = new Map(simNodesRef.current.map((n) => [String(n.id), n]));
    const container = containerRef.current;
    const width = container ? container.clientWidth : 800;
    const height = container ? container.clientHeight : 600;

    const updated = nodes.map((n, i) => {
      const key = String(n.id);
      const existing = existingMap.get(key);
      if (existing) {
        return {
          ...n,
          x: existing.x,
          y: existing.y,
          vx: existing.vx,
          vy: existing.vy,
        };
      }
      // Initial radial dispersion
      const angle = (i / Math.max(nodes.length, 1)) * 2 * Math.PI;
      const radius = 180 + Math.random() * 120;
      return {
        ...n,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
      };
    });

    simNodesRef.current = updated;
  }, [nodes]);

  // Force layout physics step
  const tickPhysics = useCallback(() => {
    const simNodes = simNodesRef.current;
    if (!simNodes.length) return;

    const nodeMap = new Map<string, GraphNode>();
    for (const n of simNodes) {
      nodeMap.set(String(n.id), n);
    }

    // 1. Repulsion force between all pairs
    const repulsion = 1200;
    for (let i = 0; i < simNodes.length; i++) {
      const a = simNodes[i];
      for (let j = i + 1; j < simNodes.length; j++) {
        const b = simNodes[j];
        const dx = (b.x || 0) - (a.x || 0);
        const dy = (b.y || 0) - (a.y || 0);
        const distSq = dx * dx + dy * dy + 1;
        const dist = Math.sqrt(distSq);

        if (dist < 400) {
          const force = repulsion / distSq;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (!a.fx) {
            a.vx = (a.vx || 0) - fx;
            a.vy = (a.vy || 0) - fy;
          }
          if (!b.fx) {
            b.vx = (b.vx || 0) + fx;
            b.vy = (b.vy || 0) + fy;
          }
        }
      }
    }

    // 2. Link attraction along edges
    const idealDist = 90;
    const linkStrength = 0.05;
    for (const edge of edges) {
      const srcId = typeof edge.source === 'object' ? String(edge.source.id) : String(edge.source);
      const tgtId = typeof edge.target === 'object' ? String(edge.target.id) : String(edge.target);
      const srcNode = nodeMap.get(srcId);
      const tgtNode = nodeMap.get(tgtId);

      if (srcNode && tgtNode) {
        const dx = (tgtNode.x || 0) - (srcNode.x || 0);
        const dy = (tgtNode.y || 0) - (srcNode.y || 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const diff = dist - idealDist;
        const force = diff * linkStrength;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        if (!srcNode.fx) {
          srcNode.vx = (srcNode.vx || 0) + fx;
          srcNode.vy = (srcNode.vy || 0) + fy;
        }
        if (!tgtNode.fx) {
          tgtNode.vx = (tgtNode.vx || 0) - fx;
          tgtNode.vy = (tgtNode.vy || 0) - fy;
        }
      }
    }

    // 3. Centering force & damping
    const container = containerRef.current;
    const cx = container ? container.clientWidth / 2 : 400;
    const cy = container ? container.clientHeight / 2 : 300;
    const centerStrength = 0.005;
    const damping = 0.88;

    for (const n of simNodes) {
      if (!n.fx) {
        n.vx = ((n.vx || 0) + (cx - (n.x || 0)) * centerStrength) * damping;
        n.vy = ((n.vy || 0) + (cy - (n.y || 0)) * centerStrength) * damping;

        n.x = (n.x || 0) + (n.vx || 0);
        n.y = (n.y || 0) + (n.vy || 0);
      }
    }
  }, [edges]);

  // Main canvas render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let isRunning = true;

    const render = () => {
      if (!isRunning) return;
      glowTickRef.current += 0.05;
      tickPhysics();

      // Ensure canvas pixel ratio matches container
      const container = containerRef.current;
      if (container) {
        const dpr = window.devicePixelRatio || 1;
        const w = container.clientWidth;
        const h = container.clientHeight;
        if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
          canvas.width = w * dpr;
          canvas.height = h * dpr;
        }
      }

      const dpr = window.devicePixelRatio || 1;
      ctx.save();
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Apply viewport transformation
      ctx.scale(dpr, dpr);
      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.scale, transform.scale);

      // Draw subtle background grid
      const gridSize = 40;
      ctx.strokeStyle = '#0f172a';
      ctx.lineWidth = 0.5;
      const startX = -transform.x / transform.scale - 200;
      const endX = startX + (canvas.width / dpr) / transform.scale + 400;
      const startY = -transform.y / transform.scale - 200;
      const endY = startY + (canvas.height / dpr) / transform.scale + 400;

      ctx.beginPath();
      for (let x = Math.floor(startX / gridSize) * gridSize; x < endX; x += gridSize) {
        ctx.moveTo(x, startY);
        ctx.lineTo(x, endY);
      }
      for (let y = Math.floor(startY / gridSize) * gridSize; y < endY; y += gridSize) {
        ctx.moveTo(startX, y);
        ctx.lineTo(endX, y);
      }
      ctx.stroke();

      const nodeMap = new Map<string, GraphNode>();
      for (const n of simNodesRef.current) {
        nodeMap.set(String(n.id), n);
      }

      const hasHighlights = highlightedNodeIds.size > 0;

      // -------------------------------------------------------------
      // DRAW EDGES
      // -------------------------------------------------------------
      for (const edge of edges) {
        const srcId = typeof edge.source === 'object' ? String(edge.source.id) : String(edge.source);
        const tgtId = typeof edge.target === 'object' ? String(edge.target.id) : String(edge.target);
        const srcNode = nodeMap.get(srcId);
        const tgtNode = nodeMap.get(tgtId);

        if (!srcNode || !tgtNode || srcNode.x === undefined || srcNode.y === undefined || tgtNode.x === undefined || tgtNode.y === undefined) {
          continue;
        }

        const isEdgeHighlighted =
          highlightedEdgeIds.has(edge.id) ||
          (highlightedNodeIds.has(srcId) && highlightedNodeIds.has(tgtId));

        ctx.save();
        if (hasHighlights) {
          if (isEdgeHighlighted) {
            // Animated pulsing glowing edge
            const pulse = 2.5 + Math.sin(glowTickRef.current * 3) * 1.2;
            ctx.strokeStyle = '#06b6d4';
            ctx.lineWidth = pulse;
            ctx.shadowColor = '#06b6d4';
            ctx.shadowBlur = 12;
            ctx.globalAlpha = 0.95;
          } else {
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 1;
            ctx.globalAlpha = 0.15; // Dimmed to 15-20%
          }
        } else {
          ctx.strokeStyle = '#334155';
          ctx.lineWidth = 1.2;
          ctx.globalAlpha = 0.45;
        }

        ctx.beginPath();
        ctx.moveTo(srcNode.x, srcNode.y);
        ctx.lineTo(tgtNode.x, tgtNode.y);
        ctx.stroke();

        // Draw directional arrow on edge
        const dx = tgtNode.x - srcNode.x;
        const dy = tgtNode.y - srcNode.y;
        const angle = Math.atan2(dy, dx);
        const arrowDist = Math.max(20, Math.sqrt(dx * dx + dy * dy) - 22);
        const arrowX = srcNode.x + Math.cos(angle) * arrowDist;
        const arrowY = srcNode.y + Math.sin(angle) * arrowDist;

        ctx.beginPath();
        ctx.moveTo(arrowX, arrowY);
        ctx.lineTo(
          arrowX - 8 * Math.cos(angle - Math.PI / 6),
          arrowY - 8 * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          arrowX - 8 * Math.cos(angle + Math.PI / 6),
          arrowY - 8 * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();

        ctx.restore();
      }

      // -------------------------------------------------------------
      // DRAW NODES
      // -------------------------------------------------------------
      for (const node of simNodesRef.current) {
        if (node.x === undefined || node.y === undefined) continue;

        const primaryLabel = node.labels?.[0] || 'Unknown';
        const color = LABEL_COLORS[primaryLabel] || DEFAULT_COLOR;
        const isHighlighted = highlightedNodeIds.has(node.id) || highlightedNodeIds.has(String(node.id));
        const isSelected = selectedNode && String(selectedNode.id) === String(node.id);
        const isTarget = targetServiceName && node.properties?.name === targetServiceName;

        const radius = isTarget ? 20 : isSelected ? 18 : isHighlighted ? 16 : 14;

        ctx.save();

        if (hasHighlights) {
          if (isHighlighted || isTarget) {
            // Traversed subgraph glow ring
            const pulse = 4 + Math.sin(glowTickRef.current * 4) * 3;
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius + pulse, 0, Math.PI * 2);
            ctx.fillStyle = color.stroke;
            ctx.globalAlpha = 0.25;
            ctx.fill();

            ctx.globalAlpha = 1.0;
            ctx.shadowColor = color.stroke;
            ctx.shadowBlur = 18;
          } else {
            ctx.globalAlpha = 0.2; // Dim non-traversed nodes to 20%
          }
        } else {
          ctx.globalAlpha = 0.9;
        }

        // Base circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color.fill;
        ctx.fill();

        ctx.lineWidth = isSelected ? 3 : isHighlighted ? 2.5 : 1.5;
        ctx.strokeStyle = isSelected ? '#ffffff' : color.stroke;
        ctx.stroke();

        // Node Label Text
        const nodeName =
          node.properties?.name ||
          node.properties?.sha ||
          node.properties?.id ||
          node.properties?.title ||
          String(node.id);

        const shortText = String(nodeName).slice(0, 16);

        ctx.font = isHighlighted || isSelected ? 'bold 11px JetBrains Mono' : '10px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';

        // Background pill for label
        const textMetrics = ctx.measureText(shortText);
        const padding = 3;
        ctx.fillStyle = 'rgba(10, 15, 29, 0.85)';
        ctx.fillRect(
          node.x - textMetrics.width / 2 - padding,
          node.y + radius + 3,
          textMetrics.width + padding * 2,
          14
        );

        ctx.fillStyle = isHighlighted || isSelected ? '#ffffff' : '#cbd5e1';
        ctx.fillText(shortText, node.x, node.y + radius + 4);

        // Track badge indicator dot on node center
        ctx.beginPath();
        ctx.arc(node.x, node.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        ctx.restore();
      }

      ctx.restore();
      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      isRunning = false;
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [edges, transform, highlightedNodeIds, highlightedEdgeIds, selectedNode, targetServiceName, tickPhysics]);

  // Mouse interaction: Node Dragging, Panning & Clicking
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Convert mouse coordinates to world coordinates
    const worldX = (mouseX - transform.x) / transform.scale;
    const worldY = (mouseY - transform.y) / transform.scale;

    // Check hit on any node
    for (const node of simNodesRef.current) {
      if (node.x !== undefined && node.y !== undefined) {
        const dist = Math.hypot(node.x - worldX, node.y - worldY);
        if (dist <= 22) {
          node.fx = node.x;
          node.fy = node.y;
          setDraggedNode(node);
          onNodeClick(node);
          return;
        }
      }
    }

    // Otherwise start canvas panning
    setIsDragging(true);
    setDragStart({ x: mouseX - transform.x, y: mouseY - transform.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (draggedNode) {
      draggedNode.fx = (mouseX - transform.x) / transform.scale;
      draggedNode.fy = (mouseY - transform.y) / transform.scale;
      draggedNode.x = draggedNode.fx;
      draggedNode.y = draggedNode.fy;
      return;
    }

    if (isDragging) {
      setTransform((prev) => ({
        ...prev,
        x: mouseX - dragStart.x,
        y: mouseY - dragStart.y,
      }));
      return;
    }

    // Hover detection for cursor styling
    const worldX = (mouseX - transform.x) / transform.scale;
    const worldY = (mouseY - transform.y) / transform.scale;
    let found: GraphNode | null = null;
    for (const node of simNodesRef.current) {
      if (node.x !== undefined && node.y !== undefined) {
        if (Math.hypot(node.x - worldX, node.y - worldY) <= 22) {
          found = node;
          break;
        }
      }
    }
    setHoveredNode(found);
  };

  const handleMouseUp = () => {
    if (draggedNode) {
      draggedNode.fx = null;
      draggedNode.fy = null;
      setDraggedNode(null);
    }
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform((prev) => {
      const newScale = Math.max(0.2, Math.min(prev.scale * zoomFactor, 3.5));
      return { ...prev, scale: newScale };
    });
  };

  const handleResetView = () => {
    const container = containerRef.current;
    const w = container ? container.clientWidth : 800;
    const h = container ? container.clientHeight : 600;
    setTransform({ scale: 0.85, x: w * 0.08, y: h * 0.08 });
  };

  const handleZoom = (direction: 'in' | 'out') => {
    setTransform((prev) => {
      const factor = direction === 'in' ? 1.2 : 0.8;
      const newScale = Math.max(0.2, Math.min(prev.scale * factor, 3.5));
      return { ...prev, scale: newScale };
    });
  };

  // Search node focus
  const handleSearchSelect = (query: string) => {
    if (!query.trim()) return;
    const match = simNodesRef.current.find((n) => {
      const name = String(n.properties?.name || n.properties?.id || n.properties?.sha || '').toLowerCase();
      return name.includes(query.toLowerCase());
    });
    if (match && match.x !== undefined && match.y !== undefined) {
      const container = containerRef.current;
      const w = container ? container.clientWidth : 800;
      const h = container ? container.clientHeight : 600;
      setTransform({
        scale: 1.3,
        x: w / 2 - match.x * 1.3,
        y: h / 2 - match.y * 1.3,
      });
      onNodeClick(match);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full h-full bg-[#080c14] overflow-hidden select-none">
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        className={`w-full h-full block ${
          hoveredNode ? 'cursor-pointer' : isDragging ? 'cursor-grabbing' : 'cursor-grab'
        }`}
      />

      {/* Floating Canvas Controls */}
      <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-[#0b1120]/90 backdrop-blur-md p-1.5 rounded-lg border border-slate-800 shadow-xl z-10">
        <button
          onClick={() => handleZoom('in')}
          title="Zoom In"
          className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={() => handleZoom('out')}
          title="Zoom Out"
          className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetView}
          title="Reset View"
          className="p-1.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <div className="w-[1px] h-4 bg-slate-800 mx-1" />
        <button
          onClick={() => setShowLegend(!showLegend)}
          title="Toggle Domain Legend"
          className={`p-1.5 rounded transition-colors ${
            showLegend ? 'bg-cyan-950 text-cyan-400 border border-cyan-800' : 'text-slate-400 hover:bg-slate-800'
          }`}
        >
          {showLegend ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
        </button>
      </div>

      {/* Node Search Bar */}
      <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-[#0b1120]/90 backdrop-blur-md px-2.5 py-1.5 rounded-lg border border-slate-800 shadow-xl z-10">
        <Search className="w-3.5 h-3.5 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearchSelect(searchQuery)}
          placeholder="Search node or service..."
          className="bg-transparent text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none w-36 sm:w-48"
        />
      </div>

      {/* Domain Color Legend Overlay */}
      {showLegend && (
        <div className="absolute bottom-3 left-3 bg-[#0b1120]/90 backdrop-blur-md p-3 rounded-lg border border-slate-800 shadow-xl z-10 max-w-xs text-xs font-mono">
          <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
            <span>FalkorDB Domain Legend</span>
            <span className="text-[9px] text-cyan-400">Force Layout</span>
          </div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[11px]">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 shadow-sm shadow-cyan-500" />
              <span className="text-slate-300">Service (T1)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
              <span className="text-slate-300">Commit (T1)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
              <span className="text-slate-300">Incident (T1)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-500 shadow-sm shadow-purple-500" />
              <span className="text-slate-300">Episode (T2)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-fuchsia-500" />
              <span className="text-slate-300">Procedure (T2)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
              <span className="text-slate-300">Handoff (T2)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500" />
              <span className="text-slate-300">Person (T3)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
              <span className="text-slate-300">Team (T3)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
              <span className="text-slate-300">Decision (T3)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span className="text-slate-300">Document (T3)</span>
            </div>
          </div>
          {highlightedNodeIds.size > 0 && (
            <div className="mt-2 pt-2 border-t border-slate-800 text-[10px] text-cyan-400 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-cyan-400 animate-spin" />
              <span>{highlightedNodeIds.size} reasoning nodes highlighted (rest dimmed)</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
