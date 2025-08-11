#!/usr/bin/env python3
import re
import sys
import json
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

def buscar_primera_tarea_pendiente(nodos):
    """
    Buscar la primera tarea pendiente siguiendo esta lógica:
    1. Primero tareas principales (nivel 0) sin completar
    2. Si una tarea principal tiene subtareas, ir a la primera subtarea pendiente
    3. Preferir tareas padre antes que sus hijos cuando es posible trabajar en el padre
    """
    
    def encontrar_tarea_trabajable(nodo):
        """
        Una tarea es trabajable si:
        - No está completada Y
        - Es una hoja (sin hijos) O tiene hijos pero se puede trabajar en ella directamente
        """
        if nodo.checked:
            return None
            
        # Si no tiene hijos, es una tarea directamente trabajable
        if not nodo.hijos:
            return nodo
            
        # Si tiene hijos, buscar primera subtarea trabajable
        for hijo in nodo.hijos:
            subtarea = encontrar_tarea_trabajable(hijo)
            if subtarea:
                return subtarea
                
        # Si todos los hijos están completos pero este nodo no, algo está mal
        # (esto se solucionaría con la propagación automática)
        return nodo
    
    # Buscar en tareas principales (nivel 0) primero
    for nodo in nodos:
        if nodo.padre is None:  # tarea principal
            tarea = encontrar_tarea_trabajable(nodo)
            if tarea:
                return tarea
                
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
    """Generar tooltip con todas las tareas pendientes"""
    pendientes = []
    
    def agregar_pendientes(nodo, prefijo=""):
        if not nodo.checked:
            pendientes.append(f"{prefijo}[ ] {nodo.texto}")
        
        for hijo in nodo.hijos:
            nuevo_prefijo = prefijo + "  " if prefijo else ""
            agregar_pendientes(hijo, nuevo_prefijo)
    
    for nodo in nodos:
        if nodo.padre is None:  # raíz
            agregar_pendientes(nodo)
    
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
