"use client";

import { useEffect, useRef } from "react";

interface Node {
  id: string;
  label: string;
  rank: number;
  avg_similarity: number;
}

interface Edge {
  source: string;
  target: string;
  weight: number;
}

export function KnowledgeGraphViz({ nodes, edges }: { nodes: Node[]; edges: Edge[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    let cancelled = false;
    let network: { destroy: () => void } | null = null;
    const loadVis = async () => {
      const [{ DataSet }, { Network }] = await Promise.all([
        import("vis-data"),
        import("vis-network"),
      ]);

      const visNodes = new DataSet(
        nodes.map((n) => ({
          id: n.id,
          label: (n.label?.slice(0, 30) ?? "") + (n.label && n.label.length > 30 ? "…" : "") || n.id,
          color: n.rank === 1 ? "#dc2626" : n.rank === 2 ? "#16a34a" : n.rank === 3 ? "#e2e8f0" : "#3b82f6",
          font: { size: 12 },
        }))
      );
      const visEdges = new DataSet(
        edges.map((e, i) => ({
          id: i,
          from: e.source,
          to: e.target,
          value: Math.max(0.1, e.weight),
        }))
      );

      const data = { nodes: visNodes, edges: visEdges };
      const options = {
        nodes: { shape: "dot", size: 16 },
        edges: { width: 0.5 },
        physics: {
          enabled: true,
          barnesHut: {
            gravitationalConstant: -3000,
            centralGravity: 0.1,
            springLength: 120,
          },
        },
        height: "400px",
      };

      if (cancelled || !containerRef.current) return;
      network = new Network(containerRef.current, data, options);
    };

    loadVis();
    return () => {
      cancelled = true;
      if (network && "destroy" in network) (network as { destroy: () => void }).destroy();
    };
  }, [nodes, edges]);

  if (nodes.length === 0) {
    return (
      <div className="flex h-[400px] items-center justify-center text-slate-500">
        No graph data. Run search and click &quot;Process → Knowledge Graph&quot;.
      </div>
    );
  }

  return <div ref={containerRef} className="h-[400px] w-full" />;
}
