"""
Sync-Arch Git Operations

Operaciones Git para sincronización de dotfiles.
"""

import logging
from datetime import datetime
from pathlib import Path
from .utils import run_command

logger = logging.getLogger(__name__)

class GitOperations:
    """Operaciones Git para sincronización"""
    
    def __init__(self, repo_dir: Path, dry_run: bool = False):
        self.repo_dir = repo_dir
        self.dry_run = dry_run
    
    def has_local_changes(self) -> bool:
        """Verificar si hay cambios locales pendientes"""
        try:
            result = run_command(['git', 'status', '--porcelain'], cwd=self.repo_dir, dry_run=False)
            has_changes = bool(result.stdout.strip())
            logger.debug(f"Cambios locales detectados: {has_changes}")
            return has_changes
        except Exception as e:
            logger.error(f"Error verificando cambios locales: {e}")
            return False
    
    def has_remote_changes(self) -> bool:
        """Verificar si hay cambios remotos pendientes"""
        try:
            # Fetch para actualizar referencias remotas
            run_command(['git', 'fetch'], cwd=self.repo_dir, dry_run=False)
            
            # Contar commits pendientes desde remoto
            result = run_command(['git', 'rev-list', '--count', 'HEAD..origin/main'], 
                                cwd=self.repo_dir, dry_run=False)
            remote_commits = int(result.stdout.strip() or 0)
            has_remote = remote_commits > 0
            
            logger.debug(f"Cambios remotos detectados: {has_remote} ({remote_commits} commits)")
            return has_remote
        except Exception as e:
            logger.error(f"Error verificando cambios remotos: {e}")
            return False
    
    def sync_from_git(self) -> bool:
        """Sincronizar cambios desde Git (pull)"""
        try:
            logger.info("Sincronizando cambios desde Git...")
            
            local_changes = self.has_local_changes()
            remote_changes = self.has_remote_changes()
            
            logger.debug(f"Cambios locales: {local_changes}, cambios remotos: {remote_changes}")
            
            if not local_changes and not remote_changes:
                logger.info("No hay cambios para sincronizar")
                return True
            
            # Si hay cambios locales, hacer stash
            if local_changes:
                run_command(['git', 'stash', 'push', '-m', 'autosave'], 
                           cwd=self.repo_dir, dry_run=self.dry_run)
                logger.debug("Cambios locales guardados en stash")
            
            # Pull con rebase
            run_command(['git', 'pull', '--rebase'], 
                       cwd=self.repo_dir, dry_run=self.dry_run)
            logger.debug("Pull con rebase completado")
            
            # Restaurar stash si había cambios locales
            if local_changes:
                run_command(['git', 'stash', 'pop'], 
                           cwd=self.repo_dir, check=False, dry_run=self.dry_run)
                logger.debug("Stash restaurado")
            
            logger.info("Cambios sincronizados desde Git")
            return True
            
        except Exception as e:
            logger.error(f"Error sincronizando desde Git: {e}")
            return False
    
    def sync_to_git(self, message: str = None) -> bool:
        """Sincronizar cambios hacia Git (commit + push)"""
        try:
            if not self.has_local_changes():
                logger.info("No hay cambios locales para sincronizar")
                return True
            
            logger.info("Sincronizando cambios hacia Git...")
            
            # Agregar todos los cambios
            run_command(['git', 'add', '-A'], cwd=self.repo_dir, dry_run=self.dry_run)
            
            # Crear mensaje de commit
            if not message:
                hostname = run_command(['uname', '-n'], dry_run=False).stdout.strip()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"Auto sync from {hostname} at {timestamp}"
            
            # Commit
            run_command(['git', 'commit', '-m', message], 
                       cwd=self.repo_dir, dry_run=self.dry_run)
            
            # Push
            run_command(['git', 'push'], cwd=self.repo_dir, dry_run=self.dry_run)
            
            logger.info("Cambios sincronizados al repositorio Git")
            return True
            
        except Exception as e:
            logger.error(f"Error sincronizando hacia Git: {e}")
            return False
    
    def get_status(self) -> dict:
        """Obtener estado del repositorio Git"""
        try:
            # Estado general
            status_result = run_command(['git', 'status', '--porcelain'], 
                                      cwd=self.repo_dir, dry_run=False)
            
            # Información de branch
            branch_result = run_command(['git', 'branch', '--show-current'], 
                                      cwd=self.repo_dir, dry_run=False)
            
            # Último commit
            commit_result = run_command(['git', 'log', '-1', '--oneline'], 
                                      cwd=self.repo_dir, dry_run=False)
            
            return {
                'has_changes': bool(status_result.stdout.strip()),
                'branch': branch_result.stdout.strip(),
                'last_commit': commit_result.stdout.strip(),
                'status_output': status_result.stdout
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado Git: {e}")
            return {
                'has_changes': False,
                'branch': 'unknown',
                'last_commit': 'unknown',
                'status_output': '',
                'error': str(e)
            }
