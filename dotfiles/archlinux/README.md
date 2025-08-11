# Configuración específica para archlinux

Esta carpeta contiene dotfiles específicos para el equipo con hostname `archlinux`.

## ¿Qué va aquí?

- **Configuraciones de hardware**: monitores, GPUs, periféricos específicos
- **Scripts personalizados**: herramientas específicas de este equipo  
- **Overrides**: archivos que reemplazan versiones de `common/`
- **Configuraciones de red**: WiFi, VPN específicas del entorno

## Ejemplo de estructura

```
archlinux/
├── .config/
│   ├── hypr/
│   │   ├── monitors.conf      # Configuración específica de monitores
│   │   └── nvidia.conf        # Configuración específica de GPU
│   ├── waybar/
│   │   └── config.jsonc       # Layout específico del equipo
│   └── networkmanager/
│       └── system-connections/ # Conexiones de red específicas
├── .local/
│   └── bin/
│       └── equipo-tool        # Script específico del equipo
└── .ssh/
    └── config                 # Configuración SSH específica
```

## Prioridad

Los archivos en esta carpeta tienen **mayor prioridad** que los de `common/`.

Si existe el mismo archivo en ambas carpetas:
- Se usa la versión de `archlinux/` ✅
- Se ignora la versión de `common/` ❌

## Agregar nuevos archivos

1. Edita `config.json` en la raíz del proyecto
2. Agrega la ruta en la sección `"archlinux"`
3. Ejecuta `./scripts/sync.sh` para aplicar

El sistema automáticamente migrará el archivo si ya existe en `common/`.
