"""
sync_remote.py - One-way data synchronization from remote Render backend to local DB.

=== IMPORTANT: USAGE POLICY ===
This script is intended for ONE-TIME MIGRATION or DISASTER RECOVERY only.
It should NOT be used for regular daily synchronization.

When to use:
- Initial migration from Render to a new local/Neon database
- Disaster recovery to restore data from Render backup
- Development environment setup

When NOT to use:
- Regular daily sync (both environments should use the same Neon DB)
- Production data updates (use the API directly)

What it does:
- Reads all clients from remote: GET {REMOTE_BASE_URL}/api/v1/crm/clients
- For each client: creates or updates locally (including beneficiaries)
- Syncs snapshots, existing products, and new products per client
- Only adds/updates, NEVER deletes

How to run:
  1. Set environment variables:
     $env:REMOTE_BASE_URL = "https://your-render-backend.onrender.com"
     $env:DATABASE_URL = "postgresql://..."  # Target Neon DB
  2. Run: python -m app.services.sync_remote

=== END USAGE POLICY ===
"""
from __future__ import annotations

from app.services.sync_remote_service import sync_all_clients_from_remote


def main() -> None:
    sync_all_clients_from_remote()


if __name__ == "__main__":
    main()
