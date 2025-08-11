# Configuración Común

Esta carpeta contiene dotfiles que se aplican a **todos los equipos**.

## Estructura recomendada

```
common/
├── .config/
│   ├── hypr/              # Hyprland configs base
│   ├── waybar/            # Waybar themes y layouts
│   ├── kitty/             # Terminal configuration
│   ├── rofi/              # Application launcher
│   └── dunst/             # Notification daemon
├── .local/
│   └── bin/               # Scripts compartidos
├── .zshrc                 # Shell configuration
└── .gitconfig             # Git global config
```

## Qué incluir aquí

- ✅ Configuraciones que funcionan en todos los equipos
- ✅ Temas y layouts visuales consistentes
- ✅ Scripts y herramientas generales
- ✅ Configuraciones de shell y terminal
- ✅ Keybindings y atajos comunes

## Qué NO incluir aquí

- ❌ Configuraciones específicas de hardware (monitores, GPU)
- ❌ Scripts con rutas absolutas específicas
- ❌ Configuraciones que dependen del hostname
- ❌ Archivos con secrets o información personal

## Migración automática

Si agregas un archivo específico para un equipo en `config.json`, Sync-Arch automáticamente:

1. Detecta el conflicto
2. Migra el archivo a la carpeta del equipo
3. Reorganiza los symlinks
4. Mantiene la configuración común para el resto de archivos
