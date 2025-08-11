"""
Sync-Arch Status Command

Comando para mostrar estado del repositorio y configuración.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class StatusCommand:
    """Comando de estado del sistema"""
    
    def __init__(self, config_manager, ignore_manager, git_ops):
        self.config = config_manager
        self.ignore = ignore_manager
        self.git_ops = git_ops
    
    def show_status(self) -> None:
        """Mostrar estado completo del sistema"""
        print("📊 Estado de Sync-Arch")
        print("=" * 50)
        
        # Información básica
        self._show_basic_info()
        
        # Estado Git
        self._show_git_status()
        
        # Configuración
        self._show_config_summary()
        
        # Rutas gestionadas
        self._show_managed_paths()
    
    def _show_basic_info(self) -> None:
        """Mostrar información básica"""
        print(f"\n🖥️  Hostname: {self.ignore.hostname}")
        print(f"📁 Home: {Path.home()}")
        print(f"⚙️  Config: {self.config.config}")
    
    def _show_git_status(self) -> None:
        """Mostrar estado de Git"""
        print(f"\n📡 Estado Git:")
        
        git_status = self.git_ops.get_status()
        
        if 'error' in git_status:
            print(f"❌ Error: {git_status['error']}")
            return
        
        print(f"   Branch: {git_status['branch']}")
        print(f"   Último commit: {git_status['last_commit']}")
        print(f"   Cambios pendientes: {'Sí' if git_status['has_changes'] else 'No'}")
        
        if git_status['has_changes']:
            print(f"\n📝 Cambios pendientes:")
            for line in git_status['status_output'].strip().split('\n'):
                if line.strip():
                    print(f"   {line}")
    
    def _show_config_summary(self) -> None:
        """Mostrar resumen de configuración"""
        print(f"\n⚙️  Configuración:")
        
        common_paths = self.config.get_common_paths()
        hostname_paths = self.config.get_hostname_paths(self.ignore.hostname)
        ignore_patterns = self.config.get_ignore_patterns()
        system_configs = self.config.get_system_configs()
        
        print(f"   Common: {len(common_paths)} rutas")
        print(f"   {self.ignore.hostname}: {len(hostname_paths)} rutas")
        print(f"   Ignore: {len(ignore_patterns)} patrones")
        print(f"   System: {len(system_configs)} configs")
    
    def _show_managed_paths(self) -> None:
        """Mostrar rutas gestionadas"""
        print(f"\n📂 Rutas Gestionadas:")
        
        # Common paths
        common_paths = self.config.get_common_paths()
        if common_paths:
            print(f"\n   📋 Common ({len(common_paths)}):")
            for path in common_paths[:5]:  # Mostrar primeras 5
                print(f"      • {path}")
            if len(common_paths) > 5:
                print(f"      ... y {len(common_paths) - 5} más")
        
        # Hostname specific paths
        hostname_paths = self.config.get_hostname_paths(self.ignore.hostname)
        if hostname_paths:
            print(f"\n   🖥️  {self.ignore.hostname} ({len(hostname_paths)}):")
            for path in hostname_paths[:5]:  # Mostrar primeras 5
                print(f"      • {path}")
            if len(hostname_paths) > 5:
                print(f"      ... y {len(hostname_paths) - 5} más")
        
        # Ignore patterns
        ignore_patterns = self.config.get_ignore_patterns()
        if ignore_patterns:
            print(f"\n   🚫 Ignore ({len(ignore_patterns)}):")
            for pattern in ignore_patterns[:5]:  # Mostrar primeros 5
                print(f"      • {pattern}")
            if len(ignore_patterns) > 5:
                print(f"      ... y {len(ignore_patterns) - 5} más")
        
        # System configs
        system_configs = self.config.get_system_configs()
        if system_configs:
            print(f"\n   🔧 System ({len(system_configs)}):")
            for config in system_configs[:3]:  # Mostrar primeros 3
                print(f"      • {config}")
            if len(system_configs) > 3:
                print(f"      ... y {len(system_configs) - 3} más")
        
        print()  # Línea en blanco al final
