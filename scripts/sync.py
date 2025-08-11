#!/usr/bin/env python3
"""
Sync-Arch: Sistema de sincronización inteligente de dotfiles
Autor: Sergio F.
Versión: 2.0.0 (Modular)

Script principal orquestador del sistema modular.
"""

import sys
import argparse
from pathlib import Path

# Agregar ruta de scripts al path para imports
sys.path.insert(0, str(Path(__file__).parent))

# Imports de módulos core
from core import (
    ConfigManager, IgnoreManager, GitOperations, 
    StowOperations, ConflictResolver, SyncLock, setup_logging
)
from core.utils import HOSTNAME, LOCK_FILE, PROJECT_ROOT

# Imports de comandos
from commands import DiscoverCommand, SyncModes, StatusCommand, CleanupCommand, ValidateCommand

# Rutas globales derivadas
DOTFILES_DIR = PROJECT_ROOT / "dotfiles"
HOME = Path.home()

class SyncArch:
    """Orquestador principal del sistema Sync-Arch"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, force_overwrite: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.force_overwrite = force_overwrite
        
        # Configurar logging
        setup_logging(verbose)
        
        # Inicializar componentes
        self.config_manager = ConfigManager()
        self.ignore_manager = IgnoreManager(self.config_manager, HOSTNAME)
        self.git_ops = GitOperations(PROJECT_ROOT, dry_run)
        self.stow_ops = StowOperations(DOTFILES_DIR, HOME, dry_run)
        self.conflict_resolver = ConflictResolver(
            DOTFILES_DIR, self.config_manager, self.ignore_manager, dry_run
        )
        
        # Inicializar comandos
        self.discover_cmd = DiscoverCommand(self.config_manager, self.ignore_manager, HOME)
        self.sync_modes = SyncModes(
            self.config_manager, self.ignore_manager, self.git_ops, 
            self.stow_ops, self.conflict_resolver, force_overwrite
        )
        self.status_cmd = StatusCommand(self.config_manager, self.ignore_manager, self.git_ops)
        self.cleanup_cmd = CleanupCommand(self.config_manager, self.ignore_manager, DOTFILES_DIR, dry_run)
        self.validate_cmd = ValidateCommand(self.config_manager, self.ignore_manager, DOTFILES_DIR, HOME)
    
    def run_startup(self) -> bool:
        """Ejecutar sincronización de startup"""
        return self.sync_modes.startup_sync()
    
    def run_shutdown(self) -> bool:
        """Ejecutar sincronización de shutdown"""
        return self.sync_modes.shutdown_sync()
    
    def run_manual(self, force: bool = False) -> bool:
        """Ejecutar sincronización manual"""
        return self.sync_modes.manual_sync(force)
    
    def run_discover(self) -> bool:
        """Ejecutar comando discover"""
        self.discover_cmd.interactive_discover()
        return True
    
    def run_status(self) -> bool:
        """Ejecutar comando status"""
        self.status_cmd.show_status()
        return True
    
    def run_cleanup(self) -> bool:
        """Ejecutar comando cleanup"""
        return self.cleanup_cmd.run_cleanup()
    
    def run_validate(self) -> bool:
        """Ejecutar comando validate"""
        return self.validate_cmd.run_validation()

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Sync-Arch: Sincronización inteligente de dotfiles")
    parser.add_argument('--mode', choices=['startup', 'shutdown', 'manual', 'discover', 'status', 'cleanup', 'validate'], 
                        default='manual', help='Modo de operación')
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
    dry_run = not args.no_dry_run if args.no_dry_run else args.dry_run
    
    try:
        with SyncLock(LOCK_FILE):
            sync = SyncArch(
                dry_run=dry_run, 
                verbose=args.verbose, 
                force_overwrite=args.force_overwrite
            )
            
            # Ejecutar comando según modo
            if args.mode == 'startup':
                success = sync.run_startup()
            elif args.mode == 'shutdown':
                success = sync.run_shutdown()
            elif args.mode == 'manual':
                success = sync.run_manual(force=args.force)
            elif args.mode == 'discover':
                success = sync.run_discover()
            elif args.mode == 'status':
                success = sync.run_status()
            elif args.mode == 'cleanup':
                success = sync.run_cleanup()
            elif args.mode == 'validate':
                success = sync.run_validate()
            else:
                print(f"❌ Modo desconocido: {args.mode}")
                sys.exit(1)
            
            if not success:
                print("❌ La operación falló")
                sys.exit(1)
            
            if dry_run and args.mode in ['startup', 'shutdown', 'manual']:
                print("\n" + "="*60)
                print("🔍 MODO DRY-RUN ACTIVADO")
                print("Para ejecutar los cambios reales, usa: --no-dry-run")
                print("="*60)
                
    except KeyboardInterrupt:
        print("\n❌ Operación interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
