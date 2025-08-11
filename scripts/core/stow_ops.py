"""
Sync-Arch Stow Operations

Operaciones GNU Stow para gestión de symlinks.
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from .utils import run_command

logger = logging.getLogger(__name__)

class StowOperations:
    """Operaciones GNU Stow"""
    
    def __init__(self, dotfiles_dir: Path, home_dir: Path, dry_run: bool = False):
        self.dotfiles_dir = dotfiles_dir
        self.home_dir = home_dir
        self.dry_run = dry_run
    
    def apply_stow(self, packages: List[str]) -> bool:
        """Aplicar GNU Stow con paquetes especificados"""
        try:
            # Primero, unstow todo para limpiar
            run_command(['stow', '-D'] + packages, 
                       cwd=self.dotfiles_dir, check=False, dry_run=self.dry_run)
            
            # Luego, restow para aplicar cambios
            run_command(['stow', '-v', '-R'] + packages, 
                       cwd=self.dotfiles_dir, dry_run=self.dry_run)
            
            logger.info(f"Stow aplicado exitosamente para: {', '.join(packages)}")
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando stow: {e}")
            return False
    
    def detect_existing_file_conflicts(self, ignore_manager, config_manager) -> List[Path]:
        """Detectar archivos existentes que conflictúan con symlinks de stow"""
        conflicts = []
        
        # Obtener rutas que serían gestionadas por stow
        managed_paths = []
        
        # Rutas de common (aplicando lógica ignore)
        for path in config_manager.get_common_paths():
            if path.endswith('/') or path == "":
                # Es carpeta, explorar contenido
                if path == "":
                    common_dir = self.dotfiles_dir / "common" / "home"
                else:
                    common_dir = self.dotfiles_dir / "common" / path.lstrip('./')
                    
                if common_dir.exists():
                    for root, dirs, files in os.walk(common_dir):
                        for file in files:
                            file_path = Path(root) / file
                            relative_path = file_path.relative_to(self.dotfiles_dir / "common")
                            
                            # Aplicar lógica ignore con precedencia
                            should_process, reason = ignore_manager.should_process_path(str(relative_path))
                            if should_process:
                                target_path = self.home_dir / relative_path
                                managed_paths.append(target_path)
                                logger.debug(f"Archivo gestionado: {relative_path} - {reason}")
                            else:
                                logger.debug(f"Archivo ignorado: {relative_path} - {reason}")
            else:
                # Es archivo específico
                should_process, reason = ignore_manager.should_process_path(path)
                if should_process:
                    target_path = self.home_dir / path.lstrip('./')
                    managed_paths.append(target_path)
                    logger.debug(f"Archivo gestionado: {path} - {reason}")
                else:
                    logger.debug(f"Archivo ignorado: {path} - {reason}")
        
        # Rutas específicas del hostname (siempre se procesan por precedencia)
        hostname = ignore_manager.hostname
        hostname_paths = config_manager.get_hostname_paths(hostname)
        for path in hostname_paths:
            target_path = self.home_dir / path.lstrip('./')
            managed_paths.append(target_path)
            logger.debug(f"Archivo explícito de {hostname}: {path}")
        
        # Verificar conflictos
        for target_path in managed_paths:
            if target_path.exists() and not target_path.is_symlink():
                conflicts.append(target_path)
                logger.debug(f"Conflicto detectado: archivo existente {target_path}")
        
        return conflicts

    def backup_existing_file(self, file_path: Path, backup_dir: Path) -> bool:
        """Hacer backup de un archivo existente"""
        try:
            # Mantener estructura de directorios en backup
            relative_path = file_path.relative_to(self.home_dir)
            backup_file = backup_dir / relative_path
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Haría backup: {file_path} → {backup_file}")
            else:
                shutil.copy2(file_path, backup_file)
                logger.info(f"Backup creado: {file_path} → {backup_file}")
            
            return True
        except Exception as e:
            logger.error(f"Error haciendo backup de {file_path}: {e}")
            return False

    def handle_existing_files_conflict(self, conflicts: List[Path], config_manager, force_overwrite: bool = False) -> bool:
        """Manejar archivos existentes que conflictúan con symlinks"""
        if not conflicts:
            logger.debug("No se detectaron conflictos con archivos existentes")
            return True
        
        logger.warning(f"Detectados {len(conflicts)} archivos existentes que conflictúan con symlinks")
        
        # Configuración de resolución de conflictos
        conflict_config = config_manager.get_conflict_resolution_config()
        interactive_confirm = conflict_config.get('interactive_confirm', True)
        backup_existing = conflict_config.get('backup_existing', True)
        
        # Confirmar acción si es interactivo y no está en force_overwrite
        if interactive_confirm and not force_overwrite and not self.dry_run:
            print(f"\n⚠️  Se encontraron {len(conflicts)} archivos existentes que serán reemplazados por symlinks:")
            for conflict in conflicts[:5]:  # Mostrar primeros 5
                print(f"   • {conflict}")
            if len(conflicts) > 5:
                print(f"   ... y {len(conflicts) - 5} archivos más")
            
            response = input("\n¿Crear backup y reemplazar con symlinks? (y/N): ")
            if response.lower() not in ['y', 'yes', 'sí', 's']:
                logger.info("Operación cancelada por el usuario")
                return False
        elif not force_overwrite and not self.dry_run:
            logger.error("Archivos existentes detectados. Use --force-overwrite para proceder automáticamente")
            return False
        
        # Crear backup si está habilitado
        if backup_existing:
            backup_location = conflict_config.get('backup_location', '~/.sync-arch-backup/')
            backup_dir = Path(backup_location).expanduser() / datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Crearía backup en: {backup_dir}")
            else:
                backup_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Creando backup en: {backup_dir}")
            
            # Hacer backup de archivos conflictivos
            for file_path in conflicts:
                if not self.backup_existing_file(file_path, backup_dir):
                    logger.error(f"Error en backup de {file_path}")
                    return False
        
        # Eliminar archivos conflictivos para permitir symlinks
        if not self.dry_run:
            for file_path in conflicts:
                try:
                    file_path.unlink()
                    logger.debug(f"Archivo eliminado para symlink: {file_path}")
                except Exception as e:
                    logger.error(f"Error eliminando {file_path}: {e}")
                    return False
        else:
            logger.info(f"[DRY-RUN] Eliminaría {len(conflicts)} archivos conflictivos")
        
        logger.info(f"Conflictos resueltos: {len(conflicts)} archivos preparados para symlinks")
        return True
