import React from 'react';
import { Patient, Allergy } from '../types';

interface PatientDetailsProps {
  patient: Patient;
  allergies: Allergy[];
  allergiesLoading: boolean;
}

const PatientDetails: React.FC<PatientDetailsProps> = ({
  patient,
  allergies,
  allergiesLoading
}) => {
  return (
    <div className="bg-white shadow-sm border-b border-gray-200">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">{patient.family_name}</h1>
            <p className="text-gray-600">Patient ID: {patient.identifier}</p>
          </div>
        </div>
        
        {/* Patient Demographics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm font-medium text-gray-500">Gender</div>
            <div className="text-lg font-semibold text-gray-900">{patient.gender}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm font-medium text-gray-500">Birth Date</div>
            <div className="text-lg font-semibold text-gray-900">{patient.birth_date}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm font-medium text-gray-500">Race</div>
            <div className="text-lg font-semibold text-gray-900">{patient.race || 'N/A'}</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-sm font-medium text-gray-500">Marital Status</div>
            <div className="text-lg font-semibold text-gray-900">{patient.marital_status || 'N/A'}</div>
          </div>
        </div>
        
        {/* Allergies Section */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Allergies</h3>
          {allergiesLoading ? (
            <div className="text-gray-500">Loading allergies...</div>
          ) : allergies.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {allergies.map((allergy, index) => (
                <span 
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800"
                >
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {allergy.allergy_name}
                </span>
              ))}
            </div>
          ) : (
            <div className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              No known allergies
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientDetails;
