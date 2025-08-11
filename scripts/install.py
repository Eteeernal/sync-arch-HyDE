#!/usr/bin/env python3
"""
Sync-Arch Installer
Autor: Sergio F.
Versión: 1.0.0

Script de instalación automática para el sistema de sincronización de dotfiles.
Configura dependencias, servicios systemd, estructura inicial y primera sincronización.
"""

import os
import subprocess
import sys
import json
import shutil
import socket
from pathlib import Path
from typing import Optional, List
import tempfile

# === CONFIGURACIÓN ===
HOME = Path.home()
REPO_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_DIR / "scripts"
SYSTEMD_DIR = REPO_DIR / "systemd"
SYSTEMD_USER_DIR = HOME / ".config/systemd/user"
HOSTNAME = socket.gethostname()

# Colores para output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def log(message: str, color: str = Colors.BLUE):
    """Imprimir mensaje con color"""
    print(f"{color}🔧 {message}{Colors.NC}")

def success(message: str):
    """Imprimir mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")

def warning(message: str):
    """Imprimir mensaje de advertencia"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")

def error(message: str):
    """Imprimir mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.NC}")

def info(message: str):
    """Imprimir mensaje informativo"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.NC}")

def run_command(cmd: List[str], check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
    """Ejecutar comando con manejo de errores"""
    cmd_str = ' '.join(str(c) for c in cmd)
    log(f"Ejecutando: {cmd_str}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=capture_output, text=True)
        return result
    except subprocess.CalledProcessError as e:
        error(f"Error ejecutando: {cmd_str}")
        if capture_output and e.stderr:
            error(f"stderr: {e.stderr}")
        if check:
            raise
        return e

def check_arch_linux() -> bool:
    """Verificar si estamos en Arch Linux"""
    try:
        with open('/etc/os-release', 'r') as f:
            content = f.read()
            return 'ID=arch' in content
    except FileNotFoundError:
        return False

def check_dependencies() -> bool:
    """Verificar y instalar dependencias"""
    log("Verificando dependencias del sistema...")
    
    required_packages = ['git', 'python', 'stow']
    missing_packages = []
    
    for package in required_packages:
        if not shutil.which(package):
            missing_packages.append(package)
    
    if missing_packages:
        warning(f"Paquetes faltantes: {', '.join(missing_packages)}")
        
        if check_arch_linux():
            log("Instalando paquetes con pacman...")
            try:
                run_command(['sudo', 'pacman', '-Sy', '--noconfirm'] + missing_packages)
                success("Dependencias instaladas correctamente")
            except subprocess.CalledProcessError:
                error("Error instalando dependencias con pacman")
                return False
        else:
            error("Sistema no es Arch Linux. Instala manualmente:")
            error(f"Paquetes requeridos: {', '.join(missing_packages)}")
            return False
    else:
        success("Todas las dependencias están instaladas")
    
    return True

def setup_git_repo() -> bool:
    """Configurar repositorio Git si es necesario"""
    log("Configurando repositorio Git...")
    
    os.chdir(REPO_DIR)
    
    # Verificar si ya es un repositorio Git
    if not (REPO_DIR / '.git').exists():
        warning("Directorio no es un repositorio Git")
        
        response = input("¿Deseas inicializar un nuevo repositorio Git? (y/N): ")
        if response.lower() in ['y', 'yes', 'sí', 's']:
            try:
                run_command(['git', 'init'])
                run_command(['git', 'add', '.'])
                run_command(['git', 'commit', '-m', 'Initial commit: Sync-Arch setup'])
                success("Repositorio Git inicializado")
            except subprocess.CalledProcessError:
                error("Error inicializando repositorio Git")
                return False
        else:
            warning("Continuando sin repositorio Git (funcionalidad limitada)")
            return True
    
    # Configurar usuario Git si no está configurado
    try:
        result = run_command(['git', 'config', 'user.name'], capture_output=True, check=False)
        if not result.stdout.strip():
            name = input("Ingresa tu nombre para Git: ")
            run_command(['git', 'config', 'user.name', name])
        
        result = run_command(['git', 'config', 'user.email'], capture_output=True, check=False)
        if not result.stdout.strip():
            email = input("Ingresa tu email para Git: ")
            run_command(['git', 'config', 'user.email', email])
        
        success("Configuración Git verificada")
    except subprocess.CalledProcessError:
        warning("Error configurando Git, pero continuando...")
    
    return True

def setup_systemd_services() -> bool:
    """Configurar servicios systemd user"""
    log("Configurando servicios systemd user...")
    
    # Crear directorio systemd user si no existe
    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    
    # Crear servicios
    startup_service = f"""[Unit]
Description=Sync-Arch dotfiles synchronization on startup
After=graphical-session.target

[Service]
Type=oneshot
ExecStart={SCRIPTS_DIR}/sync.sh startup --no-dry-run
Environment=HOME={HOME}
Environment=USER={os.getenv('USER', 'unknown')}

[Install]
WantedBy=default.target
"""

    shutdown_service = f"""[Unit]
Description=Sync-Arch dotfiles synchronization on shutdown
Before=shutdown.target sleep.target suspend.target hibernate.target hybrid-sleep.target
DefaultDependencies=no

[Service]
Type=oneshot
ExecStart={SCRIPTS_DIR}/sync.sh shutdown --no-dry-run
TimeoutSec=60
Environment=HOME={HOME}
Environment=USER={os.getenv('USER', 'unknown')}

[Install]
WantedBy=halt.target reboot.target shutdown.target sleep.target suspend.target hibernate.target hybrid-sleep.target
"""

    # Escribir archivos de servicio
    try:
        (SYSTEMD_USER_DIR / "sync-arch-startup.service").write_text(startup_service)
        (SYSTEMD_USER_DIR / "sync-arch-shutdown.service").write_text(shutdown_service)
        
        # Recargar systemd
        run_command(['systemctl', '--user', 'daemon-reload'])
        
        # Habilitar servicios
        run_command(['systemctl', '--user', 'enable', 'sync-arch-startup.service'])
        run_command(['systemctl', '--user', 'enable', 'sync-arch-shutdown.service'])
        
        success("Servicios systemd configurados y habilitados")
        
        # Información adicional
        info("Servicios systemd user creados:")
        info(f"  • sync-arch-startup.service  (inicio de sesión)")
        info(f"  • sync-arch-shutdown.service (apagado/suspensión)")
        info(f"  • Ubicación: {SYSTEMD_USER_DIR}")
        
    except subprocess.CalledProcessError as e:
        error("Error configurando servicios systemd")
        error(str(e))
        return False
    
    return True

def create_initial_dotfiles_structure() -> bool:
    """Crear estructura inicial de dotfiles si no existe"""
    log("Creando estructura inicial de dotfiles...")
    
    dotfiles_dir = REPO_DIR / "dotfiles"
    common_dir = dotfiles_dir / "common"
    hostname_dir = dotfiles_dir / HOSTNAME
    
    # Crear directorios
    common_dir.mkdir(parents=True, exist_ok=True)
    hostname_dir.mkdir(parents=True, exist_ok=True)
    
    # Crear archivos de ejemplo si no existen
    readme_common = common_dir / "README.md"
    if not readme_common.exists():
        readme_common.write_text(f"""# Configuración común

Archivos y carpetas que se aplican a todos los equipos.

Creado automáticamente por Sync-Arch el {subprocess.getoutput('date')}.
""")
    
    readme_hostname = hostname_dir / "README.md"
    if not readme_hostname.exists():
        readme_hostname.write_text(f"""# Configuración específica para {HOSTNAME}

Archivos y carpetas específicos para este equipo.

Creado automáticamente por Sync-Arch el {subprocess.getoutput('date')}.
""")
    
    success(f"Estructura de dotfiles creada (common + {HOSTNAME})")
    return True

def copy_existing_dotfiles() -> bool:
    """Copiar dotfiles existentes del usuario al repositorio"""
    log("Analizando dotfiles existentes...")
    
    # Cargar configuración
    config_file = REPO_DIR / "config.json"
    if not config_file.exists():
        warning("Archivo config.json no encontrado, saltando copia de dotfiles")
        return True
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        error(f"Error leyendo config.json: {e}")
        return False
    
    # Obtener rutas a copiar
    common_paths = config.get('common', [])
    hostname_paths = config.get(HOSTNAME, [])
    
    dotfiles_dir = REPO_DIR / "dotfiles"
    copied_files = 0
    
    # Copiar archivos comunes
    for path in common_paths:
        source = HOME / path.lstrip('./')
        dest = dotfiles_dir / "common" / path.lstrip('./')
        
        if source.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                if source.is_dir():
                    shutil.copytree(source, dest)
                    log(f"Carpeta copiada: {source} → common/")
                else:
                    shutil.copy2(source, dest)
                    log(f"Archivo copiado: {source} → common/")
                copied_files += 1
            except (shutil.Error, OSError) as e:
                warning(f"Error copiando {source}: {e}")
    
    # Copiar archivos específicos del hostname
    for path in hostname_paths:
        source = HOME / path.lstrip('./')
        dest = dotfiles_dir / HOSTNAME / path.lstrip('./')
        
        if source.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                if source.is_dir():
                    shutil.copytree(source, dest)
                    log(f"Carpeta copiada: {source} → {HOSTNAME}/")
                else:
                    shutil.copy2(source, dest)
                    log(f"Archivo copiado: {source} → {HOSTNAME}/")
                copied_files += 1
            except (shutil.Error, OSError) as e:
                warning(f"Error copiando {source}: {e}")
    
    if copied_files > 0:
        success(f"Se copiaron {copied_files} archivos/carpetas al repositorio")
    else:
        info("No se encontraron dotfiles nuevos para copiar")
    
    return True

def run_initial_sync() -> bool:
    """Ejecutar primera sincronización"""
    log("¿Deseas ejecutar una sincronización inicial?")
    info("Esto aplicará los dotfiles del repositorio a tu sistema")
    
    response = input("¿Continuar con la sincronización? (Y/n): ")
    if response.lower() in ['n', 'no']:
        info("Sincronización inicial omitida")
        return True
    
    # Primero mostrar lo que se haría (dry-run)
    log("Ejecutando dry-run para mostrar cambios...")
    try:
        sync_script = SCRIPTS_DIR / "sync.sh"
        result = run_command([str(sync_script), 'manual', '--dry-run', '--verbose'], 
                           capture_output=True, check=False)
        
        if result.returncode == 0:
            print(result.stdout)
            
            response = input("\n¿Aplicar estos cambios? (Y/n): ")
            if response.lower() not in ['n', 'no']:
                log("Ejecutando sincronización real...")
                result = run_command([str(sync_script), 'manual', '--no-dry-run'])
                
                if result.returncode == 0:
                    success("Sincronización inicial completada exitosamente")
                    return True
                else:
                    error("Error en la sincronización inicial")
                    return False
            else:
                info("Sincronización inicial cancelada por el usuario")
                return True
        else:
            error("Error en dry-run de sincronización")
            if result.stderr:
                error(result.stderr)
            return False
            
    except subprocess.CalledProcessError as e:
        error(f"Error ejecutando sincronización: {e}")
        return False

def show_post_install_info():
    """Mostrar información post-instalación"""
    print(f"\n{Colors.GREEN}{'='*60}")
    print("🎉 INSTALACIÓN COMPLETADA")
    print(f"{'='*60}{Colors.NC}")
    
    print(f"\n{Colors.WHITE}📍 INFORMACIÓN DEL SISTEMA:{Colors.NC}")
    print(f"  • Hostname: {Colors.CYAN}{HOSTNAME}{Colors.NC}")
    print(f"  • Repositorio: {Colors.CYAN}{REPO_DIR}{Colors.NC}")
    print(f"  • Dotfiles: {Colors.CYAN}{REPO_DIR}/dotfiles/{Colors.NC}")
    print(f"  • Logs: {Colors.CYAN}{HOME}/.local/state/sync-arch/{Colors.NC}")
    
    print(f"\n{Colors.WHITE}🚀 COMANDOS DISPONIBLES:{Colors.NC}")
    print(f"  • {Colors.GREEN}./scripts/sync.sh{Colors.NC}           - Sincronización manual")
    print(f"  • {Colors.GREEN}./scripts/sync.sh status{Colors.NC}    - Ver estado del repositorio")
    print(f"  • {Colors.GREEN}./scripts/sync.sh --no-dry-run{Colors.NC} - Sincronización real")
    print(f"  • {Colors.GREEN}./scripts/sync.sh help{Colors.NC}      - Ayuda detallada")
    
    print(f"\n{Colors.WHITE}⚙️  SERVICIOS SYSTEMD:{Colors.NC}")
    print(f"  • {Colors.BLUE}sync-arch-startup.service{Colors.NC}  - Sincronización al iniciar sesión")
    print(f"  • {Colors.BLUE}sync-arch-shutdown.service{Colors.NC} - Sincronización al apagar/suspender")
    
    print(f"\n{Colors.WHITE}📁 ESTRUCTURA DE DOTFILES:{Colors.NC}")
    print(f"  • {Colors.CYAN}dotfiles/common/{Colors.NC}     - Configuración compartida")
    print(f"  • {Colors.CYAN}dotfiles/{HOSTNAME}/{Colors.NC} - Configuración específica de este equipo")
    
    print(f"\n{Colors.WHITE}📝 PRÓXIMOS PASOS:{Colors.NC}")
    print("  1. Edita config.json para agregar/quitar dotfiles")
    print("  2. Ejecuta ./scripts/sync.sh para probar la sincronización")
    print("  3. Configura un repositorio Git remoto si deseas sincronización entre equipos")
    print("  4. Los servicios systemd se ejecutarán automáticamente en el próximo inicio/apagado")
    
    print(f"\n{Colors.WHITE}🔗 CONFIGURACIÓN GIT REMOTO (OPCIONAL):{Colors.NC}")
    print("  git remote add origin <tu-repositorio-git-privado>")
    print("  git push -u origin main")
    
    print(f"\n{Colors.YELLOW}⚠️  IMPORTANTE:{Colors.NC}")
    print("  • Por defecto, sync.sh ejecuta en modo dry-run (simulación)")
    print("  • Usa --no-dry-run para aplicar cambios reales")
    print("  • Revisa los logs en ~/.local/state/sync-arch/sync.log")

def main():
    """Función principal del instalador"""
    print(f"{Colors.PURPLE}")
    print("╔════════════════════════════════════════════════════════╗")
    print("║                    SYNC-ARCH INSTALLER                ║")
    print("║            Sistema de sincronización de dotfiles      ║")
    print("╚════════════════════════════════════════════════════════╝")
    print(f"{Colors.NC}")
    
    info(f"Instalando para hostname: {HOSTNAME}")
    info(f"Directorio del proyecto: {REPO_DIR}")
    
    try:
        # Paso 1: Verificar dependencias
        if not check_dependencies():
            error("Error verificando dependencias")
            sys.exit(1)
        
        # Paso 2: Configurar Git
        if not setup_git_repo():
            error("Error configurando repositorio Git")
            sys.exit(1)
        
        # Paso 3: Crear estructura de dotfiles
        if not create_initial_dotfiles_structure():
            error("Error creando estructura de dotfiles")
            sys.exit(1)
        
        # Paso 4: Copiar dotfiles existentes
        if not copy_existing_dotfiles():
            error("Error copiando dotfiles existentes")
            sys.exit(1)
        
        # Paso 5: Configurar servicios systemd
        if not setup_systemd_services():
            error("Error configurando servicios systemd")
            sys.exit(1)
        
        # Paso 6: Sincronización inicial (opcional)
        if not run_initial_sync():
            error("Error en sincronización inicial")
            sys.exit(1)
        
        # Paso 7: Mostrar información final
        show_post_install_info()
        
    except KeyboardInterrupt:
        error("\nInstalación cancelada por el usuario")
        sys.exit(130)
    except Exception as e:
        error(f"Error crítico durante la instalación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
