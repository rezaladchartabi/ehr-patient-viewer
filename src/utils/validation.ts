// Comprehensive validation utilities to prevent data issues

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// ========== PATIENT VALIDATION ==========

export const validatePatient = (patient: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!patient) {
    errors.push('Patient object is null or undefined');
    return { isValid: false, errors, warnings };
  }

  if (typeof patient !== 'object') {
    errors.push('Patient is not an object');
    return { isValid: false, errors, warnings };
  }

  // Required fields
  if (!patient.id) {
    errors.push('Patient missing required field: id');
  }

  if (!patient.family_name) {
    errors.push('Patient missing required field: family_name');
  }

  if (!patient.gender) {
    errors.push('Patient missing required field: gender');
  }

  if (!patient.birth_date) {
    errors.push('Patient missing required field: birth_date');
  }

  // Optional field validation
  if (patient.identifier && typeof patient.identifier !== 'string') {
    warnings.push('Patient identifier should be a string');
  }

  if (patient.race && typeof patient.race !== 'string') {
    warnings.push('Patient race should be a string');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// ========== ALLERGY VALIDATION ==========

export const validateAllergy = (allergy: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!allergy) {
    errors.push('Allergy object is null or undefined');
    return { isValid: false, errors, warnings };
  }

  if (typeof allergy !== 'object') {
    errors.push('Allergy is not an object');
    return { isValid: false, errors, warnings };
  }

  // Required fields
  if (!allergy.allergy_name) {
    errors.push('Allergy missing required field: allergy_name');
  } else if (typeof allergy.allergy_name !== 'string') {
    errors.push('Allergy allergy_name should be a string');
  }

  // Optional field validation
  if (allergy.id && typeof allergy.id !== 'string') {
    warnings.push('Allergy id should be a string');
  }

  if (allergy.category && typeof allergy.category !== 'string') {
    warnings.push('Allergy category should be a string');
  }

  if (allergy.clinical_status && typeof allergy.clinical_status !== 'string') {
    warnings.push('Allergy clinical_status should be a string');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// ========== NOTE VALIDATION ==========

export const validateNote = (note: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!note) {
    errors.push('Note object is null or undefined');
    return { isValid: false, errors, warnings };
  }

  if (typeof note !== 'object') {
    errors.push('Note is not an object');
    return { isValid: false, errors, warnings };
  }

  // Required fields
  if (!note.patient_id) {
    errors.push('Note missing required field: patient_id');
  }

  if (!note.note_id && !note.id) {
    errors.push('Note missing required field: note_id or id');
  }

  // Optional field validation
  if (note.text && typeof note.text !== 'string') {
    warnings.push('Note text should be a string');
  }

  if (note.content && typeof note.content !== 'string') {
    warnings.push('Note content should be a string');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// ========== API RESPONSE VALIDATION ==========

export const validateApiResponse = (response: any, expectedType: string): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!response) {
    errors.push(`API response for ${expectedType} is null or undefined`);
    return { isValid: false, errors, warnings };
  }

  if (typeof response !== 'object') {
    errors.push(`API response for ${expectedType} is not an object`);
    return { isValid: false, errors, warnings };
  }

  // Check for common API response patterns
  if (expectedType === 'allergies' && !response.allergies) {
    errors.push('API response missing allergies field');
  }

  if (expectedType === 'notes' && !response.notes) {
    errors.push('API response missing notes field');
  }

  if (expectedType === 'patients' && !response.patients) {
    errors.push('API response missing patients field');
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// ========== ARRAY VALIDATION ==========

export const validateArray = (array: any, itemValidator: (item: any) => ValidationResult, itemType: string): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!Array.isArray(array)) {
    errors.push(`${itemType} is not an array`);
    return { isValid: false, errors, warnings };
  }

  // Validate each item in the array
  array.forEach((item, index) => {
    const itemValidation = itemValidator(item);
    if (!itemValidation.isValid) {
      errors.push(`${itemType}[${index}] validation failed: ${itemValidation.errors.join(', ')}`);
    }
    warnings.push(...itemValidation.warnings.map(w => `${itemType}[${index}]: ${w}`));
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};

// ========== COMPREHENSIVE VALIDATION ==========

export const validateDataIntegrity = (data: any): ValidationResult => {
  const errors: string[] = [];
  const warnings: string[] = [];

  console.debug('[VALIDATION] Starting data integrity check:', {
    type: typeof data,
    isArray: Array.isArray(data),
    keys: data ? Object.keys(data) : 'null'
  });

  // Validate based on data type
  if (Array.isArray(data)) {
    if (data.length === 0) {
      warnings.push('Data array is empty');
    } else {
      // Try to determine the type of items in the array
      const firstItem = data[0];
      if (firstItem?.allergy_name) {
        const validation = validateArray(data, validateAllergy, 'allergies');
        errors.push(...validation.errors);
        warnings.push(...validation.warnings);
      } else if (firstItem?.family_name) {
        const validation = validateArray(data, validatePatient, 'patients');
        errors.push(...validation.errors);
        warnings.push(...validation.warnings);
      } else if (firstItem?.patient_id) {
        const validation = validateArray(data, validateNote, 'notes');
        errors.push(...validation.errors);
        warnings.push(...validation.warnings);
      } else {
        warnings.push('Unable to determine array item type for validation');
      }
    }
  } else if (typeof data === 'object' && data !== null) {
    // Validate object structure
    if (data.allergies) {
      const validation = validateArray(data.allergies, validateAllergy, 'allergies');
      errors.push(...validation.errors);
      warnings.push(...validation.warnings);
    }

    if (data.patients) {
      const validation = validateArray(data.patients, validatePatient, 'patients');
      errors.push(...validation.errors);
      warnings.push(...validation.warnings);
    }

    if (data.notes) {
      const validation = validateArray(data.notes, validateNote, 'notes');
      errors.push(...validation.errors);
      warnings.push(...validation.warnings);
    }
  } else {
    errors.push('Data is not an array or object');
  }

  console.debug('[VALIDATION] Data integrity check completed:', {
    isValid: errors.length === 0,
    errorCount: errors.length,
    warningCount: warnings.length
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
};
