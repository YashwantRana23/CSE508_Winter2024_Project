"use client";

import { sourceUrl } from "@/lib/api";
import type { Source } from "@/types";

export function SourceCard({ source, selected, onSelect, compact = false }: { source: Source; selected?: boolean; onSelect: (source: Source) => void; compact?: boolean }) {
  const href = sourceUrl(source.url);
  return (
    <article className={`source-card ${selected ? "is-selected" : ""} ${compact ? "compact" : ""}`}>
      <div className="source-card-top">
        <span className="source-number">S{source.rank}</span>
        <div className="source-heading">
          <h3>{source.title}</h3>
          <p>PDF page {source.page} <span aria-hidden="true">·</span> {source.corpus_status === "historical" ? "Historical source" : "Unverified source"}</p>
        </div>
      </div>
      <p className="source-excerpt">{source.excerpt}</p>
      <div className="source-actions">
        <button type="button" className="text-button" onClick={() => onSelect(source)} aria-pressed={selected}>Read evidence <span aria-hidden="true">→</span></button>
        {href && <a href={href} target="_blank" rel="noopener noreferrer" className="muted-link">Open PDF ↗<span className="sr-only"> in a new tab</span></a>}
      </div>
    </article>
  );
}

export function SourcePanel({ source, onClose }: { source: Source | null; onClose: () => void }) {
  const href = source && sourceUrl(source.url);
  return (
    <aside className="evidence-panel" aria-label="Source evidence" id="source-evidence">
      <div className="panel-heading"><p className="eyebrow">Evidence desk</p>{source && <button type="button" className="text-button" onClick={onClose}>Clear</button>}</div>
      {source ? (
        <>
          <span className="badge amber">{source.corpus_status === "historical" ? "Historical corpus" : "Unverified corpus"}</span>
          <h2>{source.title}</h2>
          <p className="evidence-page">[S{source.rank}] · PDF page {source.page}</p>
          <p className="evidence-copy">{source.excerpt}</p>
          {href && <a className="button secondary full" href={href} target="_blank" rel="noopener noreferrer">Open original PDF ↗<span className="sr-only"> in a new tab</span></a>}
          <p className="fineprint">PDF page numbers may differ from printed page numbers. Verify the surrounding text in the original document.</p>
        </>
      ) : (
        <div className="evidence-empty">
          <div className="book-mark" aria-hidden="true">§</div>
          <h2>Go straight to the source.</h2>
          <p>Select “Read evidence” on any result to inspect its passage and open the original PDF at the cited page.</p>
          <div className="evidence-checks"><span>Page-level provenance</span><span>Original passages</span><span>Explicit corpus scope</span></div>
        </div>
      )}
    </aside>
  );
}
