#!/bin/bash
# Sync-Arch Wrapper Script
# Interfaz CLI y integración con systemd para sync.py

set -euo pipefail

# === CONFIGURACIÓN ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_PY="$SCRIPT_DIR/sync.py"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
USER="${USER:-$(whoami)}"
HOSTNAME="${HOSTNAME:-$(uname -n)}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# === FUNCIONES ===
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

show_help() {
    cat << EOF
Sync-Arch - Sistema de sincronización inteligente de dotfiles

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    startup             Sincronización en inicio de sesión
    shutdown            Sincronización antes de apagado/suspensión
    manual              Sincronización manual (por defecto)
    discover            Descubrir y gestionar archivos no sincronizados
    cleanup             Limpiar archivos ignorados del repositorio
    validate            Validar consistencia config.json vs repo vs $HOME
    deploy              Desplegar symlinks con backup automático
    rollback [backup]   Restaurar desde backup (último si no se especifica)
    list-backups        Listar backups disponibles
    status              Mostrar estado del repositorio
    help                Mostrar esta ayuda

OPTIONS:
    --dry-run           Ejecutar en modo simulación (POR DEFECTO)
    --no-dry-run        Ejecutar cambios reales
    --force             Forzar sincronización sin verificar cambios
    --force-overwrite   Sobrescribir archivos existentes automáticamente
    --verbose, -v       Activar logging detallado
    --quiet, -q         Modo silencioso (solo errores)

EXAMPLES:
    $0                          # Sincronización manual en dry-run
    $0 --no-dry-run            # Sincronización manual real
    $0 startup --no-dry-run     # Sincronización de startup real
    $0 discover                 # Buscar archivos nuevos para gestionar
    $0 cleanup                  # Limpiar archivos ignorados del repo (dry-run)
    $0 cleanup --no-dry-run     # Limpiar archivos ignorados del repo (real)
    $0 validate                 # Validar que config.json esté sincronizado
    $0 deploy                   # Desplegar symlinks con backup (dry-run)
    $0 deploy --no-dry-run      # Desplegar symlinks con backup (real)
    $0 rollback                 # Restaurar último backup
    $0 rollback backup_20250811_143500  # Restaurar backup específico
    $0 list-backups             # Ver backups disponibles
    $0 --force-overwrite        # Sobrescribir archivos existentes (equipo nuevo)
    $0 status                   # Ver estado del repositorio
    $0 manual --force -v        # Sincronización forzada y verbosa

ENVIRONMENT:
    Hostname: $HOSTNAME
    Usuario:  $USER
    Repo:     $REPO_DIR

EOF
}

check_dependencies() {
    local missing=()
    
    # Verificar dependencias requeridas
    for cmd in python3 git stow; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Dependencias faltantes: ${missing[*]}"
        echo "Para instalar en Arch Linux:"
        echo "  sudo pacman -S python git stow"
        return 1
    fi
    
    # Verificar Python script
    if [[ ! -f "$SYNC_PY" ]]; then
        error "Script Python no encontrado: $SYNC_PY"
        return 1
    fi
    
    # Verificar que el script Python es ejecutable
    if [[ ! -x "$SYNC_PY" ]]; then
        log "Haciendo ejecutable: $SYNC_PY"
        chmod +x "$SYNC_PY"
    fi
    
    return 0
}

show_status() {
    log "=== Estado del Repositorio ==="
    
    cd "$REPO_DIR"
    
    # Estado Git
    echo -e "\n${BLUE}📁 Repositorio:${NC}"
    echo "  Directorio: $REPO_DIR"
    echo "  Rama actual: $(git branch --show-current 2>/dev/null || echo 'N/A')"
    
    # Cambios locales
    if git status --porcelain | grep -q .; then
        echo -e "\n${YELLOW}📝 Cambios locales pendientes:${NC}"
        git status --short
    else
        echo -e "\n${GREEN}✅ No hay cambios locales pendientes${NC}"
    fi
    
    # Cambios remotos
    git fetch &>/dev/null || true
    local behind=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
    local ahead=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
    
    if [[ $behind -gt 0 ]]; then
        warning "Hay $behind commits pendientes de origin/main"
    elif [[ $ahead -gt 0 ]]; then
        warning "Hay $ahead commits locales sin push"
    else
        success "Repositorio sincronizado con origin/main"
    fi
    
    # Config específica del hostname
    if grep -q "\"$HOSTNAME\"" "$REPO_DIR/config.json" 2>/dev/null; then
        success "Configuración específica encontrada para: $HOSTNAME"
    else
        warning "No hay configuración específica para: $HOSTNAME"
        echo "  Solo se aplicará configuración común"
    fi
    
    # Última sincronización
    local log_file="$HOME/.local/state/sync-arch/sync.log"
    if [[ -f "$log_file" ]]; then
        local last_sync=$(tail -n 20 "$log_file" | grep -E "(completada|completado)" | tail -n 1 | cut -d' ' -f1-2 | tr -d '[]' || echo "N/A")
        echo -e "\n${BLUE}🕒 Última sincronización:${NC} $last_sync"
    fi
}

notify_user() {
    local message="$1"
    local urgency="${2:-normal}"
    
    # Intentar enviar notificación de escritorio
    if command -v notify-send &> /dev/null && [[ -n "${DISPLAY:-}" ]] || [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
        notify-send -u "$urgency" "Sync-Arch" "$message" 2>/dev/null || true
    fi
}

run_sync() {
    local mode="$1"
    shift
    local args=("$@")
    
    log "Iniciando sincronización en modo: $mode"
    
    # Verificar dependencias
    if ! check_dependencies; then
        return 1
    fi
    
    # Construir comando Python
    local python_args=("--mode" "$mode")
    
    # Procesar argumentos
    for arg in "${args[@]}"; do
        case "$arg" in
            --dry-run|--force|--verbose|-v|--no-dry-run|--force-overwrite)
                python_args+=("$arg")
                ;;
            --quiet|-q)
                # Modo silencioso: redirigir stdout pero mantener stderr
                exec 1>/dev/null
                ;;
        esac
    done
    
    # Ejecutar script Python
    local start_time=$(date +%s)
    local success=0
    
    if python3 "$SYNC_PY" "${python_args[@]}"; then
        local duration=$(($(date +%s) - start_time))
        success "Sincronización completada en ${duration}s"
        
        case "$mode" in
            startup)
                notify_user "Dotfiles sincronizados al iniciar sesión"
                ;;
            shutdown)
                notify_user "Cambios guardados antes del apagado"
                ;;
            manual)
                notify_user "Sincronización manual completada"
                ;;
        esac
    else
        local duration=$(($(date +%s) - start_time))
        error "Sincronización falló después de ${duration}s"
        
        notify_user "Error en sincronización de dotfiles" "critical"
        success=1
    fi
    
    return $success
}

# === MAIN ===
main() {
    # Manejar argumentos
    local command="manual"
    local args=()
    
    # Procesar primer argumento como comando
    if [[ $# -gt 0 ]]; then
        case "$1" in
            startup|shutdown|manual|status|help)
                command="$1"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
        esac
    fi
    
    # Resto de argumentos
    args=("$@")
    
    # Ejecutar comando
    case "$command" in
        help)
            show_help
            ;;
        status)
            show_status
            ;;
        startup|shutdown|manual|discover|cleanup|validate|deploy|list-backups)
            run_sync "$command" "${args[@]}"
            ;;
        rollback)
            # Manejar rollback con parámetro opcional de backup
            backup_name=""
            if [[ ${args[0]+isset} ]] && [[ "${args[0]}" != --* ]]; then
                backup_name="${args[0]}"
                args=("${args[@]:1}")  # Remover primer argumento
            fi
            if [[ -n "$backup_name" ]]; then
                run_sync "$command" --backup-name "$backup_name" "${args[@]}"
            else
                run_sync "$command" "${args[@]}"
            fi
            ;;
        *)
            error "Comando desconocido: $command"
            echo "Usa '$0 help' para ver comandos disponibles"
            exit 1
            ;;
    esac
}

# Trap para cleanup en caso de interrupción
trap 'error "Sincronización interrumpida"; exit 130' INT TERM

# Ejecutar main con todos los argumentos
main "$@"
