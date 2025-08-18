/**
 * vitals.ts — extraction helpers for ED-style vitals
 *
 * Exports
 * - Vitals: normalized type
 * - parseVitals(text): Vitals | null — parse a single string
 * - extractVitalsFromChunks(chunks): ExtractedVitalsRow[] — scan chunked note text
 */

export type Vitals = {
    tempF?: number;
    heartRateBpm?: number;
    bpSys?: number;
    bpDia?: number;
    rrBpm?: number;
    spo2Percent?: number;
    oxygenDevice?: string;
    onRoomAir?: boolean;
    takenTime?: string; // optional, caller can set if available
  };
  
  export type ExtractedVitalsRow = Vitals & {
    chunkIndex: number;
    section: string;
    sourceText: string;
  };
  
  // Detect standard ED vitals line like: 98.1, 84, 142/65, 16, 98% RA
  const VITALS_LINE_RE = new RegExp(
    String.raw`((Temp(?:erature)?\s*[:=]?\s*\d{2,3}(?:\.\d)?)|\b\d{2,3}(?:\.\d)?\b)[,\s]+` +
      String.raw`((HR|Heart\s*Rate)\s*[:=]?\s*\d{2,3}|\b\d{2,3}\b)[,\s]+` +
      String.raw`(\d{2,3}\/(?:\d{2,3}))[ ,]+` +
      String.raw`((RR|Resp(?:iratory)?\s*Rate)\s*[:=]?\s*\d{1,2}|\b\d{1,2}\b)[,\s]+` +
      String.raw`(\d{2,3}\s?%(?:\s*(?:RA|room\s*air))?)`,
    "i"
  );
  
  function toNumber(s?: string): number | undefined {
    if (!s) return undefined;
    const n = Number(String(s).replace(/[^0-9.\-]/g, ""));
    return Number.isFinite(n) ? n : undefined;
  }
  
  function cToF(c: number): number {
    return Math.round((c * 9) / 5 + 32);
  }
  
  export function parseVitals(text: string): Vitals | null {
    if (!text || !text.trim()) return null;
    const s = text.trim();
    const out: Vitals = {};
  
    // Temperature labeled or with unit
    const mTempLbl = s.match(/\b(?:Temp(?:erature)?|T)\s*[:=]?\s*([0-9]{2,3}(?:\.[0-9])?)\s*([FC])?/i);
    if (mTempLbl) {
      const val = toNumber(mTempLbl[1]);
      const unit = mTempLbl[2]?.toUpperCase();
      if (val !== undefined) out.tempF = unit === "C" ? cToF(val) : val;
    } else {
      const mTempUnit = s.match(/\b([3-4][0-9](?:\.[0-9])?)\s*C\b/i);
      if (mTempUnit) out.tempF = cToF(Number(mTempUnit[1]));
      const mTempF = s.match(/\b(9[0-9](?:\.[0-9])?|1[01][0-9](?:\.[0-9])?)\b(?!\s*%)/);
      if (!out.tempF && mTempF) {
        const val = Number(mTempF[1]);
        if (val >= 94 && val <= 107) out.tempF = val;
      }
    }
  
    // Heart rate
    const mHR = s.match(/\b(?:HR|Heart\s*Rate|Pulse)\s*[:=]?\s*([0-9]{2,3})\b/i);
    if (mHR) out.heartRateBpm = toNumber(mHR[1]);
  
    // Respiratory rate
    const mRR = s.match(/\b(?:RR|Resp(?:iratory)?\s*Rate)\s*[:=]?\s*([0-9]{1,2})\b/i);
    if (mRR) out.rrBpm = toNumber(mRR[1]);
  
    // Blood pressure
    const mBP = s.match(/\b(\d{2,3})\/(\d{2,3})\b/);
    if (mBP) {
      out.bpSys = toNumber(mBP[1]);
      out.bpDia = toNumber(mBP[2]);
    }
  
    // Oxygen saturation and device
    const mSpO2 = s.match(/\b(\d{2,3})\s?%\b/i);
    if (mSpO2) out.spo2Percent = toNumber(mSpO2[1]);
    const mDevice = s.match(/\b(RA|room\s*air|NC|nasal\s*cannula|NRB|non\s*rebreather|HFNC|high\s*flow|Venturi|BiPAP|CPAP)\b/i);
    if (mDevice) {
      const dev = mDevice[1].toLowerCase();
      out.onRoomAir = dev === "ra" || dev.includes("room air");
      out.oxygenDevice = out.onRoomAir ? "Room air" : mDevice[1];
    }
  
    // Heuristic for unlabeled five term vitals lines: T, HR, BP, RR, SpO2 [Device]
    if (!mHR && !mRR && !mBP && !mSpO2 && VITALS_LINE_RE.test(s)) {
      const csv = s.split(/\s*,\s*/);
      if (csv.length >= 4) {
        const t = toNumber(csv[0]);
        const hr = toNumber(csv[1]);
        const bp = csv.find((p) => /\d{2,3}\/\d{2,3}/.test(p));
        const rr = toNumber(csv[3]);
        const spo = (csv[4] || "").match(/(\d{2,3})\s?%/);
        if (t && t > 80 && t < 110 && !out.tempF) out.tempF = t;
        if (hr && hr >= 30 && hr <= 220 && !out.heartRateBpm) out.heartRateBpm = hr;
        if (bp && (!out.bpSys || !out.bpDia)) {
          const mm = bp.match(/(\d{2,3})\/(\d{2,3})/);
          if (mm) { out.bpSys = toNumber(mm[1]); out.bpDia = toNumber(mm[2]); }
        }
        if (rr && rr >= 6 && rr <= 50 && !out.rrBpm) out.rrBpm = rr;
        if (spo && !out.spo2Percent) out.spo2Percent = toNumber(spo[1]);
        if (/\bRA\b|room\s*air/i.test(s) && out.onRoomAir === undefined) { out.onRoomAir = true; out.oxygenDevice = "Room air"; }
      }
    }
  
    const hasAny = Object.values(out).some((v) => v !== undefined);
    return hasAny ? out : null;
  }
  
  export function extractVitalsFromChunks(chunks: { section: string; content: string }[]): ExtractedVitalsRow[] {
    const rows: ExtractedVitalsRow[] = [];
    for (let i = 0; i < chunks.length; i++) {
      const c = chunks[i];
      if (c.section === "Vital signs" || /\bvital\b/i.test(c.section)) {
        const v = parseVitals(c.content);
        if (v) rows.push({ ...v, chunkIndex: i, section: c.section, sourceText: c.content });
      }
    }
    return rows;
  }
  
  /*
  Usage
  -----
  import { chunkClinicalNote } from "./chunker";
  import { parseVitals, extractVitalsFromChunks } from "./vitals";
  
  const chunks = chunkClinicalNote(noteText);
  const vitalsRows = extractVitalsFromChunks(chunks);
  */
