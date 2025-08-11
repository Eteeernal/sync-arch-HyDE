#!/usr/bin/env bash

# install-cli.sh - Instalador del comando global sync-arch
# Instala el comando CLI global para sync-arch

set -euo pipefail

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly CLI_SOURCE="$SCRIPT_DIR/sync-arch"
readonly CLI_TARGET="/usr/local/bin/sync-arch"
readonly COMPLETION_DIR="/usr/local/share/bash-completion/completions"
readonly ZSH_COMPLETION_DIR="/usr/local/share/zsh/site-functions"

# Colores
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# ============================================================================
# FUNCIONES
# ============================================================================

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

check_requirements() {
    info "Verificando requisitos..."
    
    # Verificar que el script CLI existe
    if [[ ! -f "$CLI_SOURCE" ]]; then
        error "Script CLI no encontrado: $CLI_SOURCE"
        exit 1
    fi
    
    # Verificar que el directorio target existe
    if [[ ! -d "$(dirname "$CLI_TARGET")" ]]; then
        error "Directorio target no existe: $(dirname "$CLI_TARGET")"
        echo "Solución: sudo mkdir -p $(dirname "$CLI_TARGET")"
        exit 1
    fi
    
    # Verificar permisos de escritura (será manejado por sudo)
    if [[ ! -w "$(dirname "$CLI_TARGET")" && $EUID -ne 0 ]]; then
        warning "Se requieren permisos de administrador para instalar en $CLI_TARGET"
    fi
    
    success "Requisitos verificados"
}

install_cli_command() {
    info "Instalando comando CLI global..."
    
    # Copiar el script
    if [[ $EUID -eq 0 ]]; then
        cp "$CLI_SOURCE" "$CLI_TARGET"
        chmod +x "$CLI_TARGET"
    else
        sudo cp "$CLI_SOURCE" "$CLI_TARGET"
        sudo chmod +x "$CLI_TARGET"
    fi
    
    success "Comando instalado en: $CLI_TARGET"
}

create_bash_completion() {
    info "Creando completado para Bash..."
    
    local completion_content='# sync-arch bash completion
_sync_arch() {
    local cur prev words cword
    _init_completion || return

    local commands="startup shutdown manual discover cleanup validate deploy rollback list-backups status version help"
    local options="--dry-run --no-dry-run --force --force-overwrite --verbose --quiet -v -q -h --help --version"

    case $prev in
        rollback)
            # Completar con nombres de backups disponibles
            local backups
            if command -v sync-arch >/dev/null 2>&1; then
                backups=$(sync-arch list-backups 2>/dev/null | grep "backup_" | awk "{print \$2}" || true)
                COMPREPLY=($(compgen -W "$backups" -- "$cur"))
            fi
            return
            ;;
    esac

    if [[ $cur == -* ]]; then
        COMPREPLY=($(compgen -W "$options" -- "$cur"))
    else
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
    fi
}

complete -F _sync_arch sync-arch'

    if [[ $EUID -eq 0 ]]; then
        mkdir -p "$COMPLETION_DIR"
        echo "$completion_content" > "$COMPLETION_DIR/sync-arch"
    else
        sudo mkdir -p "$COMPLETION_DIR"
        echo "$completion_content" | sudo tee "$COMPLETION_DIR/sync-arch" > /dev/null
    fi
    
    success "Completado para Bash instalado"
}

create_zsh_completion() {
    info "Creando completado para Zsh..."
    
    local zsh_completion_content='#compdef sync-arch

local commands=(
    "startup:Sincronización en inicio de sesión"
    "shutdown:Sincronización antes de apagado/suspensión"
    "manual:Sincronización manual (por defecto)"
    "discover:Descubrir y gestionar archivos no sincronizados"
    "cleanup:Limpiar archivos ignorados del repositorio"
    "validate:Validar consistencia config.json vs repo vs \$HOME"
    "deploy:Desplegar symlinks con backup automático"
    "rollback:Restaurar desde backup"
    "list-backups:Listar backups disponibles"
    "status:Mostrar estado del repositorio"
    "version:Mostrar versión"
    "help:Mostrar ayuda"
)

local options=(
    "--dry-run[Ejecutar en modo simulación]"
    "--no-dry-run[Ejecutar cambios reales]"
    "--force[Forzar sincronización sin verificar cambios]"
    "--force-overwrite[Sobrescribir archivos existentes automáticamente]"
    "--verbose[Activar logging detallado]"
    "--quiet[Modo silencioso]"
    "-v[Activar logging detallado]"
    "-q[Modo silencioso]"
    "--help[Mostrar ayuda]"
    "--version[Mostrar versión]"
)

_arguments -C \
    "1: :((${commands[@]}))" \
    "*: :((${options[@]}))" \
    && return 0

case $words[1] in
    rollback)
        _arguments \
            "2: :($(sync-arch list-backups 2>/dev/null | grep \"backup_\" | awk \"{print \\\$2}\" || true))"
        ;;
esac'

    if [[ $EUID -eq 0 ]]; then
        mkdir -p "$ZSH_COMPLETION_DIR"
        echo "$zsh_completion_content" > "$ZSH_COMPLETION_DIR/_sync-arch"
    else
        sudo mkdir -p "$ZSH_COMPLETION_DIR"
        echo "$zsh_completion_content" | sudo tee "$ZSH_COMPLETION_DIR/_sync-arch" > /dev/null
    fi
    
    success "Completado para Zsh instalado"
}

update_sync_arch_home() {
    info "Configurando variable de entorno SYNC_ARCH_HOME..."
    
    # Detectar el directorio actual del proyecto
    local project_dir="$SCRIPT_DIR"
    
    # Crear archivo de configuración para el usuario actual
    local config_file="$HOME/.sync-arch-config"
    echo "export SYNC_ARCH_HOME=\"$project_dir\"" > "$config_file"
    
    success "Configuración guardada en: $config_file"
    
    # Sugerir añadir a shell profile
    info "Para cargar automáticamente, añade a tu ~/.bashrc o ~/.zshrc:"
    echo "    source $config_file"
}

test_installation() {
    info "Probando instalación..."
    
    # Verificar que el comando existe
    if ! command -v sync-arch >/dev/null 2>&1; then
        error "El comando sync-arch no está disponible en PATH"
        echo "Solución: reinicia tu terminal o ejecuta: hash -r"
        return 1
    fi
    
    # Probar comando básico
    if sync-arch version >/dev/null 2>&1; then
        success "Comando sync-arch funciona correctamente"
    else
        warning "El comando se instaló pero puede tener problemas"
        echo "Prueba manual: sync-arch version"
    fi
    
    # Verificar detección del proyecto
    export SYNC_ARCH_HOME="$SCRIPT_DIR"
    if sync-arch status --dry-run >/dev/null 2>&1; then
        success "Detección del proyecto sync-arch funciona"
    else
        warning "Problemas detectando el proyecto sync-arch"
        echo "Verifica que SYNC_ARCH_HOME apunte al directorio correcto"
    fi
}

show_post_install_info() {
    echo ""
    echo "==============================================="
    success "¡Instalación completada exitosamente!"
    echo "==============================================="
    echo ""
    echo "El comando 'sync-arch' ya está disponible globalmente."
    echo ""
    echo "Pasos siguientes:"
    echo "  1. Reinicia tu terminal o ejecuta: hash -r"
    echo "  2. Prueba: sync-arch version"
    echo "  3. Usa: sync-arch help"
    echo ""
    echo "Para activar autocompletado en tu shell actual:"
    echo "  Bash: source $COMPLETION_DIR/sync-arch"
    echo "  Zsh:  autoload -U compinit && compinit"
    echo ""
    echo "Ejemplos de uso:"
    echo "  sync-arch status                # Ver estado"
    echo "  sync-arch deploy                # Deploy con backup"
    echo "  sync-arch validate              # Validar configuración"
    echo "  sync-arch --help               # Ayuda completa"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    echo "🚀 Instalador del Comando CLI Sync-Arch"
    echo "========================================"
    echo ""
    
    check_requirements
    echo ""
    
    install_cli_command
    echo ""
    
    create_bash_completion
    echo ""
    
    create_zsh_completion  
    echo ""
    
    update_sync_arch_home
    echo ""
    
    test_installation
    echo ""
    
    show_post_install_info
}

# Ejecutar si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
