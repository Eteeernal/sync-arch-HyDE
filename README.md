# 🚀 Sync-Arch

**Sistema inteligente de sincronización de dotfiles para Arch Linux multi-equipo**

Sync-Arch es una solución robusta y automatizada para mantener sincronizados tus dotfiles entre múltiples equipos Arch Linux, utilizando Git, GNU Stow y systemd para una experiencia fluida y sin intervención manual.

## ✨ Características principales

- **🔄 Sincronización bidireccional**: Cambios se propagan automáticamente entre equipos
- **🎯 Configuraciones inteligentes**: Archivos comunes + específicos por hostname
- **🔧 GNU Stow**: Gestión de symlinks elegante y reversible
- **⚡ Migración automática**: Reorganización inteligente de carpetas sin conflictos
- **🛡️ Modo dry-run**: Vista previa de cambios antes de aplicar
- **📊 Logging detallado**: Seguimiento completo de todas las operaciones
- **🔒 Lockfile**: Prevención de ejecuciones concurrentes
- **🎮 systemd integration**: Sincronización automática en startup/shutdown
- **🔍 Detección de conflictos**: Manejo inteligente de overrides parciales

## 📋 Requisitos

- **Sistema**: Arch Linux (recomendado)
- **Dependencias**: `git`, `python3`, `stow`
- **Opcional**: Repositorio Git privado para sincronización entre equipos

## 🚀 Instalación rápida

```bash
# 1. Clonar o crear el proyecto
git clone <este-repositorio> sync-arch
cd sync-arch

# 2. Ejecutar instalador automático
./scripts/install.py

# 3. ¡Listo! El sistema está configurado
```

## 📁 Estructura del proyecto

```
sync-arch/
├── config.json                 # Configuración de dotfiles por equipo
├── dotfiles/
│   ├── common/                  # Configuración compartida entre equipos
│   │   ├── .config/
│   │   │   ├── hypr/            # Hyprland configs comunes
│   │   │   ├── waybar/          # Waybar layouts/themes
│   │   │   └── kitty/           # Terminal config
│   │   └── .zshrc               # Shell config
│   └── archlinux/               # Configuración específica por hostname
│       ├── .config/
│       │   ├── hypr/
│       │   │   └── monitors.conf # Config monitores específicos
│       │   └── waybar/
│       │       └── config.jsonc  # Waybar específico del equipo
│       └── .local/bin/          # Scripts específicos
├── scripts/
│   ├── install.py               # Instalador automático
│   ├── sync.py                  # Motor principal (Python)
│   └── sync.sh                  # Interfaz CLI (Bash)
├── systemd/                     # Plantillas servicios systemd
└── README.md                    # Esta documentación
```

## ⚙️ Configuración (config.json)

```json
{
  "common": [
    ".config/hypr/hyprland.conf",
    ".config/waybar/style.css",
    ".config/waybar/layouts/",
    ".zshrc"
  ],
  "desktop": [
    ".config/hypr/monitors.conf",
    ".config/waybar/config.jsonc"
  ],
  "notebook": [
    ".config/hypr/power.conf",
    ".config/waybar/config.jsonc"
  ],
  "ignore": [
    "**/*.log",
    "**/.cache/**",
    ".config/pulse/**"
  ]
}
```

### Lógica de prioridad:
```
ignore > hostname_específico > common
```

## 🎮 Uso diario

### Sincronización manual
```bash
# Vista previa (dry-run por defecto)
./scripts/sync.sh

# Aplicar cambios reales
./scripts/sync.sh --no-dry-run

# Sincronización forzada
./scripts/sync.sh --force --no-dry-run

# Ver estado del repositorio
./scripts/sync.sh status
```

### Modos de sincronización
```bash
# Startup (automático al iniciar sesión)
./scripts/sync.sh startup --no-dry-run

# Shutdown (automático al apagar/suspender)
./scripts/sync.sh shutdown --no-dry-run

# Manual (interactivo)
./scripts/sync.sh manual --no-dry-run
```

## 🔄 Flujos de sincronización

### 🌅 Startup (Inicio de sesión)
1. **Detección**: Verificar cambios Git upstream/local
2. **Skip inteligente**: Si no hay cambios, salir inmediatamente
3. **Git sync**: `stash` → `pull --rebase` → `stash pop`
4. **Resolución**: Detectar y resolver conflictos automáticamente
5. **Aplicación**: `stow common hostname` con prioridades
6. **Notificación**: Informar usuario del resultado

### 🌇 Shutdown (Apagado/Suspensión)
1. **Detección**: Verificar cambios en rutas gestionadas únicamente
2. **Skip inteligente**: Si no hay cambios, salir (optimización)
3. **Commit**: `git add -A` → `commit` → `push`
4. **Timeout**: Máximo 60s (systemd)
5. **Notificación**: Confirmar guardado de cambios

### 🎯 Manual (Interactivo)
1. **Reconfiguración**: Recargar `config.json`
2. **Bidireccional**: Bajar cambios + subir cambios locales
3. **Migración**: Gestionar archivos nuevos en config
4. **Validación**: Detectar conflictos y casos borde
5. **Reporte**: Informe detallado de acciones

## 🧠 Casos de uso avanzados

### Override parcial de carpeta
```json
{
  "common": [
    ".config/waybar/"
  ],
  "desktop": [
    ".config/waybar/config.jsonc"
  ]
}
```

**Resultado**: Desktop hereda toda la carpeta waybar de `common` EXCEPTO `config.jsonc` que usa su versión específica.

### Migración automática
Cuando agregas un archivo específico al config, Sync-Arch:
1. **Detecta** el conflicto automáticamente
2. **Preserva** el contenido actual
3. **Migra** el archivo a la carpeta correcta
4. **Reorganiza** symlinks sin pérdida de datos

### Multi-host con múltiples overrides
```json
{
  "common": [".config/app/"],
  "desktop": [".config/app/desktop.conf"],
  "laptop": [".config/app/battery.conf", ".config/app/wifi.conf"]
}
```

Sync-Arch maneja automáticamente la distribución y priorización.

## 🔧 Integración systemd

### Servicios user automatizados
```bash
# Ver estado de servicios
systemctl --user status sync-arch-startup.service
systemctl --user status sync-arch-shutdown.service

# Logs de sincronización
journalctl --user -u sync-arch-startup.service -f
journalctl --user -u sync-arch-shutdown.service -f

# Deshabilitar temporalmente
systemctl --user disable sync-arch-startup.service
```

### Ubicación de servicios
- **Directorio**: `~/.config/systemd/user/`
- **Archivos**: `sync-arch-startup.service`, `sync-arch-shutdown.service`
- **Logs**: `~/.local/state/sync-arch/sync.log`

## 🚨 Resolución de problemas

### Error: Dependencias faltantes
```bash
sudo pacman -S git python stow
```

### Error: Conflictos Git
```bash
# El script maneja automáticamente, pero si falla:
cd sync-arch
git status
git stash
git pull --rebase
./scripts/sync.sh --force --no-dry-run
```

### Error: Symlinks rotos
```bash
# Recrear symlinks
./scripts/sync.sh --force --no-dry-run
```

### Error: Servicios systemd
```bash
# Reinstalar servicios
./scripts/install.py  # Re-ejecutar instalador
systemctl --user daemon-reload
```

### Debug detallado
```bash
# Logs en tiempo real
tail -f ~/.local/state/sync-arch/sync.log

# Modo verbose
./scripts/sync.sh --verbose --dry-run
```

## 🔐 Seguridad y privacidad

- **Repositorio privado**: Recomendado para configs sensibles
- **Ignores inteligentes**: Automáticamente excluye cache, logs, secrets
- **Dry-run por defecto**: Previene cambios accidentales
- **Lockfile**: Evita corrupción por ejecuciones concurrentes
- **Timeouts**: Previene bloqueos en shutdown

## 🔄 Configuración multi-equipo

### Setup repositorio remoto
```bash
# En el primer equipo
cd sync-arch
git remote add origin git@github.com:usuario/dotfiles-privado.git
git push -u origin main

# En equipos adicionales
git clone git@github.com:usuario/dotfiles-privado.git sync-arch
cd sync-arch
./scripts/install.py
```

### Sincronización automática
Una vez configurado, cada equipo:
- **Al iniciar**: Recibe cambios de otros equipos
- **Al apagar**: Envía sus cambios al repositorio
- **Conflictos**: Se resuelven automáticamente con prioridad por host

## 📊 Logging y monitoreo

### Ubicaciones de logs
- **Principal**: `~/.local/state/sync-arch/sync.log`
- **Systemd**: `journalctl --user -u sync-arch-*`
- **Formato**: `[timestamp] LEVEL: mensaje`

### Niveles de log
- **INFO**: Operaciones normales
- **WARNING**: Problemas no críticos
- **ERROR**: Errores que requieren atención
- **DEBUG**: Detalles técnicos (con `--verbose`)

## 🎯 Extensiones y personalización

### Agregar nueva aplicación
1. **Editar** `config.json`
2. **Ejecutar** `./scripts/sync.sh` (dry-run)
3. **Confirmar** con `--no-dry-run`
4. **Automático**: Se incluye en sincronizaciones futuras

### Nuevo equipo
1. **Clonar** repositorio
2. **Ejecutar** `./scripts/install.py`
3. **Automático**: Se crea sección con hostname en config
4. **Personalizar**: Agregar configs específicas del equipo

### Scripts personalizados
- **Pre-sync hooks**: Modificar `sync.py`
- **Post-sync hooks**: Agregar en `sync.sh`
- **Notificaciones**: Configurar en systemd services

## 📚 Casos de uso reales

### HyDE + Waybar + Hyprland
```json
{
  "common": [
    ".config/hypr/hyprland.conf",
    ".config/hypr/keybindings.conf",
    ".config/waybar/style.css",
    ".config/waybar/themes/",
    ".config/hyde/themes/"
  ],
  "desktop": [
    ".config/hypr/monitors.conf",
    ".config/waybar/config.jsonc"
  ],
  "laptop": [
    ".config/hypr/monitors.conf",
    ".config/hypr/powersaver.conf",
    ".config/waybar/config.jsonc"
  ]
}
```

### Desarrollo + Dotfiles
```json
{
  "common": [
    ".zshrc", ".vimrc", ".gitconfig",
    ".config/kitty/", ".config/starship/"
  ],
  "workstation": [
    ".config/code/settings.json",
    ".local/bin/work-scripts/"
  ],
  "laptop": [
    ".config/code/settings.json",
    ".ssh/config"
  ]
}
```

## 🤝 Contribución

### Estructura del código
- **`sync.py`**: Lógica principal, algoritmos de migración
- **`sync.sh`**: CLI, integración systemd, UX
- **`install.py`**: Instalación automática, detección de sistema

### Agregar features
1. **Fork** del repositorio
2. **Branch** para la feature
3. **Tests** en casos reales
4. **PR** con descripción detallada

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.

## 🙏 Agradecimientos

- **HyDE Community**: Inspiración para gestión de temas
- **GNU Stow**: Herramienta elegante de symlinks
- **Arch Linux**: Sistema base robusto y flexible

---

**Sync-Arch** - Sincronización inteligente de dotfiles para el ecosistema Arch Linux.

*Desarrollado con ❤️ para la comunidad de usuarios avanzados de Linux.*
