import React from 'react';
import { Note, Patient } from '../types';

interface NotesDisplayProps {
  notes: Note[];
  notesLoading: boolean;
  selectedNote: Note | null;
  onNoteSelect: (note: Note | null) => void;
  selectedPatient: Patient | null;
}

const NotesDisplay: React.FC<NotesDisplayProps> = ({
  notes,
  notesLoading,
  selectedNote,
  onNoteSelect,
  selectedPatient
}) => {
  return (
    <>
      {/* Notes Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">📝</span>
            <h2 className="text-xl font-semibold text-gray-900">Clinical Notes</h2>
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {notes.length} notes
            </span>
          </div>
        </div>
      </div>

      {/* Notes Content */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-900">Clinical Notes</h3>
            <p className="text-gray-600">{notes.length} notes found</p>
          </div>
          {notesLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading clinical notes...</p>
              </div>
            </div>
          ) : notes.length > 0 ? (
            <div className="space-y-4">
              {notes.map((note, index) => (
                <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden cursor-pointer hover:shadow-md transition-all duration-200 hover:border-blue-300 group" 
                     onClick={() => onNoteSelect(note)}>
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h4 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                          {note.note_id || `Note ${index + 1}`}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">
                          Click to view full details
                        </p>
                      </div>
                      <div className="flex flex-col items-end space-y-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {note.note_type || 'General'}
                        </span>
                        <span className="text-xs text-gray-400">
                          {((note.text || note.content || '').length).toLocaleString()} chars
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-3">
                      <div>
                        <span className="text-sm font-medium text-gray-500">Charted</span>
                        <p className="text-sm text-gray-900">{note.charttime_formatted || (note.timestamp ? new Date(note.timestamp).toLocaleString() : 'Unknown')}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-500">Stored</span>
                        <p className="text-sm text-gray-900">{note.storetime_formatted || (note.store_time ? new Date(note.store_time).toLocaleString() : 'Unknown')}</p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-500">Patient ID</span>
                        <p className="text-sm text-gray-900 font-mono">{note.patient_id || 'N/A'}</p>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 group-hover:bg-blue-50 transition-colors">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-500">Content Preview</span>
                        <span className="text-xs text-gray-400">Click to expand</span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-3">
                        {(note.text || note.content || '').substring(0, 300)}
                        {(note.text || note.content || '').length > 300 && '...'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <svg className="mx-auto h-16 w-16 text-gray-300 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Clinical Notes</h3>
                <p className="text-gray-600">No clinical notes available for this patient</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Note Detail Modal */}
      {selectedNote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedNote.note_id || 'Clinical Note'}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Patient: {selectedPatient?.family_name} (ID: {selectedPatient?.id})
                </p>
              </div>
              <button 
                onClick={() => onNoteSelect(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl font-bold p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Note Metadata Section */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Note Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Note ID</span>
                  <span className="text-sm text-gray-900 font-mono">{selectedNote.note_id || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Note Type</span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {selectedNote.note_type || 'General'}
                  </span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Charted Date</span>
                  <span className="text-sm text-gray-900">
                    {selectedNote.charttime_formatted || 
                     (selectedNote.timestamp ? new Date(selectedNote.timestamp).toLocaleString() : 'Unknown')}
                  </span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Stored Date</span>
                  <span className="text-sm text-gray-900">
                    {selectedNote.storetime_formatted || 
                     (selectedNote.store_time ? new Date(selectedNote.store_time).toLocaleString() : 'Unknown')}
                  </span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Created At</span>
                  <span className="text-sm text-gray-900">
                    {selectedNote.created_at ? new Date(selectedNote.created_at).toLocaleString() : 'Unknown'}
                  </span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Content Length</span>
                  <span className="text-sm text-gray-900">
                    {((selectedNote.text || selectedNote.content || '').length).toLocaleString()} characters
                  </span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Patient ID</span>
                  <span className="text-sm text-gray-900 font-mono">{selectedNote.patient_id || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500 block">Database ID</span>
                  <span className="text-sm text-gray-900 font-mono">{selectedNote.id || 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Note Content Section */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Note Content</h3>
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800 font-mono bg-gray-50 p-4 rounded border">
                  {selectedNote.text || selectedNote.content || 'No content available'}
                </div>
              </div>
            </div>

            {/* Extracted Information Section (if available) */}
            {(selectedNote.allergies || selectedNote.conditions || selectedNote.medications) && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Extracted Information</h3>
                
                {selectedNote.allergies && selectedNote.allergies.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-md font-medium text-gray-800 mb-2">Allergies Found</h4>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      {selectedNote.allergies.map((allergy: any, index: number) => (
                        <div key={index} className="text-sm text-red-800">
                          • {allergy.allergy_name || allergy.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedNote.conditions && selectedNote.conditions.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-md font-medium text-gray-800 mb-2">Conditions Found</h4>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      {selectedNote.conditions.map((condition: any, index: number) => (
                        <div key={index} className="text-sm text-blue-800">
                          • {condition.condition_name || condition.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedNote.medications && selectedNote.medications.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-md font-medium text-gray-800 mb-2">Medications Found</h4>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      {selectedNote.medications.map((medication: any, index: number) => (
                        <div key={index} className="text-sm text-green-800">
                          • {medication.medication_name || medication.name}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                onClick={() => {
                  const text = selectedNote.text || selectedNote.content || '';
                  navigator.clipboard.writeText(text);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Copy Content
              </button>
              <button
                onClick={() => onNoteSelect(null)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default NotesDisplay;
