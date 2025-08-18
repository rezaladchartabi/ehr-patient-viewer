/**
 * heading-first, sentence-aware chunker for clinical notes
 *
 * Drop-in for your RAG ingestion. Designed for ED-style notes like your Column H.
 * - Splits by common clinical headings first
 * - Keeps vitals lines intact when detected
 * - Packs sentences into ~targetTokens with overlapTokens budget
 * - Returns clean chunks with section and positions
 *
 * Usage
 * import { chunkClinicalNote, DEFAULT_HEADINGS } from "./chunker";
 * const chunks = chunkClinicalNote(noteText, {
 *   headings: DEFAULT_HEADINGS,
 *   targetTokens: 700,
 *   overlapTokens: 75,
 *   keepVitalsLines: true,
 * });
 */

export type Chunk = {
    section: string;         // e.g., "History of Present Illness"
    position: number;        // order within the note
    content: string;         // chunk text
    tokenCount: number;      // approximate tokens
    noteLocalId?: string;    // optional caller-provided id
  };
  
  export const DEFAULT_HEADINGS = [
    // Canonical
    "Service line",
    "Chief Complaint",
    "History of Present Illness",
    "Vital signs",
    "Review of Systems",
    "Past Medical History",
    "Past Surgical History",
    "Family History",
    "Social History",
    "Allergies",
    "Physical Exam",
    "Labs",
    "Imaging and Studies",
    "Findings",
    "Impression",
    "Brief Hospital Course",
    "Assessment and Plan",
    "Procedures",
    "Acute Issues",
    "Chronic Issues",
    "Medications During Admission",
    "Medications at Discharge",
    "Discharge Diagnosis",
    "Discharge Condition",
    "Discharge Instructions",
    "Follow Up",
    // Legacy/extra to match incoming text
    "HPI",
    "Admission Diagnosis",
    "Hospital Course",
    "Medications",
    "Discharge Medications",
    "Follow-Up",
    "Imaging",
    "Problem List",
    "Instructions",
    "Imaging / studies",
    "Imaging and studies",
    "Review of systems",
    "Past medical history",
    "Family history",
    "Social history",
    "Physical exam",
    "Medication",
    "medications during admission",
    "medication during discharge",
    "Discharge instruction"
  ];
  
  // Map synonyms/variants to canonical labels
  export const SYNONYM_TO_CANON: Record<string, string> = {
    "Serviceline": "Service line",
    "HPI": "History of Present Illness",
    "Vital signs": "Vital signs",
    "Review of systems": "Review of Systems",
    "Past medical history": "Past Medical History",
    "Major Surgical or Invasive Procedure": "Past Surgical History",
    "Physical exam": "Physical Exam",
    "Imaging": "Imaging and Studies",
    "Imaging / studies": "Imaging and Studies",
    "Imaging and studies": "Imaging and Studies",
    "Hospital Course": "Brief Hospital Course",
    "Assessment & Plan": "Assessment and Plan",
    "Medication": "Medications During Admission",
    "Medications": "Medications During Admission",
    "Discharge Medications": "Medications at Discharge",
    "medications during admission": "Medications During Admission",
    "medication during discharge": "Medications at Discharge",
    "Discharge instruction": "Discharge Instructions",
    "Follow-up instruction": "Discharge Instructions",
    "Follow-Up": "Follow Up",
    "Instructions": "Discharge Instructions"
  };
  
  export type ChunkerOptions = {
    headings?: string[];
    targetTokens?: number;     // default 700
    overlapTokens?: number;    // default 75
    keepVitalsLines?: boolean; // default true
    tokenizer?: (s: string) => number; // optional custom tokenizer
  };
  
  // Lightweight token estimator. If you add a real tokenizer later, pass it via options.tokenizer
  function estimateTokens(s: string): number {
    // Roughly 4 chars per token for English text
    return Math.max(1, Math.ceil(s.length / 4));
  }
  
  // Sentence splitter that respects periods, question marks, exclamation points, and newlines
  function splitSentences(text: string): string[] {
    const cleaned = text.replace(/\r/g, "");
    const parts = cleaned
      .split(/(?<=[.!?])\s+|\n{2,}/g)
      .map((s) => s.trim())
      .filter(Boolean);
    return parts;
  }
  
  const VITALS_LINE_RE = new RegExp(
    // patterns like: 98.1, 84, 142/65, 16, 98% RA
    String.raw`((Temp(?:erature)?\s*[:=]?\s*\d{2,3}(?:\.\d)?)|\b\d{2,3}(?:\.\d)?\b)[,\s]+` +
      String.raw`((HR|Heart\s*Rate)\s*[:=]?\s*\d{2,3}|\b\d{2,3}\b)[,\s]+` +
      String.raw`(\d{2,3}\/(?:\d{2,3}))[ ,]+` +
      String.raw`((RR|Resp(?:iratory)?\s*Rate)\s*[:=]?\s*\d{1,2}|\b\d{1,2}\b)[,\s]+` +
      String.raw`(\d{2,3}\s?%(?:\s*(?:RA|room\s*air))?)`,
    "i"
  );
  
  function detectHeading(section: string, headings: string[]): string | null {
    for (const h of headings) {
      const re = new RegExp(`^\n?\s*${escapeRegex(h)}\b[:\s]*`, "i");
      if (re.test(section)) return h;
    }
    return null;
  }
  
  function escapeRegex(s: string) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
  
  function splitOnHeadings(text: string, headings: string[]): string[] {
    if (!text) return [];
    const pat = new RegExp(
      `(^|\n\s*)(?:${headings.map(escapeRegex).join("|")})(?:\s*[:\n])`,
      "gi"
    );
    const sections: string[] = [];
    let last = 0;
    let m: RegExpExecArray | null;
    while ((m = pat.exec(text)) !== null) {
      const start = m.index;
      if (start > last) sections.push(text.slice(last, start));
      last = start;
    }
    sections.push(text.slice(last));
    return sections.map((s) => s.trim()).filter(Boolean);
  }
  
  export function chunkClinicalNote(
    rawText: string,
    opts: ChunkerOptions = {}
  ): Chunk[] {
    const headings = opts.headings ?? DEFAULT_HEADINGS;
    const target = Math.max(150, opts.targetTokens ?? 700);
    const overlapBudget = Math.max(0, opts.overlapTokens ?? 75);
    const keepVitals = opts.keepVitalsLines ?? true;
    const tok = opts.tokenizer ?? estimateTokens;
  
    const text = (rawText || "").replace(/\u0000/g, " ").trim();
    if (!text) return [];
  
    const sections = splitOnHeadings(text, headings);
    const pieces = sections.length ? sections : [text];
  
    const out: Chunk[] = [];
    let position = 0;
  
    for (const s of pieces) {
      const label = detectHeading(s, headings) || "General";
  const canon = SYNONYM_TO_CANON[label] || label;
      const body = label === "General" ? s : s.replace(new RegExp(`^\n?\s*${escapeRegex(label)}\b[:\s]*`, "i"), "").trim();
  
      // Optionally split out vitals line into its own tiny chunk
      const bodyLines = body.split(/\n+/);
      const vitalsLines: string[] = [];
      const remainderLines: string[] = [];
      for (const line of bodyLines) {
        if (keepVitals && VITALS_LINE_RE.test(line)) vitalsLines.push(line.trim());
        else remainderLines.push(line);
      }
  
      for (const vl of vitalsLines) {
        out.push({ section: "Vital signs", position: position++, content: vl, tokenCount: tok(vl) });
      }
  
      const remainder = remainderLines.join("\n").trim();
      if (!remainder) continue;
  
      const sentences = splitSentences(remainder);
      if (sentences.length === 0) continue;
  
      let cur: string[] = [];
      let curTokens = 0;
      const overlapBuf: string[] = [];
  
      const flush = () => {
        if (cur.length === 0) return;
        const content = cur.join(" ").trim();
        const t = tok(content);
        out.push({ section: canon, position: position++, content, tokenCount: t });
        // Prepare overlap buffer based on overlap token budget by trimming from front
        if (overlapBudget > 0) {
          overlapBuf.length = 0; // reset
          // accumulate sentences from the end until we meet overlapBudget
          let acc = 0;
          for (let i = cur.length - 1; i >= 0; i--) {
            const st = tok(cur[i]);
            if (acc + st > overlapBudget && acc > 0) break;
            overlapBuf.unshift(cur[i]);
            acc += st;
          }
        }
        cur = [];
        curTokens = 0;
      };
  
      for (let i = 0; i < sentences.length; i++) {
        const snt = sentences[i];
        const st = tok(snt);
        if (curTokens + st > target && cur.length) {
          flush();
          // start next with overlap buffer
          if (overlapBuf.length) {
            cur = overlapBuf.slice();
            curTokens = tok(cur.join(" "));
          }
        }
        cur.push(snt);
        curTokens += st;
      }
      flush();
  
      // Merge tiny tail chunks with previous if they are too small
      const MIN_TOK = Math.min(120, Math.floor(target * 0.25));
      if (out.length >= 2) {
        const last = out[out.length - 1];
        const prev = out[out.length - 2];
        if (last.section === canon && last.tokenCount < MIN_TOK) {
          prev.content = `${prev.content} ${last.content}`.trim();
          prev.tokenCount = tok(prev.content);
          out.pop();
          position--; // we merged, keep positions compact
        }
      }
    }
  
    // Reassign positions to be 0..N-1 in case of merges
    out.forEach((c, i) => (c.position = i));
    return out;
  }
  
  // Example direct run for quick testing
  if (require.main === module) {
    const sample = `\nHPI: 45-year-old with chest pain for 2 hours. Worse with exertion.\n\nVitals: 98.1, 84, 142/65, 16, 98% RA\n\nPhysical Exam: Well-appearing, speaking full sentences.\nHospital Course: Observed on telemetry. Serial troponins negative.`;
    const chunks = chunkClinicalNote(sample, {
      targetTokens: 700,
      overlapTokens: 75,
      keepVitalsLines: true,
    });
    console.log(chunks.map((c) => ({ section: c.section, pos: c.position, tokens: c.tokenCount, text: c.content.slice(0, 80) + (c.content.length > 80 ? "…" : "") })));
  }