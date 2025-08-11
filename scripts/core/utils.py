"""
Sync-Arch Utilities

Utilidades comunes para el sistema.
"""

import os
import sys
import logging
import socket
import fcntl
import subprocess
from pathlib import Path
from typing import List, Optional

# Configuración global
HOSTNAME = socket.gethostname()
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOCK_FILE = f"/tmp/sync-arch-{os.getenv('USER', 'unknown')}.lock"
LOG_DIR = Path.home() / ".local/state/sync-arch"
LOG_FILE = LOG_DIR / "sync.log"

def setup_logging(verbose: bool = False) -> None:
    """Configurar sistema de logging"""
    # Crear directorio de logs si no existe
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Configurar nivel de logging
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configurar formato
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

class SyncLock:
    """Gestor de lock para prevenir ejecuciones concurrentes"""
    
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.lock_fd = None
    
    def __enter__(self):
        """Adquirir lock"""
        try:
            self.lock_fd = os.open(self.lock_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Escribir PID en el archivo de lock
            os.write(self.lock_fd, f"{os.getpid()}\n".encode())
            
            logging.debug(f"Lock adquirido: {self.lock_file}")
            return self
        except (OSError, IOError) as e:
            if self.lock_fd:
                os.close(self.lock_fd)
            logging.error(f"No se pudo adquirir lock: {e}")
            logging.error("Otra instancia de sync-arch está ejecutándose")
            sys.exit(1)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Liberar lock"""
        if self.lock_fd:
            try:
                os.close(self.lock_fd)
                os.unlink(self.lock_file)
                logging.debug(f"Lock liberado: {self.lock_file}")
            except OSError:
                pass

def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True, dry_run: bool = False) -> subprocess.CompletedProcess:
    """Ejecutar comando con logging"""
    cmd_str = ' '.join(str(c) for c in cmd)
    logging.debug(f"Ejecutando: {cmd_str} (cwd: {cwd})")
    
    if dry_run and any(dangerous in cmd_str for dangerous in ['stow', 'git commit', 'git push', 'cp', 'mv', 'rm']):
        logging.info(f"[DRY-RUN] Simulando: {cmd_str}")
        return subprocess.CompletedProcess(cmd, 0, b"", b"")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)
        
        if result.stdout:
            logging.debug(f"stdout: {result.stdout.strip()}")
        if result.stderr:
            logging.debug(f"stderr: {result.stderr.strip()}")
            
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Error ejecutando comando: {cmd_str}")
        logging.error(f"Código de salida: {e.returncode}")
        if e.stdout:
            logging.error(f"stdout: {e.stdout.strip()}")
        if e.stderr:
            logging.error(f"stderr: {e.stderr.strip()}")
        raise
