"""
Sync-Arch Discover Command

Comando interactivo para descubrir y gestionar archivos no sincronizados.
"""

import os
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class DiscoverCommand:
    """Comando de descubrimiento interactivo"""
    
    def __init__(self, config_manager, ignore_manager, home_dir: Path):
        self.config = config_manager
        self.ignore = ignore_manager
        self.home_dir = home_dir
    
    def scan_unmanaged_paths(self) -> List[Path]:
        """Escanear $HOME en busca de archivos/carpetas no gestionados"""
        unmanaged = []
        
        # Obtener rutas actualmente gestionadas
        managed_paths = set()
        
        # Rutas de common (todo $HOME está gestionado si common contiene "")
        common_paths = self.config.get_common_paths()
        if "" in common_paths:
            # Si common gestiona todo, solo consideramos archivos explícitamente excluidos
            base_managed = True
        else:
            base_managed = False
            for path in common_paths:
                managed_paths.add(self.config.normalize_path(path))
        
        # Rutas específicas del hostname
        hostname_paths = self.config.get_hostname_paths(self.ignore.hostname)
        for path in hostname_paths:
            managed_paths.add(self.config.normalize_path(path))
        
        # Escanear $HOME
        for root, dirs, files in os.walk(self.home_dir):
            # Excluir directorios que no queremos escanear
            dirs[:] = [d for d in dirs if not d.startswith('.git') and d not in ['.cache', '.local/share/Trash']]
            
            for item in dirs + files:
                item_path = Path(root) / item
                relative_path = item_path.relative_to(self.home_dir)
                normalized_path = str(relative_path)
                
                # Verificar si está gestionado
                is_managed = False
                
                if base_managed:
                    # Si common gestiona todo, verificar si está ignorado o es específico
                    should_process, reason = self.ignore.should_process_path(normalized_path)
                    is_managed = should_process
                else:
                    # Verificar si coincide con alguna ruta gestionada
                    for managed_path in managed_paths:
                        if (normalized_path == managed_path or 
                            normalized_path.startswith(managed_path.rstrip('/') + '/') or
                            managed_path.endswith('/') and normalized_path.startswith(managed_path)):
                            is_managed = True
                            break
                
                if not is_managed and item_path.exists():
                    unmanaged.append(item_path)
        
        return unmanaged

    def interactive_discover(self) -> None:
        """Comando interactivo para descubrir y gestionar archivos no sincronizados"""
        print("🔍 Escaneando archivos no gestionados en $HOME...")
        unmanaged = self.scan_unmanaged_paths()
        
        if not unmanaged:
            print("✅ No se encontraron archivos sin gestionar")
            return
        
        print(f"📁 Encontrados {len(unmanaged)} elementos no gestionados")
        
        additions = {
            'common': [],
            self.ignore.hostname: [],
            'ignore': []
        }
        
        for item_path in unmanaged[:20]:  # Limitar a primeros 20 para no abrumar
            relative_path = item_path.relative_to(self.home_dir)
            
            print(f"\n📄 {relative_path}")
            print("¿Qué hacer con este elemento?")
            print("  [c] Agregar a COMMON (sincronizar en todos los equipos)")
            print(f"  [h] Agregar a {self.ignore.hostname.upper()} (solo este equipo)")
            print("  [i] IGNORE (no sincronizar nunca)")
            print("  [s] SKIP (omitir por ahora)")
            
            while True:
                choice = input("Elección [c/h/i/s]: ").lower().strip()
                if choice in ['c', 'h', 'i', 's']:
                    break
                print("Opción inválida. Use c, h, i o s.")
            
            if choice == 'c':
                additions['common'].append(str(relative_path))
                print(f"✅ Agregado a common: {relative_path}")
            elif choice == 'h':
                additions[self.ignore.hostname].append(str(relative_path))
                print(f"✅ Agregado a {self.ignore.hostname}: {relative_path}")
            elif choice == 'i':
                # Para carpetas, agregar patrón con /**
                pattern = str(relative_path)
                if item_path.is_dir():
                    pattern += "/**"
                additions['ignore'].append(pattern)
                print(f"✅ Agregado a ignore: {pattern}")
            else:
                print(f"⏭️  Omitido: {relative_path}")
        
        # Aplicar cambios al config.json
        if any(additions.values()):
            self.update_config_with_additions(additions)
            print("\n🎉 Config.json actualizado con los nuevos elementos")
        else:
            print("\n📝 No se realizaron cambios")

    def update_config_with_additions(self, additions: dict) -> None:
        """Actualizar config.json con nuevas adiciones"""
        total_added = 0
        for section, items in additions.items():
            if items:
                self.config.add_paths_to_section(section, items)
                total_added += len(items)
        
        # Guardar configuración
        self.config.save_config()
        logger.info(f"Config.json actualizado con {total_added} nuevos elementos")
