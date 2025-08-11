"""
Utilidades de rutas para Sync-Arch

Funciones centralizadas para manejo de rutas del repositorio,
rutas gestionadas y normalización de paths.
"""

import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class PathUtils:
    """Utilidades centralizadas para manejo de rutas"""
    
    def __init__(self, config_manager, dotfiles_dir: Path, home_dir: Path, hostname: str = None):
        self.config = config_manager
        self.dotfiles_dir = dotfiles_dir
        self.home_dir = home_dir
        self.hostname = hostname or "localhost"
    
    def get_repo_path(self, source: str, normalized_path: str) -> Path:
        """Obtener la ruta en el repositorio para un archivo/directorio
        
        Args:
            source: 'common', 'system_configs' o hostname
            normalized_path: Ruta normalizada relativa a $HOME o absoluta para system
            
        Returns:
            Path: Ruta completa en el repositorio
        """
        if source == 'common':
            return self.dotfiles_dir / "common" / "home" / normalized_path
        elif source == 'system_configs':
            return self.dotfiles_dir / "system_configs" / normalized_path.lstrip('/')
        else:
            # source es el hostname (ej: "archlinux")
            return self.dotfiles_dir / source / "home" / normalized_path
    
    def get_home_path(self, normalized_path: str) -> Path:
        """Obtener la ruta en $HOME para un archivo/directorio
        
        Args:
            normalized_path: Ruta normalizada relativa a $HOME
            
        Returns:
            Path: Ruta completa en $HOME
        """
        return self.home_dir / normalized_path
    
    def get_managed_paths(self, include_system_configs: bool = True) -> List[Dict]:
        """Obtener todas las rutas gestionadas por sync-arch
        
        Args:
            include_system_configs: Si incluir configuraciones del sistema
            
        Returns:
            List[Dict]: Lista de diccionarios con información de cada ruta gestionada
                Cada dict contiene: 'path', 'normalized', 'source'
        """
        managed_paths = []
        
        # Rutas comunes
        common_paths = self.config.get_common_paths()
        for path in common_paths:
            if path == "":  # HOME approach - se maneja todo en común
                continue
            normalized = self.config.normalize_path(path)
            managed_paths.append({
                'path': path,
                'normalized': normalized,
                'source': 'common'
            })
        
        # Rutas específicas del hostname
        hostname_paths = self.config.get_hostname_paths(self.hostname)
        for path in hostname_paths:
            normalized = self.config.normalize_path(path)
            managed_paths.append({
                'path': path,
                'normalized': normalized,
                'source': self.hostname
            })
        
        # Configuraciones del sistema
        if include_system_configs:
            system_configs = self.config.get_system_configs()
            for sys_path_str in system_configs:
                normalized_sys_path = self.config.normalize_path(sys_path_str)
                managed_paths.append({
                    'path': sys_path_str,
                    'normalized': normalized_sys_path,
                    'source': 'system_configs'
                })
        
        return managed_paths
    
    def get_all_managed_paths_dict(self, include_system_configs: bool = True) -> Dict[str, Dict]:
        """Obtener todas las rutas gestionadas como diccionario indexado por path
        
        Args:
            include_system_configs: Si incluir configuraciones del sistema
            
        Returns:
            Dict[str, Dict]: Diccionario indexado por 'normalized' con info de cada ruta
        """
        managed_paths = self.get_managed_paths(include_system_configs)
        return {path_info['normalized']: path_info for path_info in managed_paths}
    
    def is_path_managed(self, normalized_path: str, include_system_configs: bool = True) -> bool:
        """Verificar si una ruta está siendo gestionada por sync-arch
        
        Args:
            normalized_path: Ruta normalizada a verificar
            include_system_configs: Si incluir configuraciones del sistema
            
        Returns:
            bool: True si la ruta está gestionada
        """
        managed_dict = self.get_all_managed_paths_dict(include_system_configs)
        return normalized_path in managed_dict
    
    def get_path_source(self, normalized_path: str, include_system_configs: bool = True) -> str:
        """Obtener la fuente (source) de una ruta gestionada
        
        Args:
            normalized_path: Ruta normalizada
            include_system_configs: Si incluir configuraciones del sistema
            
        Returns:
            str: 'common', hostname, 'system_configs' o None si no está gestionada
        """
        managed_dict = self.get_all_managed_paths_dict(include_system_configs)
        path_info = managed_dict.get(normalized_path)
        return path_info['source'] if path_info else None
    
    def find_managed_parent(self, normalized_path: str, include_system_configs: bool = True) -> Dict:
        """Encontrar el directorio padre gestionado más específico para una ruta
        
        Args:
            normalized_path: Ruta a verificar
            include_system_configs: Si incluir configuraciones del sistema
            
        Returns:
            Dict: Info del directorio padre gestionado o None si no hay
        """
        managed_paths = self.get_managed_paths(include_system_configs)
        
        # Ordenar por especificidad (rutas más largas primero)
        managed_paths.sort(key=lambda x: len(x['normalized']), reverse=True)
        
        normalized_path_obj = Path(normalized_path)
        
        for path_info in managed_paths:
            managed_path_obj = Path(path_info['normalized'])
            
            # Verificar si normalized_path está dentro de managed_path
            try:
                normalized_path_obj.relative_to(managed_path_obj)
                return path_info
            except ValueError:
                continue
        
        return None
    
    def resolve_path_conflicts(self, paths: List[str]) -> Dict[str, str]:
        """Resolver conflictos de rutas cuando hay overlaps entre common y hostname
        
        Args:
            paths: Lista de rutas normalizadas
            
        Returns:
            Dict[str, str]: Mapeo de path -> source final después de resolver conflictos
        """
        path_sources = {}
        
        for path in paths:
            source = self.get_path_source(path)
            if source:
                # Prioridad: hostname > ignore > common
                if path not in path_sources or source == self.hostname:
                    path_sources[path] = source
        
        return path_sources
    
    def get_relative_path(self, absolute_path: Path, base_path: Path) -> str:
        """Obtener ruta relativa segura entre dos paths
        
        Args:
            absolute_path: Ruta absoluta
            base_path: Ruta base
            
        Returns:
            str: Ruta relativa o ruta absoluta si no es relativa
        """
        try:
            return str(absolute_path.relative_to(base_path))
        except ValueError:
            return str(absolute_path)
    
    def ensure_repo_structure(self) -> None:
        """Asegurar que la estructura del repositorio existe"""
        directories_to_create = [
            self.dotfiles_dir / "common" / "home",
            self.dotfiles_dir / self.hostname / "home",
            self.dotfiles_dir / "system_configs"
        ]
        
        for directory in directories_to_create:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directorio asegurado: {directory}")
