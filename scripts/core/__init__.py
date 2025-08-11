"""
Sync-Arch Core Modules

Módulos principales para la funcionalidad del sistema:
- config: Gestión de configuración
- ignore: Lógica de ignore y precedencia  
- git_ops: Operaciones Git
- stow_ops: Operaciones GNU Stow
- conflicts: Resolución de conflictos
- utils: Utilidades comunes
"""

from .config import ConfigManager
from .ignore import IgnoreManager
from .git_ops import GitOperations
from .stow_ops import StowOperations
from .conflicts import ConflictResolver
from .utils import SyncLock, setup_logging

__all__ = [
    'ConfigManager',
    'IgnoreManager', 
    'GitOperations',
    'StowOperations',
    'ConflictResolver',
    'SyncLock',
    'setup_logging'
]
