import { useState, useEffect, useRef } from 'react';
import { getGraph } from '../../utils/api';
import { useShipment } from '../../hooks/useShipment';
import type { GraphData, GraphNode } from '../../types';

interface Props { onTriggerToast: (t: { title: string; message: string; type?: 'error' | 'info' | 'success' }) => void; }

const VIS_OPTIONS = {
  nodes: {
    shape: 'box',
    borderRadius: 8,
    font: { face: 'Inter', size: 12, color: '#f1f5f9' },
    margin: { top: 8, right: 12, bottom: 8, left: 12 },
    shadow: true,
  },
  edges: {
    smooth: { enabled: true, type: 'curvedCW', roundness: 0.2 },
    font: { face: 'Inter', size: 10, color: '#94a3b8', align: 'middle' },
    arrows: { to: { enabled: true, scaleFactor: 0.6 } },
    width: 1.5,
  },
  physics: {
    enabled: true,
    stabilization: { enabled: true, iterations: 200 },
    barnesHut: { gravitationalConstant: -3000, springLength: 140 },
  },
  interaction: {
    hover: true,
    tooltipDelay: 100,
    navigationButtons: false,
    keyboard: false,
  },
};

function nodeColor(node: GraphNode): { background: string; border: string; highlight: { background: string; border: string } } {
  if (node.status === 'conflict') return { background: '#7f1d1d', border: '#f87171', highlight: { background: '#991b1b', border: '#fca5a5' } };
  if (node.status === 'warning') return { background: '#78350f', border: '#fbbf24', highlight: { background: '#92400e', border: '#fcd34d' } };
  if (node.type === 'shipment') return { background: '#312e81', border: '#818cf8', highlight: { background: '#3730a3', border: '#a5b4fc' } };
  if (node.type === 'document') {
    return { background: '#1a2466', border: '#6366f1', highlight: { background: '#252580', border: '#818cf8' } };
  }
  if (node.type === 'canonical_field') return { background: '#581c87', border: '#c084fc', highlight: { background: '#6b21a8', border: '#d8b4fe' } };
  return { background: '#14402e', border: '#10b981', highlight: { background: '#1a5c40', border: '#34d399' } };
}

export function ScreenKnowledgeGraph({ onTriggerToast }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { shipmentId } = useShipment();
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);

  const activeId = shipmentId ?? 'demo-shipment';

  // Fetch graph data
  useEffect(() => {
    setLoading(true);
    setError(null);
    getGraph(activeId)
      .then(data => {
        setGraphData(data);
        setNodeCount(data.nodes.length);
        setEdgeCount(data.edges.length);
      })
      .catch(err => setError(err.message || 'Failed to load graph from backend.'))
      .finally(() => setLoading(false));
  }, [activeId]);

  // Render vis.js network
  useEffect(() => {
    if (!graphData || !containerRef.current || loading) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let network: any = null;

    import('vis-network').then(({ Network }) => {
      import('vis-data').then(({ DataSet }) => {
        if (!containerRef.current) return;

        const nodes = new DataSet(
          graphData.nodes.map(n => ({
            id: n.id,
            label: n.label,
            color: nodeColor(n),
            title: `Type: ${n.type}\nID: ${n.id}`,
            shape: n.type === 'shipment' ? 'diamond' : n.type === 'document' ? 'box' : n.type === 'canonical_field' ? 'hexagon' : 'ellipse',
            font: { color: '#f1f5f9', face: 'Inter', size: 12 },
          }))
        );

        const edges = new DataSet(
          graphData.edges.map((e, i) => ({
            id: `edge_${i}`,
            from: e.from,
            to: e.to,
            label: e.label || '',
            color: e.label === 'ASSERTS_VALUE_FOR'
              ? { color: '#c084fc', highlight: '#d8b4fe' }
              : e.label === 'HAS_FIELD' ? { color: '#818cf8', highlight: '#a5b4fc' }
              : { color: '#475569', highlight: '#94a3b8' },
            dashes: e.label === 'CONTAINS',
            width: e.label === 'ASSERTS_VALUE_FOR' || e.label === 'HAS_FIELD' ? 2 : 1.5,
          }))
        );

        network = new Network(containerRef.current!, { nodes, edges }, VIS_OPTIONS);

        network.on('selectNode', (params: { nodes: string[] }) => {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const found = graphData.nodes.find(n => n.id === nodeId);
            if (found) setSelectedNode(found);
          }
        });

        network.on('deselectNode', () => setSelectedNode(null));
      });
    });

    return () => {
      network?.destroy();
    };
  }, [graphData, loading]);

  const handleExport = () => {
    if (!graphData) return;
    const blob = new Blob([JSON.stringify(graphData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `graph_${activeId.slice(0, 8)}.json`;
    a.click(); URL.revokeObjectURL(url);
    onTriggerToast({ title: 'Graph Exported', message: 'Full node JSON-LD downloaded.', type: 'success' });
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-8 py-8 flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-semibold text-primary">Document relationships</div>
          <h1 className="text-2xl font-bold text-on-surface tracking-tight mt-1">Knowledge graph</h1>
          <p className="text-xs md:text-sm text-on-surface-variant mt-1">See how documents, extracted values, and resolved CUSDEC fields relate.</p>
        </div>
        <button onClick={handleExport} className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold bg-primary text-white rounded-lg shadow-sm hover:bg-primary/90">
          <span className="material-symbols-outlined text-[16px]">download</span>
          <span>Export Graph JSON</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-10 gap-6 items-start">
        {/* Graph Canvas */}
        <div className="lg:col-span-7 bg-surface-container-lowest rounded-xl border border-outline-variant/30 shadow-sm relative overflow-hidden min-h-[540px] flex flex-col">
          <div className="p-3 border-b border-outline-variant/30 bg-surface-container-low/50 flex items-center justify-between text-xs">
            <span className="font-semibold text-on-surface">{nodeCount} Nodes • {edgeCount} Edges</span>
            <div className="flex items-center gap-3 text-[11px] text-on-surface-variant font-medium">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rotate-45 bg-indigo-400"></span> Shipment</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[#6366f1]"></span> Document</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 bg-purple-400"></span> Canonical Field</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#10b981]"></span> Source Assertion</span>
            </div>
          </div>

          {loading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3 text-on-surface-variant">
                <span className="material-symbols-outlined text-[40px] animate-spin text-primary">sync</span>
                <span className="text-sm">Loading knowledge graph...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center">
                <span className="material-symbols-outlined text-error text-[40px]">error</span>
                <p className="text-sm text-on-surface mt-2 font-semibold">Failed to load graph</p>
                <p className="text-xs text-on-surface-variant mt-1">{error}</p>
              </div>
            </div>
          )}

          <div
            ref={containerRef}
            className={`flex-1 w-full min-h-[480px] ${loading || error ? 'hidden' : ''}`}
            style={{ background: 'radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%)' }}
          />
        </div>

        {/* Inspector Panel */}
        <div className="lg:col-span-3 bg-surface-container-lowest p-5 rounded-xl border border-outline-variant/30 shadow-sm flex flex-col gap-4 text-xs">
          <div className="border-b border-outline-variant/20 pb-3 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-outline">Selected item</span>
              <h2 className="text-sm font-bold text-on-surface">{selectedNode ? selectedNode.label : 'Select an item'}</h2>
            </div>
            {selectedNode && (
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${selectedNode.type === 'document' ? 'bg-primary-fixed text-primary' : 'bg-secondary-container/30 text-secondary'}`}>
                {selectedNode.type}
              </span>
            )}
          </div>

          {selectedNode ? (
            <div className="bg-surface-container-low p-3 rounded-lg space-y-2">
              <div className="flex justify-between"><span className="text-outline">Node ID:</span><span className="font-semibold font-mono text-on-surface text-[10px]">{selectedNode.id}</span></div>
              <div className="flex justify-between"><span className="text-outline">Type:</span><span className="font-semibold text-on-surface">{selectedNode.type}</span></div>
              {selectedNode.document_type && (
                <div className="flex justify-between"><span className="text-outline">Doc Type:</span><span className="font-semibold text-on-surface">{selectedNode.document_type}</span></div>
              )}
            </div>
          ) : (
            <div className="bg-surface-container-low p-3 rounded-lg flex flex-col items-center gap-2 py-8">
              <span className="material-symbols-outlined text-outline text-[32px]">touch_app</span>
              <p className="text-on-surface-variant text-center">Select an item in the graph to view its details and source document.</p>
            </div>
          )}

          {/* Legend */}
          <div className="border-t border-outline-variant/20 pt-3 space-y-2">
            <div className="text-[10px] text-outline font-semibold">Relationships</div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-0.5 bg-purple-400"></div>
              <span className="text-on-surface-variant">Assertion contributes to canonical field</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-0.5 bg-[#475569] border-dashed border-t"></div>
              <span className="text-on-surface-variant">Document contains source assertion</span>
            </div>
          </div>

          <button
            onClick={() => { setLoading(true); getGraph(activeId).then(d => { setGraphData(d); setNodeCount(d.nodes.length); setEdgeCount(d.edges.length); }).finally(() => setLoading(false)); }}
            className="w-full py-2.5 rounded-lg bg-primary hover:bg-primary/90 text-white font-semibold flex items-center justify-center gap-1.5 shadow-sm text-xs"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
            <span>Refresh Graph</span>
          </button>
        </div>
      </div>
    </div>
  );
}
