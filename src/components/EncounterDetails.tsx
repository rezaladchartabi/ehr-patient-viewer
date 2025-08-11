import React, { useState, useCallback } from 'react';
import { PatientTabs } from './PatientTabs';
import { Encounter, EncounterData } from '../hooks/usePatientData';

interface EncounterDetailsProps {
  encounter: Encounter;
  encounterData: EncounterData | undefined;
  isSelected: boolean;
  onSelect: (encounterId: string) => void;
  index: number;
}

export const EncounterDetails: React.FC<EncounterDetailsProps> = React.memo(({
  encounter,
  encounterData,
  isSelected,
  onSelect,
  index
}) => {
  const [activeTab, setActiveTab] = useState('conditions');

  const handleEncounterClick = useCallback(() => {
    onSelect(isSelected ? '' : encounter.id);
  }, [isSelected, encounter.id, onSelect]);

  const getServiceLineFromEncounter = (enc: Encounter): string => {
    if (!enc) return 'Default';
    const type = (enc.encounter_type || '').toLowerCase();
    if (type === 'icu') return 'ICU';
    if (type === 'emergency') return 'ED';
    return 'Default';
  };

  const renderConditions = () => (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {(encounterData?.conditions || []).map(cond => (
        <li key={cond.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
          <b>{cond.code_display}</b> (ICD: {cond.code}) • Category: {cond.category} • Status: {cond.status}
        </li>
      ))}
      {(encounterData?.conditions || []).length === 0 && <li>None</li>}
    </ul>
  );

  const renderMedicationRequests = () => (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {(encounterData?.medicationRequests || []).map(req => (
        <li key={req.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
          <b>{req.medication_display}</b> • Status: {req.status} • Priority: {req.priority}
        </li>
      ))}
      {(encounterData?.medicationRequests || []).length === 0 && <li>None</li>}
    </ul>
  );

  const renderMedicationAdministrations = () => (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {(encounterData?.medicationAdministrations || []).slice(0, 100).map(admin => (
        <li key={admin.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
          <b>{admin.medication_display}</b> • Status: {admin.status} • Dosage: {admin.dosage_quantity} {admin.dosage_unit}
        </li>
      ))}
      {(encounterData?.medicationAdministrations || []).length === 0 && <li>None</li>}
    </ul>
  );

  const renderObservations = () => (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {(encounterData?.observations || []).map(obs => (
        <li key={obs.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
          <b>{obs.code_display}</b> • Value: {obs.value_quantity || obs.value_string || obs.value_display || obs.value_code || 'N/A'} {obs.value_unit}
        </li>
      ))}
      {(encounterData?.observations || []).length === 0 && <li>None</li>}
    </ul>
  );

  const renderProcedures = () => (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {(encounterData?.procedures || []).map(proc => (
        <li key={proc.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
          <b>{proc.procedure_display}</b> • Status: {proc.status}
        </li>
      ))}
      {(encounterData?.procedures || []).length === 0 && <li>None</li>}
    </ul>
  );

  const renderSpecimens = () => (
    <ul style={{ listStyle: 'none', padding: 0 }}>
      {(encounterData?.specimens || []).map(spec => (
        <li key={spec.id} style={{ padding: '10px', border: '1px solid #ddd', marginBottom: '5px', borderRadius: '4px' }}>
          <b>{spec.specimen_type_display}</b> • Status: {spec.status}
        </li>
      ))}
      {(encounterData?.specimens || []).length === 0 && <li>None</li>}
    </ul>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'conditions':
        return renderConditions();
      case 'medication-requests':
        return renderMedicationRequests();
      case 'medication-administrations':
        return renderMedicationAdministrations();
      case 'observations':
        return renderObservations();
      case 'procedures':
        return renderProcedures();
      case 'specimens':
        return renderSpecimens();
      default:
        return null;
    }
  };

  return (
    <li
      className={`p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-800 border-l-4 ${
        isSelected ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-500' : 'border-transparent'
      }`}
      onClick={handleEncounterClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 dark:bg-neutral-800 text-xs font-medium text-gray-700 dark:text-neutral-300">
            {index + 1}
          </span>
          <div>
            <div className="font-medium">{encounter.class_display || encounter.encounter_type || 'Encounter'}</div>
            <div className="text-xs text-gray-500">
              {encounter.start_date} {encounter.end_date ? `- ${encounter.end_date}` : ''} • {encounter.status} • {encounter.service_type || getServiceLineFromEncounter(encounter)}
            </div>
          </div>
        </div>
        <div className="text-xs text-gray-500">{encounter.priority_display}</div>
      </div>
      
      {isSelected && (
        <div className="mt-3 border-t border-gray-200 dark:border-neutral-800 pt-3">
          <div onClick={(e) => e.stopPropagation()}>
            <PatientTabs
              tabs={[
                { id: 'conditions', label: 'Conditions' },
                { id: 'medication-administrations', label: 'Med Admin' },
                { id: 'medication-requests', label: 'Med Requests' },
                { id: 'observations', label: 'Observations' },
                { id: 'procedures', label: 'Procedures' },
                { id: 'specimens', label: 'Specimens' },
              ]}
              active={activeTab}
              onChange={setActiveTab}
            />
          </div>
          <div className="mt-3">
            {renderTabContent()}
            {encounterData?.note && (
              <div className="text-xs text-gray-500 mt-2">{encounterData.note}</div>
            )}
          </div>
        </div>
      )}
    </li>
  );
});

EncounterDetails.displayName = 'EncounterDetails';
