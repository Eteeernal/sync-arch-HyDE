# Configuración específica para archlinux

Esta carpeta contiene **únicamente las diferencias** respecto a la configuración común.

## Enfoque "Solo Diferencias"

En lugar de duplicar toda la configuración, aquí solo se especifican los archivos que **deben ser diferentes** para este equipo específico.

## Estructura actual

```
archlinux/
└── home/                              # Solo overrides de $HOME
    ├── .config/
    │   └── hypr/
    │       ├── monitors.conf          # Configuración específica de monitores
    │       ├── nvidia.conf            # Configuración específica de GPU NVIDIA  
    │       └── userprefs.conf         # Preferencias específicas del equipo
    └── .local/
        └── bin/
            ├── choose_and_check_tree.py  # Scripts específicos del equipo
            ├── choose_and_check.py
            ├── current.py
            └── tree.py
```

## ¿Cómo funciona el override?

1. **Base común**: Se aplica todo `common/home/` como base
2. **Override específico**: Los archivos de esta carpeta **reemplazan** los de common
3. **Resultado**: Tienes la configuración común + las especificaciones de este equipo

### Ejemplo práctico:

**Antes del override:**
- `~/.config/hypr/monitors.conf` → symlink a `common/home/.config/hypr/monitors.conf`

**Después del override:**
- `~/.config/hypr/monitors.conf` → symlink a `archlinux/home/.config/hypr/monitors.conf` ✅

## ¿Qué incluir aquí?

- ✅ **Hardware específico**: monitors.conf, nvidia.conf, audio configs
- ✅ **Scripts únicos**: herramientas específicas de este equipo
- ✅ **Configuraciones de red**: WiFi, VPN específicas del entorno
- ✅ **Preferencias personales**: temas, layouts que solo quieres en este equipo

## ¿Qué NO incluir?

- ❌ **Configuraciones universales**: van en `common/`
- ❌ **Duplicación innecesaria**: si algo funciona igual en todos lados, va en common
- ❌ **Archivos temporales**: cache, logs, etc.

## Agregar nuevos overrides

Para agregar un nuevo archivo específico:

1. **Copia el archivo**: De `common/home/ruta/archivo` a `archlinux/home/ruta/archivo`
2. **Edita el específico**: Modifica el archivo en archlinux/ según necesites
3. **Actualiza config.json**: Agrega la ruta en la sección `"archlinux"`
4. **Ejecuta sync**: `./scripts/sync.sh --no-dry-run`

El sistema automáticamente:
- Detectará el conflicto
- Hará "unfolding" de la carpeta común
- Aplicará el override específico
- Mantendrá el resto de archivos de la carpeta común

## Filosofía

**"Configuración común por defecto, diferencias solo cuando sea necesario"**

Esto resulta en:
- Menos duplicación de código
- Maintenance más fácil
- Experiencia consistente entre equipos  
- Flexibilidad para casos específicos
