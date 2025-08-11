# 🔄 Sync-Arch 

Sistema de sincronización inteligente de dotfiles entre múltiples equipos Arch Linux con backup automático, deploy seguro y arquitectura modular avanzada.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Bash](https://img.shields.io/badge/Bash-4.0+-green.svg)](https://www.gnu.org/software/bash/)
[![GNU Stow](https://img.shields.io/badge/GNU%20Stow-Required-orange.svg)](https://www.gnu.org/software/stow/)
[![Systemd](https://img.shields.io/badge/Systemd-User%20Services-red.svg)](https://systemd.io/)

---

## 🎯 **Características Principales**

### ✨ **Sistema Completo de Dotfiles**
- 🔄 **Sincronización bidireccional** automática entre equipos
- 🏠 **Enfoque HOME completo** - sincroniza todo `$HOME` con excepciones granulares
- 🖥️ **Configuraciones por hostname** para diferencias específicas de cada máquina
- 🛡️ **Backup automático** por hostname antes de cambios críticos
- 🔗 **Symlinks con GNU Stow** para edición en tiempo real
- ⚡ **Detección de cambios inteligente** con hashing SHA256

### 🚀 **CLI Global Profesional**
- 🌍 **Comando global `sync-arch`** ejecutable desde cualquier directorio
- 🔍 **Modo dry-run por defecto** para máxima seguridad
- 🎨 **Interfaz colorizada** con mensajes informativos claros
- 📊 **Estado detallado** del repositorio y sincronización
- 🔧 **Autocompletado** para Bash y Zsh

### 🏗️ **Arquitectura Modular Avanzada**
- 📦 **Módulos core especializados** (config, git, stow, conflicts, etc.)
- 🎯 **Comandos modulares** (discover, validate, cleanup, deploy, etc.)
- 🔧 **Context manager centralizado** para gestión de dependencias
- 🔄 **Reutilización máxima de código** sin duplicación
- 🧪 **Fácil testing y extensibilidad**

### ⚙️ **Automatización Inteligente**
- 🔄 **Servicios systemd** para sincronización automática
- 🚀 **Startup sync** - sincroniza al iniciar sesión
- 💾 **Shutdown sync** - guarda cambios antes de apagar/suspender
- 🔐 **Lockfile** para prevenir ejecuciones simultáneas
- 📝 **Logging detallado** con rotación automática

---

## 📥 **Instalación Unificada**

### 🚀 **Instalación Simple en Un Solo Comando**

```bash
# Clonar el repositorio
git clone <tu-repositorio-privado> sync-arch
cd sync-arch

# Ejecutar instalador unificado
./install.sh
```

El instalador unificado configurará automáticamente:
- ✅ Dependencias del sistema (git, stow, python3)
- ✅ Estructura de dotfiles (common + hostname)
- ✅ Servicios systemd user
- ✅ **Comando CLI global `sync-arch`**
- ✅ Sincronización inicial
- ✅ Configuración de autocompletado

### 📋 **Dependencias**
- `git` - Control de versiones
- `stow` - Gestión de symlinks  
- `python3` (≥3.8) - Scripts principales
- `systemd` - Servicios automáticos

---

## 🎮 **Uso del Sistema**

### 🌍 **Comando Global Principal**

```bash
# Sincronización manual (dry-run por defecto)
sync-arch

# Sincronización real (aplicar cambios)
sync-arch --no-dry-run

# Ver ayuda completa
sync-arch --help

# Mostrar estado del repositorio
sync-arch status
```

### 🔍 **Comandos Especializados**

```bash
# === GESTIÓN DE ARCHIVOS ===
sync-arch discover          # Descubrir archivos no gestionados
sync-arch cleanup           # Limpiar archivos ignorados del repo
sync-arch validate          # Validar consistencia config.json vs repo vs $HOME

# === DEPLOYMENT SEGURO ===
sync-arch deploy            # Desplegar symlinks con backup automático
sync-arch rollback          # Restaurar desde backup más reciente
sync-arch rollback nombre   # Restaurar desde backup específico  
sync-arch list-backups      # Listar backups disponibles

# === MODOS DE SINCRONIZACIÓN ===
sync-arch startup           # Modo startup (usado por systemd)
sync-arch shutdown          # Modo shutdown (usado por systemd)
sync-arch manual            # Modo manual (por defecto)

# === OPCIONES GLOBALES ===
sync-arch --dry-run          # Simular cambios (por defecto)
sync-arch --no-dry-run       # Aplicar cambios reales
sync-arch --force            # Forzar sincronización sin verificar cambios
sync-arch --force-overwrite  # Sobrescribir archivos existentes automáticamente
sync-arch --verbose          # Logging detallado
```

### 📁 **Estructura de Archivos**

```
sync-arch/
├── config.json                 # Configuración central
├── dotfiles/
│   ├── common/                  # Archivos compartidos entre equipos
│   │   └── home/               # Symlinks a $HOME
│   └── archlinux/              # Archivos específicos del hostname
│       └── home/               # Overrides específicos
├── scripts/                    # Sistema modular
│   ├── core/                   # Módulos principales
│   │   ├── config.py           # Gestión de configuración
│   │   ├── ignore.py           # Lógica de ignore y precedencia
│   │   ├── git_ops.py          # Operaciones Git
│   │   ├── stow_ops.py         # Operaciones GNU Stow
│   │   ├── conflicts.py        # Resolución de conflictos
│   │   ├── path_utils.py       # Utilidades de rutas centralizadas
│   │   ├── context.py          # Context manager centralizado
│   │   └── utils.py            # Utilidades comunes
│   ├── commands/               # Comandos modulares
│   │   ├── discover.py         # Descubrimiento interactivo
│   │   ├── validate.py         # Validación de consistencia
│   │   ├── cleanup.py          # Limpieza de ignorados
│   │   ├── deploy.py           # Deploy seguro con backup
│   │   ├── status.py           # Estado del repositorio
│   │   └── sync_modes.py       # Modos de sincronización
│   ├── sync.py                 # Dispatcher principal
│   ├── sync.sh                 # Wrapper Bash
│   └── install.py              # Instalador unificado
├── systemd/                    # Servicios systemd
└── sync-arch                   # CLI global
```

---

## ⚙️ **Configuración Avanzada**

### 📝 **config.json**

```json
{
  "common": [
    ""                           // Enfoque HOME: gestiona todo $HOME
  ],
  "archlinux": [                 // Configuración específica del hostname
    ".config/hypr/monitors.conf",
    ".config/hypr/nvidia.conf",
    ".local/bin/script_especifico.py"
  ],
  "system_configs": [            // Archivos del sistema (/etc)
    "/etc/sddm.conf.d/theme.conf"
  ],
  "ignore": [                    // Patrones a ignorar
    "**/*.log",
    "**/.cache/**",
    ".config/Code/**",
    ".config/session/**"
  ],
  "conflict_resolution": {       // Configuración de conflictos
    "backup_existing": true,
    "backup_location": "~/.sync-arch-backup/",
    "interactive_confirm": true,
    "preserve_permissions": true
  }
}
```

### 🔄 **Lógica de Precedencia**

1. **hostname específico** > `ignore` > `common`
2. **Archivos en hostname** sobrescriben carpetas en common
3. **Unfold automático** para overrides parciales
4. **Migración automática** cuando cambian las secciones

---

## 🔧 **Servicios Systemd**

### 📋 **Servicios Instalados**

```bash
# Ver estado de servicios
systemctl --user status sync-arch-startup.service
systemctl --user status sync-arch-shutdown.service

# Logs de servicios
journalctl --user -u sync-arch-startup.service
journalctl --user -u sync-arch-shutdown.service

# Deshabilitar servicios (si es necesario)
systemctl --user disable sync-arch-startup.service
systemctl --user disable sync-arch-shutdown.service
```

### ⏰ **Funcionamiento**

- **sync-arch-startup.service**: Se ejecuta al iniciar sesión (`default.target`)
- **sync-arch-shutdown.service**: Se ejecuta antes de apagado/suspensión (`halt.target`, `reboot.target`, etc.)
- **Timeout de 60 segundos** para evitar bloqueos del sistema
- **Modo no dry-run** para aplicar cambios automáticamente

---

## 🛠️ **Workflows Típicos**

### 🆕 **Configurar Nueva Máquina**

```bash
# 1. Clonar repositorio existente
git clone <tu-repo-privado> sync-arch
cd sync-arch

# 2. Ejecutar instalador unificado
./install.sh

# 3. El sistema detectará automáticamente el hostname y creará la configuración
```

### 📁 **Agregar Nuevos Dotfiles**

```bash
# 1. Descubrir archivos no gestionados
sync-arch discover

# 2. Elegir interactivamente: common, hostname, o ignore
# 3. Validar configuración
sync-arch validate

# 4. Aplicar cambios
sync-arch --no-dry-run
```

### 🔄 **Sincronización Entre Equipos**

```bash
# Equipo A: hacer cambios y sincronizar
sync-arch --no-dry-run

# Equipo B: recibir cambios
sync-arch --no-dry-run
```

### 🛡️ **Backup y Recuperación**

```bash
# Ver backups disponibles
sync-arch list-backups

# Restaurar desde backup más reciente
sync-arch rollback

# Restaurar desde backup específico
sync-arch rollback 2025-08-11_15-30-45
```

---

## 🔍 **Comandos de Diagnóstico**

### 📊 **Estado del Sistema**

```bash
# Estado general
sync-arch status

# Validación completa
sync-arch validate

# Logs detallados
sync-arch --verbose manual

# Ver configuración actual
cat config.json | jq .
```

### 🐛 **Troubleshooting**

```bash
# Ver logs de sistema
tail -f ~/.local/state/sync-arch/sync.log

# Verificar servicios systemd
systemctl --user list-units | grep sync-arch

# Test manual de comandos
sync-arch --dry-run --verbose manual

# Verificar estado de Git
cd /ruta/a/sync-arch && git status
```

---

## 🏗️ **Arquitectura del Sistema**

### 📦 **Módulos Core**

- **`config.py`**: Gestión centralizada de configuración
- **`ignore.py`**: Lógica de patrones ignore y precedencia  
- **`git_ops.py`**: Operaciones Git (push, pull, stash, etc.)
- **`stow_ops.py`**: Operaciones GNU Stow para symlinks
- **`conflicts.py`**: Resolución de conflictos y unfold automático
- **`path_utils.py`**: Utilidades de rutas centralizadas
- **`context.py`**: Context manager para gestión de dependencias
- **`utils.py`**: Utilidades comunes (logging, lockfile, etc.)

### 🎯 **Comandos Modulares**

- **`sync_modes.py`**: Lógica para startup/shutdown/manual
- **`discover.py`**: Descubrimiento interactivo de archivos
- **`validate.py`**: Validación de consistencia
- **`cleanup.py`**: Limpieza de archivos ignorados
- **`deploy.py`**: Deploy seguro con backup
- **`status.py`**: Estado del repositorio

### 🔄 **Flujo de Ejecución**

1. **sync.py**: Dispatcher principal, parsea argumentos
2. **SyncArchContext**: Inicializa todos los managers necesarios
3. **Comando específico**: Ejecuta la lógica correspondiente
4. **Managers core**: Manejan Git, Stow, configuración, etc.
5. **Logging centralizado**: Registra todas las operaciones

---

## 🚀 **Características Avanzadas**

### 🔧 **Context Manager Centralizado**

```python
# Uso del contexto centralizado en módulos
from core import SyncArchContext

context = SyncArchContext(dotfiles_dir, home_dir, project_root, hostname, dry_run)

# Acceso a todos los managers
config = context.get_config()
git_ops = context.get_git_ops()  
stow_ops = context.get_stow_ops()
```

### 🎯 **Eliminación de Duplicidad**

- **Funciones centralizadas** en `path_utils.py`
- **Context manager** para dependencias comunes
- **Reutilización de código** entre comandos
- **Imports optimizados** sin redundancia

### 🔄 **Gestión de Estado**

- **Lockfile** para prevenir ejecuciones simultáneas
- **Stash automático** de cambios locales durante pull
- **Detección de conflictos** antes de aplicar cambios
- **Rollback automático** en caso de errores

---

## ⚠️ **Consideraciones Importantes**

### 🛡️ **Seguridad**

- **Dry-run por defecto** para prevenir cambios accidentales
- **Backup automático** antes de crear symlinks
- **Validación de rutas** para prevenir symlinks maliciosos
- **Lockfile** para prevenir corrupción de datos

### 📝 **Mejores Prácticas**

- **Usar ramas específicas** para diferentes configuraciones si es necesario
- **Revisar cambios** con `--dry-run` antes de aplicar
- **Hacer backups regulares** del repositorio
- **Documentar cambios** en commits descriptivos

### 🔧 **Limitaciones**

- **Requiere GNU Stow** para funcionar correctamente
- **Solo funciona en sistemas Unix/Linux** (debido a symlinks)
- **Requiere Python 3.8+** para características modernas
- **Servicios systemd** solo disponibles en sistemas compatibles

---

## 📚 **Recursos Adicionales**

### 📖 **Documentación**

- **README.md**: Esta documentación completa
- **config.json**: Configuración con comentarios inline
- **Scripts comentados**: Código autodocumentado

### 🔗 **Enlaces Útiles**

- [GNU Stow Manual](https://www.gnu.org/software/stow/manual/)
- [Systemd User Services](https://wiki.archlinux.org/title/Systemd/User)
- [Git Hooks Documentation](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

---

## 🤝 **Contribución**

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature: `git checkout -b mi-feature`
3. Documenta tus cambios
4. Asegúrate de que pasan todas las validaciones: `sync-arch validate`
5. Envía un pull request

---

## 📜 **Licencia**

Este proyecto está bajo licencia MIT. Ver el archivo LICENSE para más detalles.

---

**¡Disfruta de tus dotfiles perfectamente sincronizados! 🎉**