"""
Sync-Arch Sync Modes

Modos de sincronización: startup, shutdown, manual.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SyncModes:
    """Modos de sincronización del sistema"""
    
    def __init__(self, config_manager, ignore_manager, git_ops, stow_ops, conflict_resolver, 
                 force_overwrite: bool = False):
        self.config = config_manager
        self.ignore = ignore_manager
        self.git_ops = git_ops
        self.stow_ops = stow_ops
        self.conflicts = conflict_resolver
        self.force_overwrite = force_overwrite
    
    def startup_sync(self) -> bool:
        """Sincronización al inicio del sistema"""
        logger.info("=== INICIO: Sincronización de startup ===")
        
        # Sincronizar desde Git primero
        if not self.git_ops.sync_from_git():
            return False
        
        # Detectar y resolver conflictos de carpetas
        conflicts = self.conflicts.detect_conflicts()
        if conflicts:
            if not self.conflicts.reorganize_conflicted_folders(conflicts):
                return False
        
        # Manejar conflictos con archivos existentes
        existing_conflicts = self.stow_ops.detect_existing_file_conflicts(self.ignore, self.config)
        if not self.stow_ops.handle_existing_files_conflict(existing_conflicts, self.config, self.force_overwrite):
            return False
        
        # Aplicar stow
        packages = ['common']
        if self.ignore.hostname in self.config.config:
            packages.append(self.ignore.hostname)
        
        success = self.stow_ops.apply_stow(packages)
        
        if success:
            logger.info("=== FIN: Sincronización de startup completada ===")
        else:
            logger.error("=== FIN: Error en sincronización de startup ===")
        
        return success

    def shutdown_sync(self) -> bool:
        """Sincronización antes del apagado/suspensión"""
        logger.info("=== INICIO: Sincronización de shutdown ===")
        
        # Solo sincronizar cambios hacia Git (commit + push)
        success = self.git_ops.sync_to_git()
        
        if success:
            logger.info("=== FIN: Sincronización de shutdown completada ===")
        else:
            logger.error("=== FIN: Error en sincronización de shutdown ===")
        
        return success

    def manual_sync(self, force: bool = False) -> bool:
        """Sincronización manual (bidireccional completa)"""
        logger.info("=== INICIO: Sincronización manual ===")
        
        # Verificar cambios antes de proceder si no es forzado
        if not force:
            has_local = self.git_ops.has_local_changes()
            has_remote = self.git_ops.has_remote_changes()
            
            if not has_local and not has_remote:
                logger.info("No hay cambios para sincronizar")
                logger.info("=== FIN: Sincronización manual (sin cambios) ===")
                return True
        
        # Sincronizar desde Git primero
        if not self.git_ops.sync_from_git():
            return False
        
        # Detectar y resolver conflictos de carpetas
        conflicts = self.conflicts.detect_conflicts()
        if conflicts:
            if not self.conflicts.reorganize_conflicted_folders(conflicts):
                return False
        
        # Manejar conflictos con archivos existentes
        existing_conflicts = self.stow_ops.detect_existing_file_conflicts(self.ignore, self.config)
        if not self.stow_ops.handle_existing_files_conflict(existing_conflicts, self.config, self.force_overwrite):
            return False
        
        # Aplicar stow
        packages = ['common']
        if self.ignore.hostname in self.config.config:
            packages.append(self.ignore.hostname)
        
        if not self.stow_ops.apply_stow(packages):
            return False
        
        # Sincronizar cambios locales a Git
        success = self.git_ops.sync_to_git()
        
        if success:
            logger.info("=== FIN: Sincronización manual completada ===")
        else:
            logger.error("=== FIN: Error en sincronización manual ===")
        
        return success
