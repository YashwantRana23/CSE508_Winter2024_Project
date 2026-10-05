import { sourceUrl } from "@/lib/api";
import type { Source } from "@/types";

interface Brief {
  question: string;
  domain: string;
  mode: string;
  retrievalMethod: string;
  response?: string;
  reason?: string | null;
  sources: Source[];
}

function plainMarkdown(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/([`*_{}[\]<>#|])/g, "\\$1");
}

export function downloadResearchBrief(brief: Brief) {
  const time = new Date();
  const lines = [
    "# Legal Lens 2.0 — Research brief",
    "",
    `Created: ${time.toISOString()}`,
    `Corpus: ${plainMarkdown(brief.domain)}`,
    `Output mode: ${plainMarkdown(brief.mode)}`,
    `Retrieval: ${plainMarkdown(brief.retrievalMethod)}`,
    "",
    "## Scope",
    "Research demo using a bundled historical legal corpus. Coverage is incomplete and is not verified as current law. Check the original source and applicable law before relying on any passage. This brief is not legal advice.",
    "",
    "## Original question",
    plainMarkdown(brief.question),
    "",
  ];
  if (brief.response) lines.push("## Result", plainMarkdown(brief.response), "");
  if (brief.reason) lines.push("Mode note: " + plainMarkdown(brief.reason), "");
  lines.push("## Source evidence", "");
  if (!brief.sources.length) lines.push("No supporting source evidence was returned. Do not treat the result as a supported legal conclusion.", "");
  for (const source of brief.sources) {
    lines.push(
      `### [S${source.rank}] ${plainMarkdown(source.title)} — PDF page ${source.page}`,
      `Source ID: ${plainMarkdown(source.id)}`,
      `Corpus status: ${source.corpus_status}`,
      `Source URL: ${sourceUrl(source.url) ?? "Unavailable"}`,
      "",
      ...plainMarkdown(source.excerpt).split(/\r?\n/).map((line) => `> ${line}`),
      "",
    );
  }
  lines.push("Source URLs refer to the configured application server; localhost links require that server to be running.", "");
  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `legal-lens-brief-${time.toISOString().slice(0, 10)}.md`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
