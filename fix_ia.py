import os

def arreglar_indentacion_v2():
    print("📏 Arreglando indentación en ia_module.py (Ronda 7 - Rayos X)...")
    target = os.path.join(os.getcwd(), 'src', 'models', 'ia_module.py')
    
    if not os.path.exists(target):
        print(f"   ❌ No se encontró {target}")
        return

    with open(target, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    fixed = False

    # Recorremos todo el archivo
    for i in range(len(lines)):
        line = lines[i]
        
        # Ignoramos líneas vacías o comentarios
        if not line.strip() or line.strip().startswith("#"):
            continue
            
        # Si la línea termina en dos puntos (:), la SIGUIENTE línea de código debe estar indentada
        if line.strip().endswith(':'):
            current_indent = len(line) - len(line.lstrip())
            
            # Buscamos la siguiente línea que NO sea vacía ni comentario
            found_next = False
            for j in range(i + 1, len(lines)):
                next_line_content = lines[j]
                
                # Si encontramos código real
                if next_line_content.strip() and not next_line_content.strip().startswith("#"):
                    next_indent = len(next_line_content) - len(next_line_content.lstrip())
                    
                    # REGLA: Debe tener MÁS indentación que el padre
                    if next_indent <= current_indent:
                        print(f"   📍 Bloque roto detectado en línea {j+1} (Padre en {i+1})")
                        print(f"      Padre: {line.strip()}")
                        print(f"      Hijo:  {next_line_content.strip()}")
                        
                        # CORRECCIÓN
                        base_indent = line[:current_indent]
                        lines[j] = base_indent + "    " + next_line_content.lstrip()
                        
                        fixed = True
                        print(f"   ✅ Corregido (se forzaron 4 espacios).")
                    
                    # Solo nos importa la primera línea de código después de los dos puntos
                    found_next = True
                    break
            
            if not found_next:
                # Si llegamos al final del archivo y no hubo código después del ':', es un error de sintaxis,
                # pero Python lo marcaría distinto (Unexpected EOF).
                pass

    if fixed:
        with open(target, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("   💾 Archivo guardado con todas las correcciones.")
    else:
        print("   ℹ️ No se detectaron bloques mal indentados (o el archivo ya está bien).")

if __name__ == "__main__":
    arreglar_indentacion_v2()
