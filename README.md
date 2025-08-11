# Sync-Arch 🔄

Sistema de sincronización inteligente de dotfiles entre múltiples equipos Arch Linux con backup automático y deploy seguro.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Bash](https://img.shields.io/badge/Bash-4.0+-green.svg)](https://www.gnu.org/software/bash/)
[![GNU Stow](https://img.shields.io/badge/GNU%20Stow-Required-orange.svg)](https://www.gnu.org/software/stow/)

## 🎯 **Características Principales**

### ✨ **Sistema Completo de Dotfiles**
- 🔄 **Sincronización bidireccional** automática entre equipos
- 🏠 **Enfoque HOME completo** - sincroniza todo `$HOME` con excepciones
- 🖥️ **Configuraciones por hostname** para diferencias específicas
- 🛡️ **Backup automático** por hostname antes de cambios
- 🔗 **Symlinks con GNU Stow** para edición en tiempo real

### 🚀 **CLI Global Profesional**
- 🌍 **Comando global `sync-arch`** ejecutable desde cualquier directorio
- 🔍 **Detección automática** del proyecto sync-arch
- ⚡ **Autocompletado** para Bash y Zsh
- 🎨 **Interfaz con colores** y ayuda completa
- 📋 **Instalador automático** con un solo comando

### 🛡️ **Deploy Seguro con Backup**
- 📦 **Backup automático** antes de cualquier deploy
- 🔄 **Rollback completo** en caso de problemas
- 🏠 **Un backup por hostname** para evitar conflictos
- ✅ **Dry-run por defecto** para máxima seguridad
- 🔍 **Detección de conflictos** automática

### 🏗️ **Arquitectura Modular**
- 📁 **Core modules**: Config, Git, Stow, Conflicts, PathUtils
- 🎯 **Commands**: Deploy, Validate, Cleanup, Discover, Status
- 🔄 **Reutilización de código** eliminando duplicidad
- 🛠️ **Extensibilidad** fácil para nuevas funcionalidades

## 📦 **Instalación Rápida**

### **Paso 1: Clonar el Repositorio**
```bash
git clone <tu-repo-privado> ~/proyectos/sync-arch
cd ~/proyectos/sync-arch
```

### **Paso 2: Instalar CLI Global**
```bash
# Instalación automática con permisos de administrador
./install-cli.sh

# Verificar instalación
sync-arch version
sync-arch --help
```

### **Paso 3: Configurar Baseline**
```bash
# Si es tu primer equipo, generar baseline
python3 scripts/install.py

# Si es un equipo adicional
sync-arch deploy --no-dry-run
```

## 🎮 **Uso del CLI Global**

### **Comandos Principales**

```bash
# 🔍 Verificar estado del sistema
sync-arch status

# ✅ Validar configuración actual
sync-arch validate

# 🚀 Deploy seguro con backup automático
sync-arch deploy                    # [DRY-RUN] Ver plan
sync-arch deploy --no-dry-run       # Ejecutar deploy real

# 📦 Gestión de backups
sync-arch list-backups              # Ver backups disponibles
sync-arch rollback                  # Rollback último backup
sync-arch rollback backup_20250811_143500  # Rollback específico

# 🔍 Descubrir archivos nuevos
sync-arch discover                  # Interactivo para nuevos dotfiles

# 🧹 Limpieza automática
sync-arch cleanup                   # [DRY-RUN] Ver archivos a limpiar
sync-arch cleanup --no-dry-run      # Limpiar archivos ignorados

# 🔄 Sincronización manual
sync-arch                          # Sync manual [DRY-RUN]
sync-arch --no-dry-run             # Sync manual real
```

### **Casos de Uso Comunes**

#### **🆕 Configurar Nuevo Equipo**
```bash
# 1. Clonar repo en nuevo equipo
git clone <repo> ~/proyectos/sync-arch
cd ~/proyectos/sync-arch

# 2. Instalar CLI
./install-cli.sh

# 3. Ver qué se va a hacer
sync-arch validate
sync-arch deploy

# 4. Deploy real con backup automático
sync-arch deploy --no-dry-run
```

#### **🔄 Uso Diario**
```bash
# Ver estado antes de trabajar
sync-arch status

# Sincronizar cambios
sync-arch --no-dry-run

# Descubrir nuevos archivos de configuración
sync-arch discover
```

#### **🆘 Recuperación de Problemas**
```bash
# Ver backups disponibles
sync-arch list-backups

# Rollback si algo sale mal
sync-arch rollback

# Rollback a backup específico
sync-arch rollback backup_20250811_143500
```

## 📁 **Estructura del Proyecto**

```
sync-arch/
├── 🌍 CLI Global
│   ├── sync-arch              # Comando global principal
│   ├── install-cli.sh         # Instalador automático
│   └── uninstall-cli.sh       # Desinstalador limpio
│
├── ⚙️ Scripts Core
│   ├── scripts/
│   │   ├── core/              # 🔧 Módulos principales
│   │   │   ├── config.py      # Gestión configuración
│   │   │   ├── ignore.py      # Lógica ignore y precedencia
│   │   │   ├── git_ops.py     # Operaciones Git
│   │   │   ├── stow_ops.py    # Operaciones GNU Stow
│   │   │   ├── conflicts.py   # Resolución conflictos
│   │   │   ├── path_utils.py  # Utilidades rutas (elimina duplicidad)
│   │   │   └── utils.py       # Utilidades comunes
│   │   │
│   │   ├── commands/          # 🎯 Comandos usuario
│   │   │   ├── deploy.py      # Deploy con backup
│   │   │   ├── validate.py    # Validación consistencia
│   │   │   ├── cleanup.py     # Limpieza archivos ignorados
│   │   │   ├── discover.py    # Descubrimiento interactivo
│   │   │   ├── sync_modes.py  # Modos sincronización
│   │   │   └── status.py      # Estado sistema
│   │   │
│   │   ├── sync.py            # 🎼 Orquestador principal
│   │   ├── sync.sh            # 📜 Wrapper Bash
│   │   └── install.py         # 🛠️ Instalador dotfiles
│
├── 📋 Configuración
│   └── config.json            # Configuración central
│
├── 📂 Dotfiles Organizados
│   └── dotfiles/
│       ├── common/home/       # 🏠 Archivos comunes ($HOME)
│       ├── archlinux/home/    # 💻 Específicos hostname
│       └── system_configs/    # ⚙️ Configuraciones sistema
│
└── 📚 Documentación
    ├── README.md              # Este archivo
    └── docs/                  # Documentación adicional
```

## ⚙️ **Configuración Avanzada**

### **config.json - Archivo Central**

```json
{
  "common": [""],              // HOME approach: todo $HOME en común
  "archlinux": [               // Específico para este hostname
    ".config/hypr/monitors.conf",
    ".config/hypr/nvidia.conf",
    ".local/bin/scripts_especificos.py"
  ],
  "system_configs": [          // Configuraciones sistema
    "/etc/sddm.conf.d/theme.conf"
  ],
  "ignore": [                  // Patrones a ignorar
    "**/*.log",
    "**/.cache/**",
    ".config/Code/**",
    ".config/Cursor/**"
  ],
  "conflict_resolution": {     // Configuración conflictos
    "backup_existing": true,
    "backup_location": "~/.sync-arch-backup/",
    "interactive_confirm": true
  }
}
```

### **Precedencia de Configuración**
```
hostname > ignore > common
```

## 🔧 **Funcionalidades Técnicas**

### **🛡️ Sistema de Backup por Hostname**

```bash
# Estructura de backups
~/.sync-arch-backups/
└── archlinux/                    # Por hostname
    └── backup_20250811_143500/   # Timestamped
        ├── backup_metadata.txt   # Metadatos del backup
        └── [archivos_respaldados] # Archivos originales
```

**Características:**
- ✅ Un backup único por hostname (no múltiples versiones)
- ✅ Metadatos completos con información del backup
- ✅ Rollback automático o específico
- ✅ Preservación de permisos y estructura

### **🔄 Unfolding Automático**

Cuando tienes:
- `common/` maneja `.config/hypr/`
- `archlinux/` especifica `.config/hypr/monitors.conf`

El sistema automáticamente:
1. **Descompone** el directorio común en archivos individuales
2. **Migra** `monitors.conf` al directorio específico del hostname
3. **Mantiene** el resto de archivos en común
4. **Actualiza** symlinks automáticamente

### **🔍 Comandos de Diagnóstico**

#### **validate - Detección de Inconsistencias**
```bash
sync-arch validate
```

Detecta 4 tipos de problemas:
- 📁 **MISSING IN REPO**: En config pero no versionado
- 🔗 **MISSING SYMLINKS**: Versionado pero no desplegado  
- ❓ **MISSING EVERYWHERE**: En config pero no existe
- ⚠️ **ORPHANED CONFIG**: En config pero coincide con ignore

#### **cleanup - Limpieza Automática**
```bash
sync-arch cleanup --no-dry-run
```

Elimina automáticamente del repositorio:
- Archivos que coinciden con patrones `ignore`
- Archivos no explícitamente incluidos para el hostname
- **Sin tocar** archivos en `$HOME`

### **🎯 Detección Automática del Proyecto**

El CLI busca sync-arch en:
1. `$SYNC_ARCH_HOME` (variable personalizada)
2. `$HOME/proyectos/sync-arch`
3. `$HOME/projects/sync-arch`
4. `$HOME/sync-arch`
5. `$HOME/.sync-arch`
6. Repositorios git con nombre 'sync-arch'

## 🛠️ **Desarrollo y Extensión**

### **🏗️ Arquitectura Modular**

La refactorización elimina duplicidad de código:

**Antes:**
- ❌ `deploy.py` y `validate.py` tenían `get_repo_path` duplicado
- ❌ Lógica de rutas gestionadas repetida en múltiples archivos  
- ❌ Funciones de normalización de paths duplicadas

**Ahora:**
- ✅ `PathUtils` centraliza toda la lógica de rutas
- ✅ Reutilización completa entre comandos
- ✅ Fácil mantenimiento y extensión

### **📦 Agregar Nuevos Comandos**

```python
# 1. Crear scripts/commands/mi_comando.py
from core.path_utils import PathUtils

class MiComando:
    def __init__(self, config_manager, ignore_manager, dotfiles_dir, home_dir):
        self.path_utils = PathUtils(config_manager, dotfiles_dir, home_dir)
    
    def run_mi_comando(self):
        # Usar funciones centralizadas
        managed_paths = self.path_utils.get_managed_paths()
        # ... tu lógica

# 2. Agregar a scripts/commands/__init__.py
from .mi_comando import MiComando

# 3. Integrar en sync.py y sync.sh
```

## 🚨 **Troubleshooting**

### **Problemas Comunes**

#### **❌ Error: "No se pudo encontrar la instalación de sync-arch"**
```bash
# Solución 1: Definir variable de entorno
export SYNC_ARCH_HOME=/ruta/completa/al/proyecto
sync-arch status

# Solución 2: Ejecutar desde directorio del proyecto
cd ~/proyectos/sync-arch
./scripts/sync.sh status

# Solución 3: Debug mode
SYNC_ARCH_DEBUG=1 sync-arch status
```

#### **❌ Error: "Cambios locales sin commit"**
```bash
# Ver qué cambió
sync-arch status

# Commit manual
cd ~/proyectos/sync-arch
git add -A && git commit -m "Cambios manuales"

# O forzar sync
sync-arch --force --no-dry-run
```

#### **⚠️ Symlinks incorretos después de deploy**
```bash
# Rollback inmediato
sync-arch rollback

# Ver backups disponibles
sync-arch list-backups

# Rollback a backup específico
sync-arch rollback backup_20250811_143500
```

### **🔍 Debug Mode**

```bash
# Activar debug completo
SYNC_ARCH_DEBUG=1 sync-arch deploy

# Ver logs detallados
tail -f ~/.local/state/sync-arch/sync.log
```

## 📚 **Casos de Uso Avanzados**

### **🖥️ Múltiples Equipos**

**Equipo Desktop (archlinux):**
```json
{
  "archlinux": [
    ".config/hypr/monitors.conf",     // Monitor 4K
    ".config/hypr/nvidia.conf",       // GPU NVIDIA
    ".local/bin/desktop_scripts/"     // Scripts específicos
  ]
}
```

**Equipo Laptop (laptop):**
```json
{
  "laptop": [
    ".config/hypr/power.conf",        // Gestión energía
    ".config/waybar/battery.jsonc",   // Módulo batería
    ".local/bin/laptop_scripts/"      // Scripts específicos
  ]
}
```

### **⚙️ Configuraciones del Sistema**

```json
{
  "system_configs": [
    "/etc/sddm.conf.d/theme.conf",
    "/usr/share/sddm/themes/custom/",
    "/etc/systemd/system/custom.service"
  ]
}
```

**Notas importantes:**
- Requiere permisos de administrador
- Solo para archivos críticos del sistema
- Usa rutas absolutas

### **🎨 Themes y Layouts Compartidos**

```json
{
  "common": [""],                     // Todo en común
  "ignore": [
    ".config/waybar/layouts/backup/**",  // Backups personales
    ".config/hypr/themes/testing/**"     // Themes experimentales
  ],
  "archlinux": [
    ".config/waybar/layouts/4k.jsonc",   // Layout específico 4K
    ".config/hypr/themes/desktop.conf"   // Theme específico desktop
  ]
}
```

## 🤝 **Contribución**

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Abre** un Pull Request

### **🏗️ Estructura para Nuevas Features**

- **Core modules** (`scripts/core/`): Funcionalidad base reutilizable
- **Commands** (`scripts/commands/`): Comandos específicos de usuario
- **Tests**: Agregar tests para nueva funcionalidad
- **Docs**: Actualizar README.md y documentación

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para detalles.

---

## ⭐ **¿Te gusta Sync-Arch?**

Si te resulta útil este sistema:
- 🌟 **Dale una estrella** al repositorio
- 🐛 **Reporta bugs** que encuentres
- 💡 **Sugiere mejoras** vía Issues
- 🤝 **Contribuye** con nuevas features

---

**Hecho con ❤️ para la comunidad Arch Linux**