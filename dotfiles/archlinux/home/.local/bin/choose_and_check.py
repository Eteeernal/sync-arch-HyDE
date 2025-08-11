#!/usr/bin/env python3
"""
Interfaz rofi para seleccionar y marcar tareas del todolist-tree
"""

import re
import sys
import subprocess
import os
from pathlib import Path

# Archivo de configuración para almacenar la ruta del markdown actual
config_dir = Path.home() / ".local" / "share" / "todolist"
config_file = config_dir / "config.txt"
default_archivo = Path.home() / ".local" / "share" / "todolist" / "todolist.md"

def get_current_file():
    """Obtener el archivo markdown actual desde la configuración"""
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                archivo_path = f.read().strip()
                if archivo_path and Path(archivo_path).exists():
                    return Path(archivo_path)
        except:
            pass
    return default_archivo

def set_current_file(nuevo_archivo):
    """Establecer un nuevo archivo markdown como actual"""
    config_dir.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(str(nuevo_archivo))

# Obtener el archivo actual
archivo = get_current_file()

class Nodo:
    def __init__(self, texto, nivel, checked, linea_idx):
        self.texto = texto
        self.nivel = nivel
        self.checked = checked
        self.linea_idx = linea_idx
        self.hijos = []
        self.padre = None

def parsear_tareas(lineas):
    nodos = []
    stack = []

    for idx, linea in enumerate(lineas):
        # Detectar checkbox con niveles según indentación (espacios o tabs)
        m = re.match(r"^(\s*)[-*]\s+\[( |x)\]\s+(.*)", linea)
        if not m:
            continue

        indent, check, texto = m.groups()
        # Calcular nivel basado en espacios o tabs
        if '\t' in indent:
            nivel = len(indent)  # 1 tab = 1 nivel
        else:
            nivel = len(indent) // 4  # 4 espacios = 1 nivel

        nodo = Nodo(texto.strip(), nivel, check == "x", idx)

        # Insertar en el árbol
        while stack and stack[-1].nivel >= nivel:
            stack.pop()

        if stack:
            nodo.padre = stack[-1]
            stack[-1].hijos.append(nodo)

        stack.append(nodo)
        nodos.append(nodo)

    return nodos

def listar_tareas_pendientes(nodos):
    """Obtener lista de todas las tareas pendientes con formato jerárquico usando tabs por nivel"""
    tareas = []

    def agregar_tareas(nodo):
        if not nodo.checked:
            # Indentación por nivel usando tabs, similar al tooltip (1 tab por nivel)
            indent = "  " * nodo.nivel
            indicador = ""
            tareas.append(f"{indent}{indicador} {nodo.texto}")

        # Agregar hijos (aunque el padre esté marcado, los hijos pueden estar desmarcados)
        for hijo in nodo.hijos:
            agregar_tareas(hijo)

    for nodo in nodos:
        if nodo.padre is None:  # raíz
            agregar_tareas(nodo)

    return tareas

def buscar_archivos_markdown():
    """Buscar archivos markdown en ubicaciones comunes"""
    archivos = []
    ubicaciones = [
        Path.home(),
        Path.home() / "proyectos", 
        Path.home() / "Documentos",
        Path.home() / "Documents",
        Path.home() / "Desktop",
        Path.home() / "Escritorio"
    ]
    
    for ubicacion in ubicaciones:
        if ubicacion.exists():
            try:
                # Buscar archivos .md hasta 3 niveles de profundidad
                for archivo in ubicacion.rglob("*.md"):
                    if archivo.is_file() and ".local" not in str(archivo):
                        archivos.append(archivo)
                for archivo in ubicacion.rglob("*.markdown"):
                    if archivo.is_file() and ".local" not in str(archivo):
                        archivos.append(archivo)
            except:
                continue
    
    # Limitar a 50 archivos más recientes
    archivos = sorted(archivos, key=lambda x: x.stat().st_mtime, reverse=True)[:50]
    return archivos

def obtener_archivos_recientes():
    """Obtener historial de archivos utilizados recientemente"""
    historial_file = config_dir / "historial.txt"
    if historial_file.exists():
        try:
            with open(historial_file, "r", encoding="utf-8") as f:
                rutas = [line.strip() for line in f.readlines() if line.strip()]
                return [Path(ruta) for ruta in rutas if Path(ruta).exists()][:10]
        except:
            pass
    return []

def agregar_a_historial(archivo):
    """Agregar archivo al historial de archivos recientes"""
    historial_file = config_dir / "historial.txt"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Leer historial existente
    historial = []
    if historial_file.exists():
        try:
            with open(historial_file, "r", encoding="utf-8") as f:
                historial = [line.strip() for line in f.readlines() if line.strip()]
        except:
            pass
    
    # Agregar nuevo archivo al inicio (si no existe ya)
    ruta_str = str(archivo)
    if ruta_str in historial:
        historial.remove(ruta_str)
    historial.insert(0, ruta_str)
    
    # Mantener solo los últimos 10
    historial = historial[:10]
    
    # Guardar historial actualizado
    try:
        with open(historial_file, "w", encoding="utf-8") as f:
            f.write("\n".join(historial))
    except:
        pass

def mostrar_menu_seleccion_archivo():
    """Mostrar menú con diferentes opciones para seleccionar archivo"""
    opciones = [
        "🔍 Buscar en archivos encontrados",
        "⏰ Archivos recientes",
        "📝 Escribir ruta manualmente"
    ]
    
    entrada = "\n".join(opciones)
    
    try:
        result = subprocess.run([
            "rofi", 
            "-dmenu", 
            "-i",
            "-p", "¿Cómo seleccionar archivo?:",
            "-theme-str", "window { width: 50%; }",
            "-theme-str", "listview { lines: 4; }"
        ], 
        input=entrada, 
        text=True, 
        capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    return None

def seleccionar_de_lista(archivos, titulo):
    """Mostrar lista de archivos para selección"""
    if not archivos:
        subprocess.run([
            "notify-send", 
            "Sin archivos", 
            "No se encontraron archivos markdown"
        ])
        return None
    
    # Preparar lista con información útil
    opciones = []
    for archivo in archivos:
        try:
            # Mostrar ruta relativa si es posible
            try:
                ruta_rel = archivo.relative_to(Path.home())
                display_path = f"~/{ruta_rel}"
            except:
                display_path = str(archivo)
            
            # Agregar icono según ubicación
            if "proyecto" in str(archivo).lower():
                icono = "💻"
            elif "documento" in str(archivo).lower():
                icono = "📄"
            elif str(archivo.parent) == str(Path.home()):
                icono = "🏠"
            else:
                icono = "📝"
            
            opciones.append(f"{icono} {archivo.name} ({display_path})")
        except:
            opciones.append(f"📝 {archivo.name}")
    
    entrada = "\n".join(opciones)
    
    try:
        result = subprocess.run([
            "rofi", 
            "-dmenu", 
            "-i",
            "-p", titulo,
            "-theme-str", "window { width: 70%; }",
            "-theme-str", "listview { lines: 12; }"
        ], 
        input=entrada, 
        text=True, 
        capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            seleccion = result.stdout.strip()
            # Extraer índice de la selección
            try:
                indice = opciones.index(seleccion)
                return archivos[indice]
            except:
                return None
    except:
        pass
    
    return None

def cambiar_archivo():
    """Abrir selector de archivos mejorado para cambiar el markdown actual"""
    opcion = mostrar_menu_seleccion_archivo()
    
    if not opcion:
        return False
    
    nuevo_archivo = None
    
    if opcion == "🔍 Buscar en archivos encontrados":
        archivos = buscar_archivos_markdown()
        nuevo_archivo = seleccionar_de_lista(archivos, "Seleccionar archivo markdown:")
        
    elif opcion == "⏰ Archivos recientes":
        archivos_recientes = obtener_archivos_recientes()
        nuevo_archivo = seleccionar_de_lista(archivos_recientes, "Archivos recientes:")
        
    elif opcion == "📝 Escribir ruta manualmente":
        # Modo manual mejorado con autocompletado de directorios comunes
        directorios_comunes = [
            f"~/{Path.home().name}",
            "~/proyectos/",
            "~/Documentos/", 
            "~/Documents/",
            "~/Desktop/",
            "~/Escritorio/"
        ]
        
        placeholder = "Ej: ~/proyectos/mi-proyecto.md"
        
        try:
            result = subprocess.run([
                "rofi", 
                "-dmenu",
                "-i",
                "-p", "Ruta del archivo markdown:",
                "-theme-str", "window { width: 60%; }",
                "-theme-str", f'entry {{ placeholder: "{placeholder}"; }}'
            ], 
            input="\n".join(directorios_comunes), 
            text=True, 
            capture_output=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                ruta = result.stdout.strip()
                # Expandir ~ si existe
                if ruta.startswith("~/"):
                    ruta = str(Path.home() / ruta[2:])
                nuevo_archivo = Path(ruta)
        except:
            pass
        return False
    
    # Validar y aplicar el archivo seleccionado
    if nuevo_archivo:
        # Verificar que el archivo existe
        if nuevo_archivo.exists():
            # Verificar que es un archivo markdown
            if nuevo_archivo.suffix.lower() in ['.md', '.markdown']:
                set_current_file(nuevo_archivo)
                agregar_a_historial(nuevo_archivo)
                subprocess.run([
                    "notify-send", 
                    "Archivo Cambiado", 
                    f"📄 {nuevo_archivo.name}\n📁 {nuevo_archivo.parent}"
                ])
                return True
            else:
                subprocess.run([
                    "notify-send", 
                    "Error", 
                    "El archivo debe ser markdown (.md o .markdown)"
                ])
        else:
            subprocess.run([
                "notify-send", 
                "Error", 
                f"El archivo no existe: {nuevo_archivo}"
            ])
    
    return False

def marcar_tarea(lineas, nodos, texto_seleccionado):
    """Marcar la tarea seleccionada y propagar hacia arriba"""
    # Limpiar el texto seleccionado (quitar iconos y espacios)
    texto_limpio = re.sub(r'^[\s]*[🔲📁]\s*', '', texto_seleccionado).strip()
    
    # Buscar nodo por texto exacto
    nodo_obj = None
    for n in nodos:
        if n.texto == texto_limpio:
            nodo_obj = n
            break
    
    if not nodo_obj:
        return False

    # Marcar nodo como hecho (en el archivo)
    linea = lineas[nodo_obj.linea_idx]
    nueva_linea = re.sub(r"\[ \]", "[x]", linea, count=1)
    lineas[nodo_obj.linea_idx] = nueva_linea

    # Actualizar estado en memoria
    nodo_obj.checked = True

    # Subir recursivamente y marcar padres si todos sus hijos están marcados
    padre = nodo_obj.padre
    while padre:
        if all(h.checked for h in padre.hijos):
            # Marcar padre en archivo y memoria
            linea_padre = lineas[padre.linea_idx]
            nueva_linea_padre = re.sub(r"\[ \]", "[x]", linea_padre, count=1)
            lineas[padre.linea_idx] = nueva_linea_padre
            padre.checked = True
            padre = padre.padre
        else:
            break

    return True

def mostrar_rofi(opciones):
    """Mostrar menú rofi con las opciones disponibles"""
    # Agregar opciones del sistema al menú
    opciones_sistema = [
        "📁 Cambiar archivo markdown...",
        "📄 Editar archivo actual...",
        "─" * 30  # Separador visual
    ]
    
    if not opciones:
        # Si no hay tareas, solo mostrar opciones del sistema
        opciones_finales = opciones_sistema[:2]  # Solo cambiar y ver archivo
        mensaje_extra = "¡Todas las tareas están completadas! 🎉"
    else:
        # Combinar opciones del sistema con tareas
        opciones_finales = opciones_sistema + opciones
        mensaje_extra = None
    
    # Preparar entrada para rofi
    entrada = "\n".join(opciones_finales)
    
    try:
        result = subprocess.run([
            "rofi", 
            "-dmenu", 
            "-i",
            "-p", "Seleccionar acción:",
            "-theme-str", "window { width: 60%; }",
            "-theme-str", "listview { lines: 12; }"
        ], 
        input=entrada, 
        text=True, 
        capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            seleccion = result.stdout.strip()
            
            # Manejar opciones del sistema
            if seleccion == "📁 Cambiar archivo markdown...":
                return "CAMBIAR_ARCHIVO"
            elif seleccion == "📄 Editar archivo actual...":
                return "EDITAR_ARCHIVO"
            elif seleccion.startswith("─"):
                return None  # Separador seleccionado, ignorar
            else:
                return seleccion  # Tarea seleccionada
        
    except FileNotFoundError:
        # Si rofi no está disponible, mostrar notificación
        subprocess.run([
            "notify-send", 
            "Error", 
            "Rofi no está instalado"
        ])
    
    if mensaje_extra:
        subprocess.run([
            "notify-send", 
            "Todolist", 
            mensaje_extra
        ])
    
    return None

def editar_archivo_actual():
    """Editar archivo actual en VSCode"""
    archivo_actual = get_current_file()
    try:
        subprocess.run([
            "code", 
            archivo_actual
        ])
    except Exception as e:
        subprocess.run([
            "notify-send", 
            "Error", 
            f"No se pudo leer el archivo: {e}"
        ])

def main():
    while True:  # Loop para permitir múltiples acciones
        archivo_actual = get_current_file()
        
        try:
            with open(archivo_actual, "r", encoding="utf-8") as f:
                lineas = f.readlines()
        except FileNotFoundError:
            subprocess.run([
                "notify-send", 
                "Error", 
                f"No se encontró el archivo {archivo_actual}"
            ])
            sys.exit(1)

        nodos = parsear_tareas(lineas)
        tareas_pendientes = listar_tareas_pendientes(nodos)
        
        # Mostrar rofi y obtener selección
        seleccion = mostrar_rofi(tareas_pendientes)
        
        if not seleccion:
            break  # Usuario canceló o cerró rofi
            
        # Manejar acciones especiales
        if seleccion == "CAMBIAR_ARCHIVO":
            if cambiar_archivo():
                # Archivo cambiado exitosamente, recargar
                continue
            else:
                break
        elif seleccion == "EDITAR_ARCHIVO":
            editar_archivo_actual()
            continue
        else:
            # Es una tarea normal, marcarla
            exito = marcar_tarea(lineas, nodos, seleccion)
            
            if exito:
                # Guardar cambios
                with open(archivo_actual, "w", encoding="utf-8") as f:
                    f.writelines(lineas)
                
                # Mostrar notificación de éxito
                texto_limpio = re.sub(r'^[\s]*[🔲📁]\s*', '', seleccion).strip()
                subprocess.run([
                    "notify-send", 
                    "Tarea Completada", 
                    f"✅ {texto_limpio}"
                ])
                break  # Salir después de marcar una tarea
            else:
                subprocess.run([
                    "notify-send", 
                    "Error", 
                    "No se pudo marcar la tarea"
                ])
                break

if __name__ == "__main__":
    main()