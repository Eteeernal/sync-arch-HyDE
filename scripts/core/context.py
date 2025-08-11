"""
Context Manager para Sync-Arch

Proporciona un contexto centralizado con todos los managers y utilidades
necesarios para las operaciones del sistema. Esto elimina la duplicidad
de inicialización y mejora la gestión de dependencias.
"""

import logging
from pathlib import Path
from typing import Optional

from .config import ConfigManager
from .ignore import IgnoreManager  
from .git_ops import GitOperations
from .stow_ops import StowOperations
from .conflicts import ConflictResolver
from .path_utils import PathUtils

logger = logging.getLogger(__name__)

class SyncArchContext:
    """
    Context manager centralizado para Sync-Arch
    
    Proporciona acceso unificado a todos los managers y utilidades
    necesarios para las operaciones del sistema.
    """
    
    def __init__(self, 
                 dotfiles_dir: Path,
                 home_dir: Path, 
                 project_root: Path,
                 hostname: str,
                 dry_run: bool = True):
        """
        Inicializar contexto con todas las dependencias
        
        Args:
            dotfiles_dir: Directorio de dotfiles
            home_dir: Directorio home del usuario  
            project_root: Directorio raíz del proyecto
            hostname: Nombre del host
            dry_run: Si ejecutar en modo dry-run
        """
        self.dotfiles_dir = dotfiles_dir
        self.home_dir = home_dir
        self.project_root = project_root
        self.hostname = hostname
        self.dry_run = dry_run
        
        # Inicializar managers principales
        self.config = ConfigManager()
        self.ignore = IgnoreManager(self.config, hostname)
        self.git_ops = GitOperations(project_root, dry_run)
        self.stow_ops = StowOperations(dotfiles_dir, home_dir, dry_run)
        self.conflicts = ConflictResolver(dotfiles_dir, self.config, self.ignore, dry_run)
        self.path_utils = PathUtils(self.config, dotfiles_dir, home_dir, hostname)
        
        logger.debug(f"SyncArchContext inicializado para hostname: {hostname}")
    
    def get_config(self) -> ConfigManager:
        """Obtener el ConfigManager"""
        return self.config
    
    def get_ignore(self) -> IgnoreManager:
        """Obtener el IgnoreManager"""
        return self.ignore
    
    def get_git_ops(self) -> GitOperations:
        """Obtener GitOperations"""
        return self.git_ops
    
    def get_stow_ops(self) -> StowOperations:
        """Obtener StowOperations"""
        return self.stow_ops
    
    def get_conflicts(self) -> ConflictResolver:
        """Obtener ConflictResolver"""
        return self.conflicts
    
    def get_path_utils(self) -> PathUtils:
        """Obtener PathUtils"""
        return self.path_utils
    
    def is_dry_run(self) -> bool:
        """Verificar si está en modo dry-run"""
        return self.dry_run
    
    def set_dry_run(self, dry_run: bool) -> None:
        """Cambiar el modo dry-run en todos los managers"""
        self.dry_run = dry_run
        self.git_ops.dry_run = dry_run
        self.stow_ops.dry_run = dry_run
        self.conflicts.dry_run = dry_run
        
        logger.debug(f"Modo dry-run cambiado a: {dry_run}")
