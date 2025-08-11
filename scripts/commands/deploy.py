"""
Sync-Arch Deploy Command

Comando para desplegar symlinks de forma segura con backup automático
para permitir rollback en caso de problemas.
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class DeployCommand:
    """Comando de despliegue seguro con backup"""
    
    def __init__(self, config_manager, ignore_manager, stow_ops, dotfiles_dir: Path, home_dir: Path, dry_run: bool = True):
        self.config = config_manager
        self.ignore = ignore_manager
        self.stow_ops = stow_ops
        self.dotfiles_dir = dotfiles_dir
        self.home_dir = home_dir
        self.hostname = ignore_manager.hostname
        self.dry_run = dry_run
        
        # Directorio de backup por hostname
        self.backup_dir = Path.home() / ".sync-arch-backups" / self.hostname
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Importar PathUtils del core
        from core.path_utils import PathUtils
        self.path_utils = PathUtils(config_manager, dotfiles_dir, home_dir, self.hostname)
    
    def get_conflicting_files(self) -> List[Dict]:
        """Obtener lista de archivos que necesitan ser reemplazados por symlinks"""
        conflicting_files = []
        
        # Obtener rutas gestionadas
        managed_paths = self._get_managed_paths()
        
        for path_info in managed_paths:
            normalized_path = path_info['normalized']
            source = path_info['source']
            
            # Verificar existencia en repo
            repo_path = self._get_repo_path(source, normalized_path)
            if not repo_path.exists():
                continue
            
            # Verificar existencia en $HOME
            home_path = self.home_dir / normalized_path
            if not home_path.exists():
                continue
            
            # Si existe pero no es symlink correcto, es conflictivo
            if not (home_path.is_symlink() and 
                   home_path.resolve() == repo_path.resolve()):
                conflicting_files.append({
                    'path': normalized_path,
                    'source': source,
                    'home_path': home_path,
                    'repo_path': repo_path,
                    'is_symlink': home_path.is_symlink(),
                    'is_file': home_path.is_file(),
                    'is_dir': home_path.is_dir()
                })
        
        return conflicting_files
    
    def create_backup(self, files_to_backup: List[Dict]) -> str:
        """Crear backup timestamped de archivos conflictivos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        current_backup_dir = self.backup_dir / backup_name
        
        if self.dry_run:
            print(f"🔄 [DRY-RUN] Crearía backup en: {current_backup_dir}")
            return backup_name
        
        current_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo de metadatos
        metadata_file = current_backup_dir / "backup_metadata.txt"
        with open(metadata_file, 'w') as f:
            f.write(f"Backup creado: {datetime.now().isoformat()}\n")
            f.write(f"Hostname: {self.hostname}\n")
            f.write(f"Total archivos: {len(files_to_backup)}\n")
            f.write("\nArchivos respaldados:\n")
            
            for file_info in files_to_backup:
                home_path = file_info['home_path']
                rel_path = file_info['path']
                
                # Crear estructura de directorios en backup
                backup_file_path = current_backup_dir / rel_path
                backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    if home_path.is_dir():
                        shutil.copytree(home_path, backup_file_path, dirs_exist_ok=True)
                        f.write(f"DIR:  {rel_path}\n")
                    else:
                        shutil.copy2(home_path, backup_file_path)
                        f.write(f"FILE: {rel_path}\n")
                    
                    logger.info(f"Backup creado: {home_path} -> {backup_file_path}")
                    
                except Exception as e:
                    logger.error(f"Error creando backup para {home_path}: {e}")
                    f.write(f"ERROR: {rel_path} - {e}\n")
        
        print(f"✅ Backup creado: {current_backup_dir}")
        return backup_name
    
    def remove_conflicting_files(self, files_to_remove: List[Dict]) -> bool:
        """Eliminar archivos conflictivos para permitir symlinks"""
        success = True
        
        for file_info in files_to_remove:
            home_path = file_info['home_path']
            rel_path = file_info['path']
            
            if self.dry_run:
                print(f"🗑️  [DRY-RUN] Eliminaría: {home_path}")
                continue
            
            try:
                if home_path.is_dir():
                    shutil.rmtree(home_path)
                else:
                    home_path.unlink()
                
                logger.info(f"Archivo conflictivo eliminado: {home_path}")
                print(f"🗑️  Eliminado: {rel_path}")
                
            except Exception as e:
                logger.error(f"Error eliminando {home_path}: {e}")
                print(f"❌ Error eliminando {rel_path}: {e}")
                success = False
        
        return success
    
    def deploy_symlinks(self) -> bool:
        """Desplegar symlinks usando Stow"""
        if self.dry_run:
            print("🔗 [DRY-RUN] Desplegaría symlinks usando Stow")
            return True
        
        try:
            # Usar stow para crear symlinks
            packages = ["common", self.hostname]
            existing_packages = [pkg for pkg in packages if (self.dotfiles_dir / pkg).exists()]
            
            if not existing_packages:
                print("❌ No hay paquetes para desplegar")
                return False
            
            print(f"🔗 Desplegando symlinks para: {', '.join(existing_packages)}")
            return self.stow_ops.apply_stow(existing_packages)
            
        except Exception as e:
            logger.error(f"Error desplegando symlinks: {e}")
            print(f"❌ Error desplegando symlinks: {e}")
            return False
    
    def rollback(self, backup_name: str = None) -> bool:
        """Hacer rollback desde un backup específico o el más reciente"""
        if not backup_name:
            # Usar el backup más reciente
            backups = sorted([d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")])
            if not backups:
                print("❌ No hay backups disponibles para rollback")
                return False
            backup_name = backups[-1].name
        
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            print(f"❌ Backup no encontrado: {backup_path}")
            return False
        
        print(f"🔄 Iniciando rollback desde: {backup_name}")
        
        # Leer metadatos
        metadata_file = backup_path / "backup_metadata.txt"
        if metadata_file.exists():
            print(f"📋 Información del backup:")
            with open(metadata_file, 'r') as f:
                for line in f.readlines()[:4]:  # Primeras 4 líneas
                    print(f"   {line.strip()}")
        
        if self.dry_run:
            print(f"🔄 [DRY-RUN] Restauraría archivos desde {backup_path}")
            return True
        
        # Confirmar rollback
        response = input(f"\n¿Confirmar rollback desde {backup_name}? (y/N): ")
        if response.lower() not in ['y', 'yes', 'sí', 's']:
            print("❌ Rollback cancelado")
            return False
        
        # Restaurar archivos
        success = True
        for item in backup_path.iterdir():
            if item.name == "backup_metadata.txt":
                continue
            
            target_path = self.home_dir / item.name
            
            try:
                # Eliminar symlink/archivo existente si existe
                if target_path.exists() or target_path.is_symlink():
                    if target_path.is_dir() and not target_path.is_symlink():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
                
                # Restaurar desde backup
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if item.is_dir():
                    shutil.copytree(item, target_path)
                else:
                    shutil.copy2(item, target_path)
                
                print(f"✅ Restaurado: {target_path.relative_to(self.home_dir)}")
                
            except Exception as e:
                logger.error(f"Error restaurando {item}: {e}")
                print(f"❌ Error restaurando {item.name}: {e}")
                success = False
        
        if success:
            print(f"✅ Rollback completado desde {backup_name}")
        else:
            print(f"⚠️  Rollback parcial desde {backup_name}")
        
        return success
    
    def list_backups(self) -> None:
        """Listar backups disponibles"""
        backups = sorted([d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")])
        
        if not backups:
            print("📁 No hay backups disponibles")
            return
        
        print(f"📁 Backups disponibles para {self.hostname}:")
        print(f"   Directorio: {self.backup_dir}")
        print()
        
        for backup in backups:
            metadata_file = backup / "backup_metadata.txt"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    lines = f.readlines()
                    created = lines[0].strip().split(': ', 1)[1] if len(lines) > 0 else "Unknown"
                    file_count = lines[2].strip().split(': ', 1)[1] if len(lines) > 2 else "Unknown"
                
                print(f"   📦 {backup.name}")
                print(f"      Creado: {created}")
                print(f"      Archivos: {file_count}")
                print()
    
    def run_deploy(self) -> bool:
        """Ejecutar despliegue completo con backup"""
        dry_status = " [DRY-RUN]" if self.dry_run else ""
        print(f"🚀 Iniciando despliegue seguro...{dry_status}")
        print()
        
        # Obtener archivos conflictivos
        conflicting_files = self.get_conflicting_files()
        
        if not conflicting_files:
            print("✅ No hay archivos conflictivos - todos los symlinks están correctos")
            return True
        
        print(f"📋 Archivos a reemplazar con symlinks: {len(conflicting_files)}")
        for file_info in conflicting_files:
            file_type = "DIR" if file_info['is_dir'] else "SYMLINK" if file_info['is_symlink'] else "FILE"
            print(f"   {file_type}: {file_info['path']}")
        print()
        
        if not self.dry_run:
            # Confirmar operación
            response = input("¿Continuar con el despliegue? (y/N): ")
            if response.lower() not in ['y', 'yes', 'sí', 's']:
                print("❌ Despliegue cancelado")
                return False
        
        # Crear backup
        print("📦 Creando backup de seguridad...")
        backup_name = self.create_backup(conflicting_files)
        
        # Eliminar archivos conflictivos
        print("🗑️  Eliminando archivos conflictivos...")
        if not self.remove_conflicting_files(conflicting_files):
            print("❌ Error eliminando archivos - abortando")
            return False
        
        # Desplegar symlinks
        print("🔗 Desplegando symlinks...")
        if not self.deploy_symlinks():
            print(f"❌ Error desplegando symlinks")
            if not self.dry_run:
                print(f"💡 Usa: ./scripts/sync.sh rollback {backup_name}")
            return False
        
        print(f"✅ Despliegue completado exitosamente")
        if not self.dry_run:
            print(f"💾 Backup disponible: {backup_name}")
            print(f"💡 Si hay problemas: ./scripts/sync.sh rollback {backup_name}")
        
        return True
    
    def _get_managed_paths(self) -> List[Dict]:
        """Obtener todas las rutas gestionadas"""
        return self.path_utils.get_managed_paths(include_system_configs=False)
    
    def _get_repo_path(self, source: str, normalized_path: str) -> Path:
        """Obtener la ruta en el repositorio"""
        return self.path_utils.get_repo_path(source, normalized_path)
