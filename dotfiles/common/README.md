# Configuración Común (Enfoque HOME)

Esta carpeta contiene una **réplica completa** de la estructura de `$HOME` que se aplica a todos los equipos.

## Estructura

```
common/
└── home/                        # Réplica de $HOME
    ├── .config/                 # Todas las configuraciones base
    │   ├── hypr/                # Hyprland (excepto archivos específicos por equipo)
    │   ├── waybar/              # Waybar completo (themes, layouts, modules)
    │   ├── hyde/                # HyDE themes y configuración
    │   ├── kitty/               # Terminal configuration
    │   ├── rofi/                # Application launcher
    │   ├── dunst/               # Notification daemon
    │   ├── fastfetch/           # System info tool
    │   ├── starship/            # Shell prompt
    │   └── zsh/                 # Zsh configuration
    ├── .local/
    │   └── bin/                 # Scripts compartidos entre equipos
    ├── .zshrc                   # Shell configuration
    └── .bashrc                  # Bash configuration
```

## Enfoque "HOME Completo"

- ✅ **`home/` se aplica completo** a todos los equipos por defecto
- ✅ **Automático**: Cualquier dotfile nuevo se sincroniza sin configuración
- ✅ **Override inteligente**: Los archivos específicos por hostname reemplazan automáticamente los de aquí

## Qué incluir aquí

- ✅ **Toda configuración que funciona universalmente**
- ✅ **Temas y layouts consistentes entre equipos**
- ✅ **Scripts y herramientas generales**
- ✅ **Configuraciones base de aplicaciones**

## Qué se override automáticamente

Los archivos específicos por hostname (en `../archlinux/home/`) **reemplazan automáticamente** los de aquí:

- `monitors.conf` → hardware específico
- `nvidia.conf` → GPU específica  
- `userprefs.conf` → preferencias del equipo
- Scripts personalizados del equipo

## Ventajas de este enfoque

1. **Escalabilidad automática**: Nuevos dotfiles se sincronizan sin configurar
2. **Menos mantenimiento**: Solo especificas diferencias, no duplicas todo
3. **Consistent UX**: Misma experiencia base en todos los equipos
4. **Override selectivo**: Solo cambias lo que necesitas por equipo
