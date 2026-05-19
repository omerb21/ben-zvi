from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models import Client
from app.services.justification_b1 import _get_client_export_dir
from app.utils.paths import get_app_base_dir


def check_remaining_documents(db: Session) -> Dict[str, int | List[str]]:
    """Check how many justification documents remain on the server."""
    
    remaining_client_dirs: List[str] = []
    remaining_files = 0
    remaining_bytes = 0
    
    # Check all clients' export directories
    clients = db.query(Client).all()
    
    for client in clients:
        try:
            export_dir = _get_client_export_dir(client)
            
            if export_dir.exists() and export_dir.is_dir():
                # Count files in this client's directory
                files_in_dir = list(export_dir.rglob("*"))
                file_count = sum(1 for f in files_in_dir if f.is_file())
                dir_size = sum(f.stat().st_size for f in files_in_dir if f.is_file())
                
                if file_count > 0:
                    client_name = f"{client.first_name or ''} {client.last_name or ''}".strip() or f"Client {client.id}"
                    remaining_client_dirs.append(f"{client_name}: {file_count} files ({dir_size} bytes)")
                    remaining_files += file_count
                    remaining_bytes += dir_size
        
        except Exception:
            continue
    
    # Check for orphaned directories
    orphaned_dirs: List[str] = []
    try:
        base_dir = get_app_base_dir()
        exports_dir = base_dir / "exports"
        
        if exports_dir.exists():
            client_ids = {client.id for client in clients}
            
            for item in exports_dir.iterdir():
                if item.is_dir():
                    dir_name_parts = item.name.split("_", 1)
                    if dir_name_parts:
                        try:
                            dir_client_id = int(dir_name_parts[0])
                            if dir_client_id not in client_ids:
                                files_in_dir = list(item.rglob("*"))
                                file_count = sum(1 for f in files_in_dir if f.is_file())
                                dir_size = sum(f.stat().st_size for f in files_in_dir if f.is_file())
                                
                                if file_count > 0:
                                    orphaned_dirs.append(f"Orphaned {item.name}: {file_count} files ({dir_size} bytes)")
                                    remaining_files += file_count
                                    remaining_bytes += dir_size
                        except (ValueError, IndexError):
                            continue
    
    except Exception:
        pass
    
    return {
        "totalClients": len(clients),
        "clientsWithFiles": len(remaining_client_dirs),
        "orphanedDirectories": len(orphaned_dirs),
        "totalRemainingFiles": remaining_files,
        "totalRemainingBytes": remaining_bytes,
        "remainingClientDirs": remaining_client_dirs,
        "remainingOrphanedDirs": orphaned_dirs,
    }
