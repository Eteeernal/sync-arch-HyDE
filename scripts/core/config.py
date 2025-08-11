"""
Sync-Arch Configuration Management

Gestión centralizada de configuración del sistema.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

# Rutas globales
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.json"
DOTFILES_DIR = PROJECT_ROOT / "dotfiles"  
HOME = Path.home()

class ConfigManager:
    """Gestor de configuración del sistema"""
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Cargar configuración desde config.json"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logger.debug(f"Configuración cargada desde: {CONFIG_FILE}")
            return config
        except FileNotFoundError:
            logger.error(f"Archivo de configuración no encontrado: {CONFIG_FILE}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error al parsear configuración JSON: {e}")
            raise
    
    def save_config(self) -> None:
        """Guardar configuración actual a config.json"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.debug(f"Configuración guardada en: {CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            raise
    
    def get_common_paths(self) -> List[str]:
        """Obtener rutas comunes"""
        return self.config.get('common', [])
    
    def get_hostname_paths(self, hostname: str) -> List[str]:
        """Obtener rutas específicas de hostname"""
        return self.config.get(hostname, [])
    
    def get_ignore_patterns(self) -> List[str]:
        """Obtener patrones de ignore"""
        return self.config.get('ignore', [])
    
    def get_system_configs(self) -> List[str]:
        """Obtener configuraciones de sistema"""
        return self.config.get('system_configs', [])
    
    def get_conflict_resolution_config(self) -> Dict:
        """Obtener configuración de resolución de conflictos"""
        return self.config.get('conflict_resolution', {})
    
    def add_paths_to_section(self, section: str, paths: List[str]) -> None:
        """Agregar rutas a una sección específica"""
        if section not in self.config:
            self.config[section] = []
        self.config[section].extend(paths)
        logger.debug(f"Agregadas {len(paths)} rutas a sección '{section}'")
    
    def normalize_path(self, path: str) -> str:
        """Normalizar ruta removiendo prefijos inconsistentes"""
        # Remover prefijo home/ si existe (para compatibilidad)
        normalized = path.replace('home/', '')
        # Asegurar que empiece con . para rutas relativas al HOME
        if normalized and not normalized.startswith('.') and not normalized.startswith('/'):
            normalized = '.' + normalized if normalized.startswith('/') else normalized
        return normalized
