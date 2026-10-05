import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Legal Lens 2.0 — Research with provenance",
  description: "Explore a historical legal corpus with hybrid search, grounded answers, page-linked evidence, and downloadable research briefs.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
