"""
Sync-Arch Conflict Resolution

Resolución de conflictos de override parcial y reorganización de carpetas.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Tuple
from .utils import run_command

logger = logging.getLogger(__name__)

class ConflictResolver:
    """Resolutor de conflictos de configuración"""
    
    def __init__(self, dotfiles_dir: Path, config_manager, ignore_manager, dry_run: bool = False):
        self.dotfiles_dir = dotfiles_dir
        self.config = config_manager
        self.ignore = ignore_manager
        self.dry_run = dry_run
    
    def detect_conflicts(self) -> List[Tuple[str, str, str]]:
        """Detectar conflictos de override parcial (carpeta en common + archivo específico en host)"""
        conflicts = []
        common_folders = [path for path in self.config.get_common_paths() if path.endswith('/')]
        
        for hostname, files in self.config.config.items():
            if hostname in ['common', 'ignore', 'system_configs', 'conflict_resolution']:
                continue
                
            for file_path in files:
                for common_folder in common_folders:
                    # Normalizar rutas para comparación
                    normalized_file = self.config.normalize_path(file_path)
                    normalized_folder = self.config.normalize_path(common_folder)
                    
                    # Verificar si el archivo está dentro de la carpeta común
                    if normalized_file.startswith(normalized_folder):
                        conflicts.append((common_folder, file_path, hostname))
                        logger.debug(f"Conflicto detectado: {common_folder} vs {file_path} ({hostname})")
        
        return conflicts

    def backup_and_migrate_file(self, source_path: Path, dest_path: Path) -> bool:
        """Migrar archivo preservando contenido"""
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.exists():
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Migraría: {source_path} → {dest_path}")
                else:
                    shutil.copy2(source_path, dest_path)
                    logger.debug(f"Archivo migrado: {source_path} → {dest_path}")
                return True
            elif dest_path.exists():
                logger.debug(f"Archivo ya existe en destino: {dest_path}")
                return True
            else:
                logger.warning(f"Archivo no existe ni en fuente ni en destino: {source_path} → {dest_path}")
                return False
        except Exception as e:
            logger.error(f"Error migrando archivo {source_path} → {dest_path}: {e}")
            return False

    def reorganize_conflicted_folders(self, conflicts: List[Tuple[str, str, str]]) -> bool:
        """Reorganizar carpetas con conflictos de override parcial"""
        if not conflicts:
            return True
            
        logger.info(f"Reorganizando {len(conflicts)} conflictos de carpetas...")
        
        # Agrupar conflictos por carpeta común
        folder_conflicts = {}
        for common_folder, file_path, hostname in conflicts:
            if common_folder not in folder_conflicts:
                folder_conflicts[common_folder] = []
            folder_conflicts[common_folder].append((file_path, hostname))
        
        for common_folder, file_assignments in folder_conflicts.items():
            logger.info(f"Procesando carpeta: {common_folder}")
            
            # Ruta de la carpeta común
            common_folder_path = self.dotfiles_dir / "common" / common_folder.lstrip('./')
            
            if not common_folder_path.exists():
                logger.warning(f"Carpeta común no existe: {common_folder_path}")
                continue
            
            # Migrar cada archivo específico a su hostname correspondiente
            success = True
            for file_path, hostname in file_assignments:
                # Verificar si el archivo debe procesarse según lógica ignore
                should_process, reason = self.ignore.should_process_path(file_path)
                if not should_process:
                    logger.info(f"Omitiendo migración de {file_path}: {reason}")
                    continue
                
                source_file = self.dotfiles_dir / "common" / file_path.lstrip('./')
                dest_file = self.dotfiles_dir / hostname / file_path.lstrip('./')
                
                # Si el archivo no existe en common pero está explícitamente incluido en hostname,
                # es normal (archivo que no estaba en common originalmente)
                if not source_file.exists() and self.ignore.is_explicitly_included(file_path):
                    logger.debug(f"Archivo {file_path} no existe en common pero está explícitamente en {hostname} - OK")
                    continue
                
                if not self.backup_and_migrate_file(source_file, dest_file):
                    success = False
                elif not self.dry_run and source_file.exists():
                    # Solo eliminar archivo de common si realmente se migró desde ahí
                    try:
                        source_file.unlink()
                        logger.debug(f"Archivo eliminado de common: {source_file}")
                    except OSError as e:
                        logger.warning(f"No se pudo eliminar archivo de common: {e}")
            
            if not success:
                logger.error(f"Error reorganizando carpeta: {common_folder}")
                return False
        
        return True
