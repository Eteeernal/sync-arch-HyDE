#!/usr/bin/env python3
import re
import sys
import json
import os
from pathlib import Path

# Sistema de configuración para archivo markdown dinámico
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

def buscar_primera_tarea_pendiente(nodos):
    """
    Buscar la primera tarea pendiente siguiendo orden secuencial:
    1. Procesar tareas de nivel 0 en orden
    2. Para cada tarea de nivel 0:
       - Si no tiene hijos y no está completada: es la primera
       - Si tiene hijos: buscar primera subtarea no completada (DFS)
       - Si todos los hijos están completados pero ella no: es la tarea
    3. Continuar con siguiente tarea de nivel 0
    """
    
    def buscar_en_subtareas(nodo):
        """Buscar primera tarea pendiente en este nodo y sus hijos (DFS)"""
        if not nodo.checked:
            # Si este nodo no está completado
            if not nodo.hijos:
                # Es una hoja, es trabajable
                return nodo
            else:
                # Tiene hijos, buscar en sus hijos primero
                for hijo in nodo.hijos:
                    resultado = buscar_en_subtareas(hijo)
                    if resultado:
                        return resultado
                
                # Si todos los hijos están completos pero este nodo no,
                # este nodo debe completarse automáticamente o ser trabajable
                return nodo
        else:
            # El nodo está marcado como completado
            # Pero verificar si tiene hijos sin completar (caso de inconsistencia)
            if nodo.hijos:
                for hijo in nodo.hijos:
                    resultado = buscar_en_subtareas(hijo)
                    if resultado:
                        return resultado
        
        return None
    
    # Buscar en tareas principales (nivel 0) en orden secuencial
    for nodo in nodos:
        if nodo.padre is None:  # tarea principal (nivel 0)
            resultado = buscar_en_subtareas(nodo)
            if resultado:
                return resultado
                
    return None

def marcar_tarea(lineas, nodos, texto_seleccionado):
    # Marcar la tarea seleccionada y sus padres si corresponde
    # Buscar nodo por texto exacto
    nodo_obj = None
    for n in nodos:
        if n.texto == texto_seleccionado:
            nodo_obj = n
            break
    if not nodo_obj:
        print("No se encontró la tarea seleccionada.", file=sys.stderr)
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

def generar_tooltip(nodos):
    """Generar tooltip con todas las tareas pendientes mostrando jerarquía visualmente"""
    pendientes = []
    
    def agregar_pendientes(nodo, nivel=0):
        if not nodo.checked:
            # Agregar espacios según el nivel de anidación (4 espacios por nivel)
            espacios = "    " * nivel
            pendientes.append(f"{espacios}[ ] {nodo.texto}")
        
        for hijo in nodo.hijos:
            agregar_pendientes(hijo, nivel + 1)
    
    for nodo in nodos:
        if nodo.padre is None:  # raíz
            agregar_pendientes(nodo, 0)
    
    return "\n".join(pendientes) if pendientes else "✅ Todas las tareas completadas"

def main():
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        # Si no existe el archivo, crear uno básico
        contenido_inicial = """# Lista de tareas con estructura

- [ ] Tarea principal 1
    - [ ] Subtarea 1.1
    - [ ] Subtarea 1.2
- [ ] Tarea principal 2
    - [ ] Subtarea 2.1
        - [ ] Sub-subtarea 2.1.1
"""
        with open(archivo, "w", encoding="utf-8") as f:
            f.write(contenido_inicial)
        lineas = contenido_inicial.splitlines(True)

    nodos = parsear_tareas(lineas)

    # Si se llamó con argumento, es para marcar esa tarea
    if len(sys.argv) > 1:
        tarea_a_marcar = sys.argv[1]
        exito = marcar_tarea(lineas, nodos, tarea_a_marcar)
        if exito:
            with open(archivo, "w", encoding="utf-8") as f:
                f.writelines(lineas)
        else:
            sys.exit(1)
        sys.exit(0)

    # Si no, generar salida JSON para waybar
    primera = buscar_primera_tarea_pendiente(nodos)
    tooltip = generar_tooltip(nodos)
    
    if primera:
        salida = {
            "text": primera.texto,
            "tooltip": tooltip,
            "class": "todolist-tree"
        }
    else:
        salida = {
            "text": "✅ Todo listo",
            "tooltip": tooltip,
            "class": "todolist-tree-complete"
        }
    
    print(json.dumps(salida, ensure_ascii=False))

if __name__ == "__main__":
    main()
