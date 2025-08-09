import React from 'react';
import { Card } from './ui/card';
import { Sun, Moon } from 'lucide-react';

interface PatientHeaderBannerProps {
  title: string;
  subtitle?: string;
  onToggleTheme: () => void;
  isDark: boolean;
}

export function PatientHeaderBanner({ title, subtitle, onToggleTheme, isDark }: PatientHeaderBannerProps) {
  return (
    <Card className="flex items-center justify-between p-4">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
        {subtitle && <p className="text-sm text-gray-500 dark:text-neutral-400 mt-1">{subtitle}</p>}
      </div>
      <button
        onClick={onToggleTheme}
        className="inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm hover:bg-white dark:hover:bg-neutral-800 transition"
      >
        {isDark ? <Sun size={16} /> : <Moon size={16} />} {isDark ? 'Light mode' : 'Dark mode'}
      </button>
    </Card>
  );
}


