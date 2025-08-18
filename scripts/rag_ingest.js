#!/usr/bin/env node
/*
  RAG Ingestion Script

  Usage examples:
    node scripts/rag_ingest.js --jsonl rag_chunks.jsonl --url http://127.0.0.1:8005 --collection patient --batch 200

  Environment variables (fallbacks):
    RAG_BACKEND_URL (default: http://127.0.0.1:8005)
    RAG_COLLECTION   (default: patient)
    RAG_BATCH        (default: 200)
*/

const fs = require('fs');
const readline = require('readline');

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--jsonl' || a === '-j') args.jsonl = argv[++i];
    else if (a === '--url' || a === '-u') args.url = argv[++i];
    else if (a === '--collection' || a === '-c') args.collection = argv[++i];
    else if (a === '--batch' || a === '-b') args.batch = Number(argv[++i]);
    else if (a === '--help' || a === '-h') args.help = true;
  }
  return args;
}

function usage() {
  console.log(
    'Usage: node scripts/rag_ingest.js --jsonl rag_chunks.jsonl [--url http://127.0.0.1:8005] [--collection patient] [--batch 200]'
  );
}

async function postBatch(indexUrl, documents, collection) {
  const res = await fetch(indexUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ documents, collection })
  });
  const text = await res.text();
  return { status: res.status, body: text };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return usage();

  const jsonlPath = args.jsonl || 'rag_chunks.jsonl';
  const baseUrl = args.url || process.env.RAG_BACKEND_URL || 'http://127.0.0.1:8005';
  const collection = args.collection || process.env.RAG_COLLECTION || 'patient';
  const batchSize = args.batch || Number(process.env.RAG_BATCH) || 200;

  const indexUrl = `${baseUrl.replace(/\/$/, '')}/rag/index`;

  if (!fs.existsSync(jsonlPath)) {
    console.error(`Input JSONL not found: ${jsonlPath}`);
    process.exit(1);
  }

  const rl = readline.createInterface({
    input: fs.createReadStream(jsonlPath, { encoding: 'utf8' }),
    crlfDelay: Infinity
  });

  let buffer = [];
  let total = 0;
  const t0 = Date.now();

  async function flush() {
    if (buffer.length === 0) return;
    try {
      const res = await postBatch(indexUrl, buffer, collection);
      console.log(`indexed ${buffer.length} -> ${res.status} ${res.body.slice(0, 200)}`);
      total += buffer.length;
      buffer = [];
    } catch (err) {
      console.error('Batch index failed:', err);
      process.exit(2);
    }
  }

  for await (const line of rl) {
    const s = line.trim();
    if (!s) continue;
    try {
      const o = JSON.parse(s);
      buffer.push({ id: o.id, text: o.text, metadata: o.metadata || {} });
      if (buffer.length >= batchSize) {
        await flush();
      }
    } catch (err) {
      console.warn('Skipping malformed line:', err);
    }
  }

  await flush();
  const dt = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`TOTAL indexed: ${total} in ${dt}s`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});


