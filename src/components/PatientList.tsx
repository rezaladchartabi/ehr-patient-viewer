import React from 'react';
import { Patient } from '../types';

interface PatientListProps {
  patients: Patient[];
  selectedPatient: Patient | null;
  onPatientSelect: (patient: Patient) => void;
  loading: boolean;
  isSearching: boolean;
  onClearSearch: () => void;
}

const PatientList: React.FC<PatientListProps> = ({
  patients,
  selectedPatient,
  onPatientSelect,
  loading,
  isSearching,
  onClearSearch
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading patients...</p>
        </div>
      </div>
    );
  }

  if (patients.length === 0) {
    if (isSearching) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No patients found</h3>
          <p className="text-gray-600 mb-4">No patients match your search criteria</p>
          <button
            onClick={onClearSearch}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Show All Patients
          </button>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No patients available</h3>
        <p className="text-gray-600">No patients are currently loaded in the system</p>
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {patients.map(patient => (
        <div
          key={patient.id}
          className={`p-4 cursor-pointer transition-all duration-200 ${
            selectedPatient?.id === patient.id 
              ? 'bg-blue-50 border-l-4 border-blue-500 shadow-sm' 
              : 'hover:bg-gray-50 border-l-4 border-transparent'
          }`}
          onClick={() => onPatientSelect(patient)}
        >
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="font-semibold text-gray-900 truncate">{patient.family_name}</div>
              <div className="text-sm text-gray-500 mt-1">
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 mr-2">
                  {patient.gender}
                </span>
                {patient.birth_date}
              </div>
            </div>
            {selectedPatient?.id === patient.id && (
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default PatientList;
