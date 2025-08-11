#!/usr/bin/env bash

# uninstall-cli.sh - Desinstalador del comando global sync-arch

set -euo pipefail

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

readonly CLI_TARGET="/usr/local/bin/sync-arch"
readonly COMPLETION_BASH="/usr/local/share/bash-completion/completions/sync-arch"
readonly COMPLETION_ZSH="/usr/local/share/zsh/site-functions/_sync-arch"
readonly USER_CONFIG="$HOME/.sync-arch-config"

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

remove_cli_command() {
    if [[ -f "$CLI_TARGET" ]]; then
        info "Eliminando comando CLI: $CLI_TARGET"
        if [[ $EUID -eq 0 ]]; then
            rm -f "$CLI_TARGET"
        else
            sudo rm -f "$CLI_TARGET"
        fi
        success "Comando CLI eliminado"
    else
        info "Comando CLI no encontrado (ya desinstalado)"
    fi
}

remove_bash_completion() {
    if [[ -f "$COMPLETION_BASH" ]]; then
        info "Eliminando completado de Bash: $COMPLETION_BASH"
        if [[ $EUID -eq 0 ]]; then
            rm -f "$COMPLETION_BASH"
        else
            sudo rm -f "$COMPLETION_BASH"
        fi
        success "Completado de Bash eliminado"
    else
        info "Completado de Bash no encontrado"
    fi
}

remove_zsh_completion() {
    if [[ -f "$COMPLETION_ZSH" ]]; then
        info "Eliminando completado de Zsh: $COMPLETION_ZSH"
        if [[ $EUID -eq 0 ]]; then
            rm -f "$COMPLETION_ZSH"
        else
            sudo rm -f "$COMPLETION_ZSH"
        fi
        success "Completado de Zsh eliminado"
    else
        info "Completado de Zsh no encontrado"
    fi
}

remove_user_config() {
    if [[ -f "$USER_CONFIG" ]]; then
        info "¿Eliminar configuración de usuario? ($USER_CONFIG)"
        read -p "Eliminar configuración [y/N]: " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f "$USER_CONFIG"
            success "Configuración de usuario eliminada"
        else
            info "Configuración de usuario conservada"
        fi
    else
        info "No hay configuración de usuario para eliminar"
    fi
}

verify_uninstallation() {
    info "Verificando desinstalación..."
    
    local issues=()
    
    # Verificar comando CLI
    if command -v sync-arch >/dev/null 2>&1; then
        issues+=("El comando 'sync-arch' aún está disponible")
    fi
    
    # Verificar archivos
    [[ -f "$CLI_TARGET" ]] && issues+=("Archivo CLI aún existe: $CLI_TARGET")
    [[ -f "$COMPLETION_BASH" ]] && issues+=("Completado Bash aún existe: $COMPLETION_BASH")
    [[ -f "$COMPLETION_ZSH" ]] && issues+=("Completado Zsh aún existe: $COMPLETION_ZSH")
    
    if [[ ${#issues[@]} -eq 0 ]]; then
        success "Desinstalación verificada correctamente"
        return 0
    else
        warning "Problemas encontrados en la desinstalación:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        return 1
    fi
}

show_post_uninstall_info() {
    echo ""
    echo "==============================================="
    success "¡Desinstalación completada!"
    echo "==============================================="
    echo ""
    echo "El comando 'sync-arch' ha sido eliminado del sistema."
    echo ""
    echo "Nota: Para usar sync-arch nuevamente:"
    echo "  1. Usa el script local: ./scripts/sync.sh"
    echo "  2. O reinstala: ./install-cli.sh"
    echo ""
    echo "El proyecto sync-arch local permanece intacto."
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    echo "🗑️  Desinstalador del Comando CLI Sync-Arch"
    echo "==========================================="
    echo ""
    
    # Confirmar desinstalación
    warning "Esto eliminará el comando global 'sync-arch' del sistema."
    echo "El proyecto local de sync-arch NO será afectado."
    echo ""
    read -p "¿Continuar con la desinstalación? [y/N]: " -r
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Desinstalación cancelada"
        exit 0
    fi
    
    echo ""
    
    remove_cli_command
    echo ""
    
    remove_bash_completion
    echo ""
    
    remove_zsh_completion
    echo ""
    
    remove_user_config
    echo ""
    
    verify_uninstallation
    echo ""
    
    show_post_uninstall_info
}

# Ejecutar si se llama directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
