#!/usr/bin/env python3
"""
Sync-Arch: Sistema de sincronización inteligente de dotfiles
Autor: Sergio F.
Versión: 1.0.0

Este script maneja la sincronización bidireccional de dotfiles usando Git + GNU Stow,
con soporte para configuraciones comunes y específicas por hostname, migración automática
y reorganización inteligente de carpetas.
"""

import json
import os
import subprocess
import shutil
import socket
import argparse
import logging
import hashlib
import time
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import fcntl
import sys

# === CONFIGURACIÓN GLOBAL ===
HOME = Path.home()
REPO_DIR = Path(__file__).parent.parent
CONFIG_FILE = REPO_DIR / "config.json"
DOTFILES_DIR = REPO_DIR / "dotfiles"
LOG_DIR = HOME / ".local/state/sync-arch"
LOG_FILE = LOG_DIR / "sync.log"
LOCK_FILE = f"/tmp/sync-arch-{os.getenv('USER', 'unknown')}.lock"
HOSTNAME = socket.gethostname()

# Crear directorio de logs si no existe
LOG_DIR.mkdir(parents=True, exist_ok=True)

# === CONFIGURACIÓN DE LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SyncLock:
    """Manejo de lockfile para evitar ejecuciones concurrentes"""
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.lock_fd = None

    def __enter__(self):
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(f"{os.getpid()}\n{datetime.now().isoformat()}\n")
            self.lock_fd.flush()
            logger.debug(f"Lock adquirido: {self.lock_file}")
            return self
        except (IOError, OSError) as e:
            logger.error(f"No se pudo adquirir lock: {e}")
            if self.lock_fd:
                self.lock_fd.close()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
            self.lock_fd.close()
            try:
                os.unlink(self.lock_file)
                logger.debug(f"Lock liberado: {self.lock_file}")
            except OSError:
                pass

class SyncArch:
    """Clase principal para la sincronización de dotfiles"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, force_overwrite: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.force_overwrite = force_overwrite
        self.config = self.load_config()
        self.hostname = HOSTNAME
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.info(f"Iniciando Sync-Arch para hostname: {self.hostname}")
        logger.info(f"Modo dry-run: {'ACTIVADO' if dry_run else 'DESACTIVADO'}")
        if force_overwrite:
            logger.info("Modo force-overwrite: ACTIVADO")

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

    def should_ignore_path(self, path: str) -> bool:
        """Verificar si una ruta debe ser ignorada según patrones en config.json"""
        ignore_patterns = self.config.get('ignore', [])
        
        # Normalizar ruta removiendo prefijo home/ si existe
        normalized_path = path.replace('home/', '')
        
        for pattern in ignore_patterns:
            # Usar fnmatch para patrones con wildcards
            if fnmatch.fnmatch(normalized_path, pattern):
                logger.debug(f"Ruta {normalized_path} coincide con patrón ignore: {pattern}")
                return True
                
            # También verificar ruta completa con home/
            if fnmatch.fnmatch(path, pattern):
                logger.debug(f"Ruta {path} coincide con patrón ignore: {pattern}")
                return True
                
        return False

    def is_explicitly_included(self, path: str) -> bool:
        """Verificar si una ruta está explícitamente incluida en hostname específico"""
        if self.hostname not in self.config:
            return False
            
        hostname_files = self.config[self.hostname]
        
        # Normalizar ruta removiendo prefijo home/ si existe
        normalized_path = path.replace('home/', '')
        
        for file_path in hostname_files:
            # Remover prefijo home/ del config si existe
            config_path = file_path.replace('home/', '')
            
            # Verificar coincidencia exacta
            if config_path == normalized_path or config_path == path:
                logger.debug(f"Ruta {path} está explícitamente incluida en {self.hostname}")
                return True
                
            # Verificar si la ruta está dentro de una carpeta especificada
            if config_path.endswith('/') and (normalized_path.startswith(config_path) or path.startswith(config_path)):
                logger.debug(f"Ruta {path} está dentro de carpeta explícita {config_path} en {self.hostname}")
                return True
                
        return False

    def should_process_path(self, path: str) -> tuple[bool, str]:
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

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
        """Ejecutar comando con logging"""
        cmd_str = ' '.join(str(c) for c in cmd)
        logger.debug(f"Ejecutando: {cmd_str} (cwd: {cwd})")
        
        if self.dry_run and any(dangerous in cmd_str for dangerous in ['stow', 'git commit', 'git push', 'cp', 'mv', 'rm']):
            logger.info(f"[DRY-RUN] Simulando: {cmd_str}")
            return subprocess.CompletedProcess(cmd, 0, b"", b"")
        
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)
            if result.stdout:
                logger.debug(f"stdout: {result.stdout.strip()}")
            if result.stderr:
                logger.debug(f"stderr: {result.stderr.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Error ejecutando comando: {cmd_str}")
            logger.error(f"Código de salida: {e.returncode}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            raise

    def has_git_changes(self) -> bool:
        """Verificar si hay cambios en el repositorio Git"""
        try:
            # Verificar cambios locales
            result = self.run_command(['git', 'status', '--porcelain'], cwd=REPO_DIR, check=False)
            local_changes = bool(result.stdout.strip())
            
            # Verificar cambios remotos
            self.run_command(['git', 'fetch'], cwd=REPO_DIR, check=False)
            result = self.run_command(['git', 'rev-list', '--count', 'HEAD..origin/main'], cwd=REPO_DIR, check=False)
            remote_changes = int(result.stdout.strip() or "0") > 0
            
            logger.debug(f"Cambios locales: {local_changes}, cambios remotos: {remote_changes}")
            return local_changes or remote_changes
        except Exception as e:
            logger.warning(f"Error verificando cambios Git: {e}")
            return True  # Asumir cambios si hay error

    def get_file_hash(self, file_path: Path) -> Optional[str]:
        """Obtener hash MD5 de un archivo"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except (OSError, IOError):
            return None

    def detect_conflicts(self) -> List[Tuple[str, str, str]]:
        """Detectar conflictos de override parcial (carpeta en common + archivo específico en host)"""
        conflicts = []
        common_folders = [path for path in self.config.get('common', []) if path.endswith('/')]
        
        for hostname, files in self.config.items():
            if hostname in ['common', 'ignore', 'system_configs']:
                continue
                
            for file_path in files:
                for common_folder in common_folders:
                    if file_path.startswith(common_folder):
                        conflicts.append((common_folder, file_path, hostname))
                        logger.debug(f"Conflicto detectado: {common_folder} vs {file_path} ({hostname})")
        
        return conflicts

    def backup_and_migrate_file(self, source_path: Path, dest_path: Path) -> bool:
        """Migrar archivo preservando contenido"""
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.exists():
                if self.dry_run:
                    logger.info(f"[DRY-RUN] Migraría: {source_path} → {dest_path}")
                else:
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"Archivo migrado: {source_path} → {dest_path}")
                return True
            elif dest_path.exists():
                # Caso especial: archivo ya existe en destino (enfoque HOME)
                logger.debug(f"Archivo ya existe en destino: {dest_path}")
                return True
            else:
                logger.warning(f"Archivo no existe ni en fuente ni en destino: {source_path} → {dest_path}")
                return False
        except Exception as e:
            logger.error(f"Error migrando archivo {source_path} → {dest_path}: {e}")
            return False

    def detect_existing_file_conflicts(self) -> List[Path]:
        """Detectar archivos existentes que conflictúan con symlinks de stow"""
        conflicts = []
        
        # Obtener rutas que serían gestionadas por stow
        managed_paths = []
        
        # Rutas de common (aplicando lógica ignore)
        for path in self.config.get('common', []):
            if path.endswith('/'):
                # Es carpeta, explorar contenido
                common_dir = DOTFILES_DIR / "common" / path.lstrip('./')
                if common_dir.exists():
                    for root, dirs, files in os.walk(common_dir):
                        for file in files:
                            file_path = Path(root) / file
                            relative_path = file_path.relative_to(DOTFILES_DIR / "common")
                            
                            # Aplicar lógica ignore con precedencia
                            should_process, reason = self.should_process_path(str(relative_path))
                            if should_process:
                                target_path = HOME / relative_path
                                managed_paths.append(target_path)
                                logger.debug(f"Archivo gestionado: {relative_path} - {reason}")
                            else:
                                logger.debug(f"Archivo ignorado: {relative_path} - {reason}")
            else:
                # Es archivo específico
                should_process, reason = self.should_process_path(path)
                if should_process:
                    target_path = HOME / path.lstrip('./')
                    managed_paths.append(target_path)
                    logger.debug(f"Archivo gestionado: {path} - {reason}")
                else:
                    logger.debug(f"Archivo ignorado: {path} - {reason}")
        
        # Rutas específicas del hostname (siempre se procesan por precedencia)
        if self.hostname in self.config:
            for path in self.config[self.hostname]:
                target_path = HOME / path.lstrip('./')
                managed_paths.append(target_path)
                logger.debug(f"Archivo explícito de {self.hostname}: {path}")
        
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
            relative_path = file_path.relative_to(HOME)
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

    def handle_existing_files_conflict(self) -> bool:
        """Manejar archivos existentes que conflictúan con symlinks"""
        conflicts = self.detect_existing_file_conflicts()
        
        if not conflicts:
            logger.debug("No se detectaron conflictos con archivos existentes")
            return True
        
        logger.warning(f"Detectados {len(conflicts)} archivos existentes que conflictúan con symlinks")
        
        # Configuración de resolución de conflictos
        conflict_config = self.config.get('conflict_resolution', {})
        interactive_confirm = conflict_config.get('interactive_confirm', True)
        backup_existing = conflict_config.get('backup_existing', True)
        
        # Confirmar acción si es interactivo y no está en force_overwrite
        if interactive_confirm and not self.force_overwrite and not self.dry_run:
            print(f"\n⚠️  Se encontraron {len(conflicts)} archivos existentes que serán reemplazados por symlinks:")
            for conflict in conflicts[:5]:  # Mostrar primeros 5
                print(f"   • {conflict}")
            if len(conflicts) > 5:
                print(f"   ... y {len(conflicts) - 5} archivos más")
            
            response = input("\n¿Crear backup y reemplazar con symlinks? (y/N): ")
            if response.lower() not in ['y', 'yes', 'sí', 's']:
                logger.info("Operación cancelada por el usuario")
                return False
        elif not self.force_overwrite and not self.dry_run:
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

    def reorganize_conflicted_folders(self, conflicts: List[Tuple[str, str, str]]) -> bool:
        """Reorganizar carpetas con conflictos de override parcial"""
        if not conflicts:
            return True
            
        logger.info(f"Reorganizando {len(conflicts)} conflictos de carpetas...")
        
        # Agrupar conflictos por carpeta común
        folder_conflicts = {}
        for common_folder, file_path, hostname in conflicts:
            if common_folder not in folder_conflicts:
                folder_conflicts[common_folder] = []
            folder_conflicts[common_folder].append((file_path, hostname))
        
        for common_folder, file_assignments in folder_conflicts.items():
            logger.info(f"Procesando carpeta: {common_folder}")
            
            # Ruta de la carpeta común
            common_folder_path = DOTFILES_DIR / "common" / common_folder.lstrip('./')
            
            if not common_folder_path.exists():
                logger.warning(f"Carpeta común no existe: {common_folder_path}")
                continue
            
            # Migrar cada archivo específico a su hostname correspondiente
            success = True
            for file_path, hostname in file_assignments:
                # Verificar si el archivo debe procesarse según lógica ignore
                should_process, reason = self.should_process_path(file_path)
                if not should_process:
                    logger.info(f"Omitiendo migración de {file_path}: {reason}")
                    continue
                
                source_file = DOTFILES_DIR / "common" / file_path.lstrip('./')
                dest_file = DOTFILES_DIR / hostname / file_path.lstrip('./')
                
                # Si el archivo no existe en common pero está explícitamente incluido en hostname,
                # es normal (archivo que no estaba en common originalmente)
                if not source_file.exists() and self.is_explicitly_included(file_path):
                    logger.debug(f"Archivo {file_path} no existe en common pero está explícitamente en {hostname} - OK")
                    continue
                
                if not self.backup_and_migrate_file(source_file, dest_file):
                    success = False
                elif not self.dry_run and source_file.exists():
                    # Solo eliminar archivo de common si realmente se migró desde ahí
                    try:
                        source_file.unlink()
                        logger.debug(f"Archivo eliminado de common: {source_file}")
                    except OSError as e:
                        logger.warning(f"No se pudo eliminar archivo de common: {e}")
            
            if not success:
                logger.error(f"Error reorganizando carpeta: {common_folder}")
                return False
        
        return True

    def apply_stow(self, packages: List[str]) -> bool:
        """Aplicar GNU Stow con paquetes especificados"""
        try:
            # Primero, unstow todo para limpiar
            self.run_command(['stow', '-D'] + packages, cwd=DOTFILES_DIR, check=False)
            
            # Luego stow con reemplazo
            cmd = ['stow', '-v', '-R'] + packages
            result = self.run_command(cmd, cwd=DOTFILES_DIR)
            
            logger.info(f"Stow aplicado exitosamente para: {', '.join(packages)}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error aplicando stow: {e}")
            return False

    def sync_to_git(self) -> bool:
        """Sincronizar cambios al repositorio Git"""
        try:
            # Cambiar al directorio del repositorio
            os.chdir(REPO_DIR)
            
            # Verificar si hay cambios
            result = self.run_command(['git', 'status', '--porcelain'], check=False)
            if not result.stdout.strip():
                logger.info("No hay cambios para commitear")
                return True
            
            # Agregar cambios
            self.run_command(['git', 'add', '-A'])
            
            # Commit con mensaje automático
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"Auto sync from {self.hostname} at {timestamp}"
            self.run_command(['git', 'commit', '-m', commit_msg])
            
            # Push
            self.run_command(['git', 'push'])
            
            logger.info("Cambios sincronizados al repositorio Git")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sincronizando a Git: {e}")
            return False

    def sync_from_git(self) -> bool:
        """Sincronizar cambios desde el repositorio Git"""
        try:
            os.chdir(REPO_DIR)
            
            # Stash cambios locales
            self.run_command(['git', 'stash', 'push', '-m', 'autosave'], check=False)
            
            # Pull cambios
            self.run_command(['git', 'pull', '--rebase'])
            
            # Pop stash
            self.run_command(['git', 'stash', 'pop'], check=False)
            
            logger.info("Cambios sincronizados desde Git")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error sincronizando desde Git: {e}")
            return False

    def startup_sync(self) -> bool:
        """Sincronización en inicio de sesión"""
        logger.info("=== INICIO: Sincronización de startup ===")
        
        if not self.has_git_changes():
            logger.info("No hay cambios pendientes, saltando sincronización")
            return True
        
        # Sincronizar desde Git
        if not self.sync_from_git():
            return False
        
        # Detectar y resolver conflictos
        conflicts = self.detect_conflicts()
        if conflicts:
            if not self.reorganize_conflicted_folders(conflicts):
                return False
        
        # Manejar conflictos con archivos existentes
        if not self.handle_existing_files_conflict():
            return False
        
        # Aplicar stow
        packages = ['common']
        if self.hostname in self.config:
            packages.append(self.hostname)
        
        success = self.apply_stow(packages)
        
        if success:
            logger.info("=== FIN: Sincronización de startup completada ===")
        else:
            logger.error("=== FIN: Error en sincronización de startup ===")
        
        return success

    def shutdown_sync(self) -> bool:
        """Sincronización antes de apagado/suspensión"""
        logger.info("=== INICIO: Sincronización de shutdown ===")
        
        # Detectar cambios en archivos gestionados
        has_changes = False
        managed_paths = []
        
        # Recopilar todas las rutas gestionadas
        for section in ['common', self.hostname]:
            if section in self.config:
                for path in self.config[section]:
                    full_path = HOME / path.lstrip('./')
                    managed_paths.append(full_path)
        
        # Verificar si alguna ruta gestionada cambió
        for path in managed_paths:
            if path.exists():
                has_changes = True
                break
        
        if not has_changes:
            logger.info("No hay cambios en archivos gestionados")
            return True
        
        # Sincronizar a Git
        success = self.sync_to_git()
        
        if success:
            logger.info("=== FIN: Sincronización de shutdown completada ===")
        else:
            logger.error("=== FIN: Error en sincronización de shutdown ===")
        
        return success

    def manual_sync(self, force: bool = False) -> bool:
        """Sincronización manual bidireccional"""
        logger.info("=== INICIO: Sincronización manual ===")
        
        # Recargar configuración
        self.config = self.load_config()
        
        # Verificar cambios si no es forzado
        if not force and not self.has_git_changes():
            logger.info("No hay cambios pendientes y no se forzó la sincronización")
            return True
        
        # Sincronizar desde Git primero
        if not self.sync_from_git():
            return False
        
        # Detectar y resolver conflictos
        conflicts = self.detect_conflicts()
        if conflicts:
            if not self.reorganize_conflicted_folders(conflicts):
                return False
        
        # Manejar conflictos con archivos existentes
        if not self.handle_existing_files_conflict():
            return False
        
        # Aplicar stow
        packages = ['common']
        if self.hostname in self.config:
            packages.append(self.hostname)
        
        if not self.apply_stow(packages):
            return False
        
        # Sincronizar cambios locales a Git
        success = self.sync_to_git()
        
        if success:
            logger.info("=== FIN: Sincronización manual completada ===")
        else:
            logger.error("=== FIN: Error en sincronización manual ===")
        
        return success

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Sync-Arch: Sincronización inteligente de dotfiles")
    parser.add_argument('--mode', choices=['startup', 'shutdown', 'manual'], default='manual',
                        help='Modo de sincronización')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Ejecutar en modo simulación (por defecto)')
    parser.add_argument('--force', action='store_true',
                        help='Forzar sincronización sin verificar cambios')
    parser.add_argument('--no-dry-run', action='store_true',
                        help='Desactivar modo dry-run y ejecutar cambios reales')
    parser.add_argument('--force-overwrite', action='store_true',
                        help='Sobrescribir archivos existentes automáticamente')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Activar logging detallado')
    
    args = parser.parse_args()
    
    # Configurar dry-run
    if args.no_dry_run:
        dry_run = False
    else:
        dry_run = args.dry_run
    
    try:
        with SyncLock(LOCK_FILE):
            sync = SyncArch(dry_run=dry_run, verbose=args.verbose, force_overwrite=args.force_overwrite)
            
            if args.mode == 'startup':
                success = sync.startup_sync()
            elif args.mode == 'shutdown':
                success = sync.shutdown_sync()
            else:  # manual
                success = sync.manual_sync(force=args.force)
            
            if not success:
                logger.error("Sincronización falló")
                sys.exit(1)
            
            if dry_run and args.mode == 'manual':
                print("\n" + "="*60)
                print("🔍 MODO DRY-RUN ACTIVADO")
                print("Para ejecutar los cambios reales, usa: --no-dry-run")
                print("="*60)
    
    except Exception as e:
        logger.error(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
