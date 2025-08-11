#!/usr/bin/env python3
"""
Interfaz rofi para seleccionar y marcar tareas del todolist-tree
"""

import re
import sys
import subprocess
import os
from pathlib import Path

# Obtener la ruta del archivo de tareas relativa al script
script_dir = Path(__file__).parent
archivo = Path.home() / ".local" / "share" / "todolist-tree" / "todolist-tree.md"

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
    """Obtener lista de todas las tareas pendientes con formato jerárquico"""
    tareas = []
    
    def agregar_tareas(nodo, prefijo=""):
        if not nodo.checked:
            # Mostrar tarea con indentación visual
            indicador = "🔲" if not nodo.hijos else "📁"
            tareas.append(f"{prefijo}{indicador} {nodo.texto}")
        
        # Agregar hijos (aunque el padre esté marcado, los hijos pueden estar desmarcados)
        for hijo in nodo.hijos:
            nuevo_prefijo = prefijo + "  " if prefijo else ""
            agregar_tareas(hijo, nuevo_prefijo)
    
    for nodo in nodos:
        if nodo.padre is None:  # raíz
            agregar_tareas(nodo)
    
    return tareas

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
    if not opciones:
        subprocess.run([
            "notify-send", 
            "Todolist Tree", 
            "¡Todas las tareas están completadas! 🎉"
        ])
        return None
    
    # Preparar entrada para rofi
    entrada = "\n".join(opciones)
    
    try:
        result = subprocess.run([
            "rofi", 
            "-dmenu", 
            "-i",
            "-p", "Seleccionar tarea tree:",
            "-theme-str", "window { width: 50%; }",
            "-theme-str", "listview { lines: 10; }"
        ], 
        input=entrada, 
        text=True, 
        capture_output=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
    except FileNotFoundError:
        # Si rofi no está disponible, mostrar notificación
        subprocess.run([
            "notify-send", 
            "Error", 
            "Rofi no está instalado"
        ])
    
    return None

def main():
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        subprocess.run([
            "notify-send", 
            "Error", 
            f"No se encontró el archivo {archivo}"
        ])
        sys.exit(1)

    nodos = parsear_tareas(lineas)
    tareas_pendientes = listar_tareas_pendientes(nodos)
    
    # Mostrar rofi y obtener selección
    seleccion = mostrar_rofi(tareas_pendientes)
    
    if seleccion:
        # Marcar la tarea seleccionada
        exito = marcar_tarea(lineas, nodos, seleccion)
        
        if exito:
            # Guardar cambios
            with open(archivo, "w", encoding="utf-8") as f:
                f.writelines(lineas)
            
            # Mostrar notificación de éxito
            texto_limpio = re.sub(r'^[\s]*[🔲📁]\s*', '', seleccion).strip()
            subprocess.run([
                "notify-send", 
                "Tarea Completada", 
                f"✅ {texto_limpio}"
            ])
        else:
            subprocess.run([
                "notify-send", 
                "Error", 
                "No se pudo marcar la tarea"
            ])

if __name__ == "__main__":
    main()