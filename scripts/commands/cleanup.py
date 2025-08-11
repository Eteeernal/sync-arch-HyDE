"""
Sync-Arch Cleanup Command

Comando para limpiar archivos del repositorio que no deberían estar según patrones ignore.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

class CleanupCommand:
    """Comando de limpieza del repositorio"""
    
    def __init__(self, config_manager, ignore_manager, dotfiles_dir: Path, dry_run: bool = False):
        self.config = config_manager
        self.ignore = ignore_manager
        self.dotfiles_dir = dotfiles_dir
        self.dry_run = dry_run
    
    def scan_ignored_files_in_repo(self) -> List[Tuple[Path, str]]:
        """Escanear repositorio buscando archivos que coinciden con patrones ignore"""
        ignored_files = []
        
        # Escanear carpeta common
        common_dir = self.dotfiles_dir / "common"
        if common_dir.exists():
            ignored_files.extend(self._scan_directory(common_dir, "common"))
        
        # Escanear carpetas específicas de hostname (solo verificar si no están explícitamente incluidos)
        for hostname_dir in self.dotfiles_dir.iterdir():
            if (hostname_dir.is_dir() and 
                hostname_dir.name not in ['common', '.git'] and
                not hostname_dir.name.startswith('.')):
                ignored_files.extend(self._scan_directory(hostname_dir, hostname_dir.name))
        
        return ignored_files
    
    def _scan_directory(self, base_dir: Path, context: str) -> List[Tuple[Path, str]]:
        """Escanear un directorio específico buscando archivos ignorados"""
        ignored_files = []
        
        for root, dirs, files in os.walk(base_dir):
            for item in dirs + files:
                item_path = Path(root) / item
                
                # Obtener ruta relativa desde base_dir
                relative_path = item_path.relative_to(base_dir)
                
                # Para common, quitar prefijo "home/" si existe para normalizar
                if context == "common" and str(relative_path).startswith("home/"):
                    normalized_path = str(relative_path)[5:]  # Quitar "home/"
                else:
                    normalized_path = str(relative_path)
                
                # Verificar si debería ser ignorado
                if context == "common":
                    # En common, solo verificar ignore
                    if self.ignore.should_ignore_path(normalized_path):
                        ignored_files.append((item_path, f"ignore pattern: {normalized_path}"))
                else:
                    # En carpetas hostname, verificar que no esté explícitamente incluido
                    if (self.ignore.should_ignore_path(normalized_path) and
                        not self.ignore.is_explicitly_included(normalized_path)):
                        ignored_files.append((item_path, f"ignore pattern: {normalized_path} (not explicit in {context})"))
        
        return ignored_files
    
    def cleanup_ignored_files(self, ignored_files: List[Tuple[Path, str]]) -> bool:
        """Eliminar archivos ignorados del repositorio"""
        if not ignored_files:
            print("✅ No se encontraron archivos para limpiar")
            return True
        
        print(f"🧹 Encontrados {len(ignored_files)} elementos para limpiar:")
        print()
        
        # Mostrar lista de elementos a eliminar
        for file_path, reason in ignored_files:
            relative_to_repo = file_path.relative_to(self.dotfiles_dir)
            print(f"📁 {relative_to_repo}")
            print(f"   Razón: {reason}")
        
        print()
        
        if self.dry_run:
            print("🔍 [DRY-RUN] Los archivos arriba serían eliminados del repositorio")
            print("💡 Para ejecutar la limpieza real, usa: --no-dry-run")
            return True
        
        # Confirmar con el usuario
        response = input("¿Eliminar estos archivos del repositorio? (y/N): ")
        if response.lower() not in ['y', 'yes', 'sí', 's']:
            print("❌ Limpieza cancelada")
            return False
        
        # Eliminar archivos
        success_count = 0
        for file_path, reason in ignored_files:
            try:
                if file_path.is_dir():
                    # Eliminar directorio y su contenido
                    import shutil
                    shutil.rmtree(file_path)
                    logger.info(f"Directorio eliminado: {file_path}")
                else:
                    # Eliminar archivo
                    file_path.unlink()
                    logger.info(f"Archivo eliminado: {file_path}")
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error eliminando {file_path}: {e}")
                print(f"❌ Error eliminando {file_path.relative_to(self.dotfiles_dir)}: {e}")
        
        if success_count == len(ignored_files):
            print(f"✅ Limpieza completada: {success_count} elementos eliminados")
            print("💡 Recuerda hacer commit de los cambios")
            return True
        else:
            print(f"⚠️  Limpieza parcial: {success_count}/{len(ignored_files)} elementos eliminados")
            return False
    
    def run_cleanup(self) -> bool:
        """Ejecutar limpieza completa"""
        print("🧹 Iniciando limpieza del repositorio...")
        print("🔍 Buscando archivos que coinciden con patrones ignore...")
        print()
        
        ignored_files = self.scan_ignored_files_in_repo()
        
        if not ignored_files:
            print("✅ El repositorio está limpio - no hay archivos que coincidan con patrones ignore")
            return True
        
        return self.cleanup_ignored_files(ignored_files)
