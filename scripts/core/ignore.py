"""
Sync-Arch Ignore Logic

Manejo de patrones ignore y lógica de precedencia: hostname > ignore > common
"""

import fnmatch
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class IgnoreManager:
    """Gestor de lógica ignore y precedencia"""
    
    def __init__(self, config_manager, hostname: str):
        self.config = config_manager
        self.hostname = hostname
    
    def should_ignore_path(self, path: str) -> bool:
        """Verificar si una ruta debe ser ignorada según patrones en config.json"""
        ignore_patterns = self.config.get_ignore_patterns()
        
        # Normalizar ruta
        normalized_path = self.config.normalize_path(path)
        
        for pattern in ignore_patterns:
            # Usar fnmatch para patrones con wildcards
            if fnmatch.fnmatch(normalized_path, pattern):
                logger.debug(f"Ruta {normalized_path} coincide con patrón ignore: {pattern}")
                return True
                
        return False

    def is_explicitly_included(self, path: str) -> bool:
        """Verificar si una ruta está explícitamente incluida en hostname específico"""
        hostname_files = self.config.get_hostname_paths(self.hostname)
        
        if not hostname_files:
            return False
        
        # Normalizar ruta
        normalized_path = self.config.normalize_path(path)
        
        for file_path in hostname_files:
            # Normalizar ruta del config
            config_path = self.config.normalize_path(file_path)
            
            # Verificar coincidencia exacta
            if config_path == normalized_path:
                logger.debug(f"Ruta {normalized_path} está explícitamente incluida en {self.hostname}")
                return True
                
            # Verificar si la ruta está dentro de una carpeta especificada
            if config_path.endswith('/') and normalized_path.startswith(config_path):
                logger.debug(f"Ruta {normalized_path} está dentro de carpeta explícita {config_path} en {self.hostname}")
                return True
                
        return False

    def should_process_path(self, path: str) -> Tuple[bool, str]:
        """
        Determinar si una ruta debe procesarse según precedencia: hostname > ignore > common
        
        Returns:
            tuple[bool, str]: (should_process, reason)
        """
        # Precedencia 1: Explícitamente incluido en hostname específico
        if self.is_explicitly_included(path):
            return True, f"explícitamente incluido en {self.hostname}"
            
        # Precedencia 2: En lista ignore
        if self.should_ignore_path(path):
            return False, "coincide con patrón ignore"
            
        # Precedencia 3: En common (se procesa por defecto)
        return True, "permitido por configuración común"
