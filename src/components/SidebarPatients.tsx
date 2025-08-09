import React from 'react';
import { Card } from './ui/card';
import { cn } from '../lib/utils';

interface SidebarPatientsProps<PatientT> {
  patients: PatientT[];
  selectedId?: string;
  onSelect: (patient: PatientT) => void;
  renderItem: (patient: PatientT) => React.ReactNode;
}

export function SidebarPatients<PatientT extends { id: string }>({
  patients,
  selectedId,
  onSelect,
  renderItem,
}: SidebarPatientsProps<PatientT>) {
  return (
    <aside className="w-[320px] shrink-0">
      <Card className="p-2">
        <div className="px-2 py-3 text-sm font-medium tracking-wide text-gray-500">Patients</div>
        <ul className="space-y-2">
          {patients.map((p) => (
            <li key={p.id}>
              <button
                onClick={() => onSelect(p)}
                className={cn(
                  'w-full text-left px-3 py-2 rounded-lg border bg-white/60 dark:bg-neutral-800/60 hover:bg-white dark:hover:bg-neutral-800 transition',
                  selectedId === p.id ? 'border-blue-500 ring-2 ring-blue-200 dark:ring-blue-600' : 'border-gray-200 dark:border-neutral-700'
                )}
              >
                {renderItem(p)}
              </button>
            </li>
          ))}
        </ul>
      </Card>
    </aside>
  );
}


