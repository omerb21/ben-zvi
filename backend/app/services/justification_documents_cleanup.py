from __future__ import annotations

import logging
import shutil
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models import Client
from app.services.justification_b1 import _get_client_export_dir
from app.utils.paths import get_app_base_dir

logger = logging.getLogger(__name__)


def delete_all_justification_documents(db: Session) -> Dict[str, int | List[str]]:
    """Delete all justification PDF documents for all clients.
    
    Returns a report with:
    - totalClients: number of clients processed
    - deletedDirectories: number of client export directories deleted
    - totalFilesDeleted: total number of files deleted
    - totalBytesFreed: total disk space freed in bytes
    - deletedClientNames: list of client names whose documents were deleted
    """
    
    total_clients = 0
    deleted_directories = 0
    total_files_deleted = 0
    total_bytes_freed = 0
    deleted_client_names: List[str] = []
    
    # Get all clients
    clients = db.query(Client).all()
    total_clients = len(clients)
    
    logger.info(f"Starting deletion of justification documents for {total_clients} clients")
    
    for client in clients:
        try:
            export_dir = _get_client_export_dir(client)
            
            if export_dir.exists() and export_dir.is_dir():
                # Count files and calculate size before deletion
                files_in_dir = list(export_dir.rglob("*"))
                file_count = sum(1 for f in files_in_dir if f.is_file())
                dir_size = sum(f.stat().st_size for f in files_in_dir if f.is_file())
                
                # Delete the entire client export directory
                shutil.rmtree(export_dir)
                
                deleted_directories += 1
                total_files_deleted += file_count
                total_bytes_freed += dir_size
                
                client_name = f"{client.first_name or ''} {client.last_name or ''}".strip() or f"Client {client.id}"
                deleted_client_names.append(client_name)
                
                logger.info(f"Deleted export directory for client {client.id}: {file_count} files, {dir_size} bytes")
        
        except Exception as exc:
            logger.error(f"Failed to delete export directory for client {client.id}: {exc}")
            continue
    
    # Also check for orphaned directories in exports folder
    try:
        base_dir = get_app_base_dir()
        exports_dir = base_dir / "exports"
        
        if exports_dir.exists():
            # Get all client IDs
            client_ids = {client.id for client in clients}
            
            # Check for directories that don't match any client
            for item in exports_dir.iterdir():
                if item.is_dir():
                    # Directory format: {client_id}_{first_name}_{last_name}
                    dir_name_parts = item.name.split("_", 1)
                    if dir_name_parts:
                        try:
                            dir_client_id = int(dir_name_parts[0])
                            # If this client ID doesn't exist in DB, it's orphaned
                            if dir_client_id not in client_ids:
                                files_in_dir = list(item.rglob("*"))
                                file_count = sum(1 for f in files_in_dir if f.is_file())
                                dir_size = sum(f.stat().st_size for f in files_in_dir if f.is_file())
                                
                                shutil.rmtree(item)
                                
                                deleted_directories += 1
                                total_files_deleted += file_count
                                total_bytes_freed += dir_size
                                deleted_client_names.append(f"Orphaned: {item.name}")
                                
                                logger.info(f"Deleted orphaned directory {item.name}: {file_count} files, {dir_size} bytes")
                        except (ValueError, IndexError):
                            # Skip directories that don't follow the naming convention
                            continue
    
    except Exception as exc:
        logger.error(f"Failed to clean orphaned directories: {exc}")
    
    logger.info(
        f"Document deletion complete: {deleted_directories} directories, "
        f"{total_files_deleted} files, {total_bytes_freed} bytes freed"
    )
    
    return {
        "totalClients": total_clients,
        "deletedDirectories": deleted_directories,
        "totalFilesDeleted": total_files_deleted,
        "totalBytesFreed": total_bytes_freed,
        "deletedClientNames": deleted_client_names,
    }
