"""
Sync-Arch Validate Command

Comando para detectar inconsistencias cuando archivos están en config.json
pero no están correctamente sincronizados o versionados.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set

logger = logging.getLogger(__name__)

class ValidateCommand:
    """Comando de validación de sincronización"""
    
    def __init__(self, config_manager, ignore_manager, dotfiles_dir: Path, home_dir: Path, dry_run: bool = True):
        self.config = config_manager
        self.ignore = ignore_manager
        self.dotfiles_dir = dotfiles_dir
        self.home_dir = home_dir
        self.hostname = ignore_manager.hostname
        self.dry_run = dry_run
        
        # Importar PathUtils del core
        from core.path_utils import PathUtils
        self.path_utils = PathUtils(config_manager, dotfiles_dir, home_dir, self.hostname)
    
    def scan_missing_items(self) -> Dict[str, List[Dict]]:
        """Escanear elementos en config.json que no están correctamente sincronizados"""
        issues = {
            'missing_in_repo': [],      # En config pero no en repo
            'missing_symlinks': [],     # En repo pero sin symlink
            'missing_everywhere': [],   # En config pero no existe en ningún lado
            'orphaned_config': []       # En config pero ignorado (no debería estar)
        }
        
        # Obtener todas las rutas gestionadas
        managed_paths = self.get_all_managed_paths()
        
        for key, path_info in managed_paths.items():
            path = path_info['path']
            normalized_path = path_info['normalized']
            source = path_info['source']
            
            # Verificar si está en ignore (no debería estar en config)
            if self.ignore.should_ignore_path(normalized_path):
                # Solo reportar si no está explícitamente incluido en hostname
                if not self.ignore.is_explicitly_included(normalized_path):
                    issues['orphaned_config'].append({
                        'path': path,
                        'source': source,
                        'reason': f'Coincide con patrón ignore pero está en {source}'
                    })
                    continue
            
            # Verificar existencia en repo
            repo_path = self.get_repo_path(source, normalized_path)
            repo_exists = repo_path.exists()
            
            # Verificar existencia en $HOME
            home_path = self.home_dir / normalized_path
            home_exists = home_path.exists()
            
            # Verificar si es symlink correcto
            is_correct_symlink = (home_exists and 
                                home_path.is_symlink() and 
                                home_path.resolve() == repo_path.resolve())
            
            # Clasificar el problema
            if not repo_exists and not home_exists:
                # No existe en ningún lado
                issues['missing_everywhere'].append({
                    'path': path,
                    'source': source,
                    'reason': 'Especificado en config pero no existe'
                })
            elif not repo_exists and home_exists:
                # Existe en HOME pero no en repo
                issues['missing_in_repo'].append({
                    'path': path,
                    'source': source,
                    'home_path': str(home_path),
                    'repo_path': str(repo_path),
                    'reason': 'Existe en $HOME pero no está versionado'
                })
            elif repo_exists and not is_correct_symlink:
                # Existe en repo pero sin symlink correcto
                if home_exists and not home_path.is_symlink():
                    reason = 'Archivo real en $HOME, necesita ser reemplazado por symlink'
                elif home_exists and home_path.is_symlink():
                    reason = 'Symlink incorrecto en $HOME'
                else:
                    reason = 'Versionado pero no desplegado en $HOME'
                
                issues['missing_symlinks'].append({
                    'path': path,
                    'source': source,
                    'home_path': str(home_path),
                    'repo_path': str(repo_path),
                    'home_exists': home_exists,
                    'is_symlink': home_path.is_symlink() if home_exists else False,
                    'reason': reason
                })
        
        return issues
    
    def get_all_managed_paths(self) -> Dict[str, Dict]:
        """Obtener todas las rutas gestionadas desde config.json"""
        managed_paths = {}
        
        # Usar la función centralizada de path_utils
        paths_list = self.path_utils.get_managed_paths(include_system_configs=False)
        
        # Convertir a formato de dict con keys únicos para compatibilidad
        for path_info in paths_list:
            key = f"{path_info['source']}:{path_info['path']}"
            managed_paths[key] = path_info
            
        return managed_paths
    
    def get_repo_path(self, source: str, normalized_path: str) -> Path:
        """Obtener la ruta en el repositorio para un archivo"""
        return self.path_utils.get_repo_path(source, normalized_path)
    
    def show_validation_report(self, issues: Dict[str, List[Dict]]) -> None:
        """Mostrar reporte de validación"""
        total_issues = sum(len(issue_list) for issue_list in issues.values())
        
        if total_issues == 0:
            print("✅ Validación completa: todos los elementos en config.json están correctamente sincronizados")
            return
        
        print(f"🔍 REPORTE DE VALIDACIÓN - {total_issues} problemas encontrados")
        print("=" * 60)
        print()
        
        # Elementos faltantes en repositorio
        if issues['missing_in_repo']:
            print("📁 ARCHIVOS FALTANTES EN REPOSITORIO")
            print("   → Existen en $HOME pero no están versionados")
            print()
            for item in issues['missing_in_repo']:
                print(f"   • {item['path']} ({item['source']})")
                print(f"     $HOME: {item['home_path']} ✅")
                print(f"     Repo:  {item['repo_path']} ❌")
                print(f"     💡 Solución: Agregar al repositorio")
                print()
        
        # Symlinks faltantes
        if issues['missing_symlinks']:
            print("🔗 SYMLINKS FALTANTES O INCORRECTOS")
            print("   → Versionados pero no desplegados correctamente")
            print()
            for item in issues['missing_symlinks']:
                print(f"   • {item['path']} ({item['source']})")
                print(f"     $HOME: {item['home_path']} {'✅' if item['home_exists'] else '❌'}")
                print(f"     Repo:  {item['repo_path']} ✅")
                if item['home_exists']:
                    print(f"     Tipo:  {'Symlink' if item['is_symlink'] else 'Archivo real'}")
                print(f"     💡 Solución: {item['reason']}")
                print()
        
        # Elementos que no existen en ningún lado
        if issues['missing_everywhere']:
            print("❓ ENTRADAS OBSOLETAS EN CONFIG")
            print("   → Especificadas pero no existen")
            print()
            for item in issues['missing_everywhere']:
                print(f"   • {item['path']} ({item['source']})")
                print(f"     💡 Solución: Remover de config.json o crear el archivo")
                print()
        
        # Configuraciones huérfanas (en ignore)
        if issues['orphaned_config']:
            print("⚠️  CONFIGURACIONES CONFLICTIVAS")
            print("   → En config pero coinciden con patrones ignore")
            print()
            for item in issues['orphaned_config']:
                print(f"   • {item['path']} ({item['source']})")
                print(f"     💡 {item['reason']}")
                print()
    
    def suggest_fixes(self, issues: Dict[str, List[Dict]]) -> None:
        """Sugerir comandos para arreglar los problemas"""
        if not any(issues.values()):
            return
        
        print("🛠️  COMANDOS SUGERIDOS PARA CORREGIR")
        print("=" * 40)
        print()
        
        # Para archivos faltantes en repo
        if issues['missing_in_repo']:
            print("📁 Agregar archivos al repositorio:")
            for item in issues['missing_in_repo']:
                repo_dir = Path(item['repo_path']).parent
                print(f"   mkdir -p {repo_dir}")
                print(f"   cp -r {item['home_path']} {item['repo_path']}")
            print()
        
        # Para symlinks faltantes
        if issues['missing_symlinks']:
            print("🔗 Crear/corregir symlinks:")
            print("   # Usar GNU Stow para desplegar:")
            print("   cd dotfiles")
            print("   stow common")
            print(f"   stow {self.hostname}")
            print()
        
        # Para entradas obsoletas
        if issues['missing_everywhere']:
            print("❓ Limpiar config.json:")
            print("   # Remover estas entradas de config.json:")
            for item in issues['missing_everywhere']:
                print(f"   # - {item['path']} (de {item['source']})")
            print()
        
        # Para configuraciones conflictivas
        if issues['orphaned_config']:
            print("⚠️  Resolver conflictos ignore:")
            print("   # Opciones:")
            print("   # 1. Remover de config.json si no debe sincronizarse")
            print("   # 2. Ajustar patrones ignore si debe sincronizarse")
            print()
    
    def run_validation(self) -> bool:
        """Ejecutar validación completa"""
        dry_status = " [DRY-RUN]" if self.dry_run else ""
        print(f"🔍 Iniciando validación de sincronización...{dry_status}")
        print("🔍 Verificando consistencia entre config.json, repositorio y $HOME...")
        print()
        
        issues = self.scan_missing_items()
        self.show_validation_report(issues)
        
        if any(issues.values()):
            print()
            self.suggest_fixes(issues)
            return False
        
        return True
