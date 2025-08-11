import React, { useState } from 'react';

type Props = {
  apiBase: string;
  onPickPatient: (p: any) => void;
};

export default function SearchBar({ apiBase, onPickPatient }: Props) {
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<Array<any>>([]);

  const runSearch = () => {
    if (!q.trim()) {
      setItems([]);
      setOpen(true);
      return;
    }
    setLoading(true);
    setOpen(true);
    fetch(`${apiBase}/search?q=${encodeURIComponent(q.trim())}&limit=50`)
      .then((r) => r.json())
      .then((data) => setItems(Array.isArray(data.items) ? data.items : []))
      .finally(() => setLoading(false));
  };

  const fetchPatientAndPick = async (patientId: string) => {
    const bundle = await fetch(`${apiBase}/Patient?_id=${encodeURIComponent(patientId)}&_count=1`).then((r) => r.json());
    const p = bundle.entry && bundle.entry[0] ? bundle.entry[0].resource : null;
    if (!p) return;
    const patient = {
      id: p.id,
      family_name: p.name?.[0]?.family || 'Unknown',
      gender: p.gender || 'Unknown',
      birth_date: p.birthDate || 'Unknown',
      race: undefined,
      ethnicity: undefined,
      birth_sex: undefined,
      identifier: p.identifier?.[0]?.value,
      marital_status: p.maritalStatus?.text,
      deceased_date: p.deceasedDateTime,
      managing_organization: p.managingOrganization?.reference,
    };
    onPickPatient(patient);
    setOpen(false);
  };

  return (
    <div className="relative z-50 ml-auto w-full max-w-[25vw]" style={{ marginTop: '10px' }}>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Search patients or meds..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') runSearch();
          }}
          className="w-full rounded-lg border border-gray-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 px-3 py-2 shadow-soft focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button onClick={runSearch} className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
          Search
        </button>
      </div>
      {open && (
        <>
          <div className="fixed inset-0 bg-black/30 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 right-0 mt-2 z-50 rounded-xl border border-gray-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 shadow-soft max-h-[60vh] overflow-y-auto">
            <div className="border-b border-gray-200 dark:border-neutral-800 px-4 py-2 text-sm text-gray-500">
              {loading ? 'Searching...' : 'Search Results'}
            </div>
            {!loading && (
              <div className="p-2">
                {items.length === 0 && <div className="px-3 py-4 text-sm text-gray-500">No results</div>}
                {items.length > 0 && (
                  <ul className="divide-y divide-gray-100 dark:divide-neutral-800">
                    {items.map((it) => (
                      <li
                        key={`${it.type}-${it.rid}`}
                        className="cursor-pointer px-3 py-2 hover:bg-gray-50 dark:hover:bg-neutral-800 rounded-md"
                        onClick={() => fetchPatientAndPick(it.patient_id || it.rid)}
                      >
                        <div className="font-medium">{it.title || it.type}</div>
                        <div className="text-xs text-gray-500">{it.type} • {it.subtitle}</div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}


