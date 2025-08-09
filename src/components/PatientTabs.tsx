import React from 'react';
import { cn } from '../lib/utils';

export interface TabDef {
  id: string;
  label: string;
}

interface PatientTabsProps {
  tabs: TabDef[];
  active: string;
  onChange: (id: string) => void;
}

export function PatientTabs({ tabs, active, onChange }: PatientTabsProps) {
  return (
    <div className="border-b border-gray-200 dark:border-neutral-800">
      <div className="flex gap-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            className={cn(
              'px-4 py-2 rounded-t-lg text-sm font-medium',
              active === t.id
                ? 'bg-white dark:bg-neutral-900 text-blue-600 border-x border-t border-gray-200 dark:border-neutral-800'
                : 'text-gray-600 dark:text-neutral-400 hover:text-gray-900 dark:hover:text-neutral-100'
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  );
}


