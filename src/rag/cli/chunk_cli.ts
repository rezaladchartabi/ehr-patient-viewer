#!/usr/bin/env node
/*
  CLI: Chunk discharge notes and emit JSONL for RAG ingestion

  Usage:
    npm run chunk:notes -- --in backend/discharge_notes.xlsx --out rag_chunks.jsonl

  Output JSONL per line:
    {
      id, text,
      metadata: {
        patient_identifier, note_id, chart_time, section, position, tokenCount,
        vitals?, note_metadata: { ...all original XLSX columns... }
      }
    }
*/

import fs from "fs";
import path from "path";
import * as XLSX from "xlsx";
import { chunkClinicalNote } from "../chunker";
import { extractVitalsFromChunks } from "../vitals";

type Row = Record<string, any>;

function parseArgs(argv: string[]) {
  const args: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--in" || a === "-i") args.in = argv[++i];
    else if (a === "--out" || a === "-o") args.out = argv[++i];
    else if (a === "--sheet") args.sheet = argv[++i];
    else if (a === "--help" || a === "-h") args.help = true;
  }
  return args;
}

function usage() {
  console.log(
    "Usage: chunk_cli --in backend/discharge_notes.xlsx --out rag_chunks.jsonl [--sheet Sheet1]"
  );
}

function readXlsxRows(filePath: string, sheetName?: string): Row[] {
  const wb = XLSX.readFile(filePath, { cellDates: false });
  const name = sheetName || wb.SheetNames[0];
  const sheet = wb.Sheets[name];
  if (!sheet) throw new Error(`Sheet not found: ${name}`);
  const rows: Row[] = XLSX.utils.sheet_to_json(sheet, { defval: "" });
  return rows;
}

function normalizeSubjectId(v: any): string {
  if (v === null || v === undefined) return "";
  return String(v);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return usage();

  const inPath = String(args.in || "backend/discharge_notes.xlsx");
  const outPath = String(args.out || "rag_chunks.jsonl");
  const sheet = (args.sheet as string) || undefined;

  if (!fs.existsSync(inPath)) {
    console.error(`Input not found: ${inPath}`);
    process.exit(1);
  }

  const rows = readXlsxRows(inPath, sheet);
  const out = fs.createWriteStream(outPath, { encoding: "utf8" });

  let totalChunks = 0;
  let totalNotes = 0;

  for (const row of rows) {
    const noteId = String(row.note_id ?? row.noteId ?? "");
    const subjectId = normalizeSubjectId(row.subject_id ?? row.subjectId);
    const chartTime = String(row.charttime ?? row.chart_time ?? "");
    const text = String(row.text ?? "");

    if (!text) continue;
    totalNotes++;

    const chunks = chunkClinicalNote(text, {
      targetTokens: 700,
      overlapTokens: 150,
      keepVitalsLines: true,
    });

    // Optional vitals extraction for auditing
    const vitalsRows = extractVitalsFromChunks(
      chunks.map((c) => ({ section: c.section, content: c.content }))
    );
    const vitalsByIndex = new Map<number, any>();
    for (const vr of vitalsRows) vitalsByIndex.set(vr.chunkIndex, vr);

    for (const c of chunks) {
      const id = `${noteId}:${c.position}`;
      const payload = {
        id,
        text: c.content,
        metadata: {
          patient_identifier: subjectId,
          note_id: noteId,
          chart_time: chartTime,
          section: c.section,
          position: c.position,
          tokenCount: c.tokenCount,
          vitals: vitalsByIndex.get(c.position) || undefined,
          note_metadata: row,
        },
      };
      out.write(JSON.stringify(payload) + "\n");
      totalChunks++;
    }
  }

  out.end();
  out.on("finish", () => {
    console.log(
      `Wrote ${totalChunks} chunks from ${totalNotes} notes to ${path.resolve(outPath)}`
    );
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


