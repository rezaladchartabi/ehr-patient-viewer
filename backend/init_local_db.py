#!/usr/bin/env python3
"""
Script to initialize the local database with allowlist patients
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

from local_db import LocalDatabase
from sync_service import SyncService

# Allowlist patient IDs
ALLOWLIST_IDS = [
    '03632093-8e46-5c64-8d8b-76ce07fa7b35',
    '063ef64a-f642-563f-b9f0-206e1d32b930',
    '08744ed5-b376-5a84-8cca-6b4f61ea633e',
    '10306acb-5f9d-596d-828c-ad1432efb89b',
    '146c9f68-5b1c-5713-a5ea-6a31f0d21543',
    '271cd75b-b278-51fe-a6cf-6efe41c3da2b',
    '2ae93a82-fd85-5a0b-88ac-683b152c7025',
    '2d4ea3ef-5bec-5529-92ce-a9926343b794',
    '408d1f02-a864-599e-ac5c-b358440a801c',
    '4b1cc63a-cbb0-5b64-ac10-f98bc3385292',
    '51b9ffda-5b82-5e91-a8bc-1b8d1e03451b',
    '540ab130-1abc-578d-8f6e-63c1f82bb305',
    '558e0386-a3d3-5bfb-ad28-939133fcc773',
    '5601a622-8a8f-5951-b5e3-17179238462e',
    '56c044dd-8545-57d3-a473-5a285c7311d7',
    '58639ace-d5e3-540d-8d0b-d479e60e2147',
    '5c52d57d-d13a-5f0d-a71d-b489f9b521b3',
    '5f3da891-ffc9-5381-9b37-c139fc99da00',
    '6027f3be-106c-5d2f-a260-6534b5c5c5b2',
    '62a85fdd-29d8-5d34-a217-bd770876cb24',
    '64437fe8-8298-515e-9195-04301b2402c8',
    '68048f1c-c0c9-550e-8bb1-78dc375f2e84',
    '7070642d-2d89-53f3-9803-d0edb424596c',
    '817e8a08-7dcb-51e1-ad8a-b516d82105ef',
    '81c60b68-489e-5464-aa80-a8b66703285b',
    '8e77dd0b-932d-5790-9ba6-5c6df8434457',
    '91b0e6ff-bdb7-523c-b0bb-22b5a2a70b3f',
    '92091486-6cbc-53d0-8a01-6df6e3ca6455',
    '962d6bd6-a1ed-58be-a9ca-30cd88be29de',
    '96b32ca3-178c-5974-aa33-c18706ee473f',
    'a33a2ab3-b8d6-5124-b768-b796fc2d2dd5',
    'a4b7554d-09c9-567a-8b4b-4b282362e510',
    'ad1ff22c-ce53-5dc0-8cca-e1081d59449d',
    'ae082d90-8911-5df9-910f-0fdb3565e830',
    'b2d5983f-72df-5009-9453-a9e3a33a7e32',
    'b84dffcf-f665-5b90-b220-e885889044c6',
    'b853fc07-c16c-57d5-9717-6222ea9ad34e',
    'bdc2b86a-6f4e-5acc-8205-75c46c6c2788',
    'bec8f6a0-ca78-5ae2-aa20-3c9855eb7020',
    'c105f41b-d00f-527e-aec1-475b17e98733',
    'c4c140ee-66ed-570a-acf6-b1b1c8e660b3',
    'c7ff882e-20c3-519e-bfbc-47a9b593c665',
    'db229499-93a2-5118-8195-33a48505a489',
    'dc8b0319-70b6-5467-8c78-7c0bb4e370d8',
    'e26f28b0-c110-5598-83ff-f369ebb5642b',
    'e5fe9e20-47d3-5287-b97d-a1de25e8a7c3',
    'e6eb2f3a-47e9-5837-a89d-37faf9bc073d',
    'f2464461-71fe-5800-aebf-39d65a5b4037',
    'f549d909-2219-5b6c-bc8d-b305089ed406',
    'f5a9fc1e-22b2-5289-b89b-3a4630a4c8f0',
    'f6bfab69-6556-5e1e-886b-46576a5c6980',
    'fcac65bf-eb99-5ac1-a90c-3ebe20083ce6',
    'fca25cfa-fe5d-586b-a231-8e97106ad7c5',
    '4adc57a7-71a4-5fed-a6e0-bd8b59a261f2',
    '727be2fe-b941-5561-bce0-6778e090f594'
]

async def main():
    """Initialize local database with allowlist patients"""
    print("Initializing local database...")
    
    # Initialize database and sync service
    local_db = LocalDatabase("local_ehr.db")
    sync_service = SyncService("https://gel-landscapes-impaired-vitamin.trycloudflare.com/fhir", local_db)
    
    print(f"Syncing {len(ALLOWLIST_IDS)} allowlist patients...")
    
    # Sync specific patients
    results = await sync_service.sync_specific_patients(ALLOWLIST_IDS)
    
    # Print results
    success_count = sum(1 for result in results.values() if result.get('status') == 'success')
    error_count = len(results) - success_count
    
    print(f"Sync completed:")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    
    if error_count > 0:
        print("\nErrors:")
        for patient_id, result in results.items():
            if result.get('status') == 'error':
                print(f"  {patient_id}: {result.get('error')}")
    
    # Show database stats
    patient_count = local_db.get_patient_count()
    print(f"\nDatabase contains {patient_count} patients")
    
    print("Local database initialization complete!")

if __name__ == "__main__":
    asyncio.run(main())
