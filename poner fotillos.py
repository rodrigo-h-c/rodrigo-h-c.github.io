import os
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from datetime import datetime
from bs4 import BeautifulSoup
import re

# ==========================================
# CONFIGURACIÓN DE RUTAS A PRUEBA DE FALLOS
# ==========================================
# Esto obtiene la ruta exacta de la carpeta donde guardaste ESTE script de Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Unimos esa ruta con los nombres de los archivos/carpetas
HTML_FILE = os.path.join(BASE_DIR, "archivo.html")
FOTOS_DIR = os.path.join(BASE_DIR, "fotospagpro")

def seleccionar_imagen():
    """Abre un diálogo para seleccionar una imagen."""
    root = tk.Tk()
    root.withdraw() 
    file_path = filedialog.askopenfilename(
        title="Selecciona una imagen para el archivo",
        filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp")]
    )
    return file_path

def pedir_datos():
    """Pide al usuario la fecha y la descripción."""
    root = tk.Tk()
    root.withdraw()
    
    fecha = simpledialog.askstring(
        "Fecha de la foto", 
        "Ingresa la fecha (ej. 2 de mayo, 2026):",
        parent=root
    )
    if not fecha:
        return None, None

    descripcion = simpledialog.askstring(
        "Descripción", 
        "Ingresa la descripción de la foto:",
        parent=root
    )
    
    return fecha, descripcion

def convertir_fecha_a_orden(fecha_str):
    """Convierte el string de fecha para poder ordenarlo."""
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    
    fecha_str = fecha_str.lower().replace(",", "").replace(" de ", " ")
    partes = fecha_str.split()
    
    try:
        if len(partes) >= 3:
            dia = int(partes[0])
            mes = meses.get(partes[1], 1)
            anio = int(partes[2])
            return datetime(anio, mes, dia)
    except Exception as e:
        pass
    
    return datetime(1900, 1, 1)

def actualizar_html(nueva_foto_nombre, fecha, descripcion):
    """Lee el archivo HTML, inyecta la nueva foto y el objeto en el script, y ordena."""
    
    if not os.path.exists(HTML_FILE):
        messagebox.showerror("Error", f"No se encontró el archivo:\n{HTML_FILE}")
        return False

    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. ACTUALIZAR EL ARRAY DE JAVASCRIPT
    script_tags = soup.find_all('script')
    target_script = None
    
    for script in script_tags:
        if script.string and "const fotos =" in script.string:
            target_script = script
            break
            
    if not target_script:
        messagebox.showerror("Error", "No se encontró el array 'const fotos =' en el HTML.")
        return False

    js_content = target_script.string
    
    array_pattern = r'const fotos = \[([\s\S]*?)\];'
    match = re.search(array_pattern, js_content)
    
    if not match:
        messagebox.showerror("Error", "No se pudo parsear el array de fotos en JS.")
        return False
        
    inner_array_content = match.group(1).strip()
    
    fotos_list = []
    lineas_js = inner_array_content.split('\n')
    for linea in lineas_js:
        linea = linea.strip()
        if linea.startswith('{') and linea.endswith(('}', '},')):
            src_match = re.search(r"src:\s*'(.*?)'", linea)
            date_match = re.search(r"date:\s*'(.*?)'", linea)
            caption_match = re.search(r"caption:\s*'(.*?)'", linea)
            
            if src_match and date_match and caption_match:
                fotos_list.append({
                    'src': src_match.group(1),
                    'date': date_match.group(1),
                    'caption': caption_match.group(1)
                })

    # Añadir la nueva foto a la lista
    fotos_list.append({
        'src': f"fotospagpro/{nueva_foto_nombre}",
        'date': fecha,
        'caption': descripcion
    })
    
    # Ordenar la lista (de más reciente a más antigua)
    fotos_list.sort(key=lambda x: convertir_fecha_a_orden(x['date']), reverse=True)

    # Reconstruir el array de JS
    nuevo_array_js = "const fotos = [\n"
    for i, foto in enumerate(fotos_list):
        coma = "," if i < len(fotos_list) - 1 else ""
        nuevo_array_js += f"            {{ src: '{foto['src']}', date: '{foto['date']}', caption: '{foto['caption']}' }}{coma}\n"
    nuevo_array_js += "        ];"

    nuevo_js_content = re.sub(array_pattern, nuevo_array_js, js_content)
    target_script.string.replace_with(nuevo_js_content)

    # 2. ACTUALIZAR EL GRID DE MINIATURAS HTML
    grid_div = soup.find('div', class_='ig-grid')
    if grid_div:
        grid_div.clear()
        
        for i, foto in enumerate(fotos_list):
            thumb_html = f"""
                <div class="ig-thumb" onclick="openModal({i})">
                    <img alt="" src="{foto['src']}"/>
                    <div class="ig-thumb-overlay"><span>Chismosear</span></div>
                </div>"""
            fragment = BeautifulSoup(thumb_html, 'html.parser')
            grid_div.append(fragment)
    else:
        messagebox.showerror("Error", "No se encontró el <div class='ig-grid'> en el HTML.")
        return False

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        final_html = str(soup).replace("&lt;", "<").replace("&gt;", ">")
        f.write(final_html)

    return True

def main():
    print("Iniciando Gestor de Archivo...")
    
    img_path = seleccionar_imagen()
    if not img_path:
        print("Operación cancelada.")
        return

    fecha, descripcion = pedir_datos()
    if not fecha or not descripcion:
        print("Operación cancelada. Datos incompletos.")
        return

    if not os.path.exists(FOTOS_DIR):
        os.makedirs(FOTOS_DIR)
        
    img_filename = os.path.basename(img_path)
    clean_filename = img_filename.replace(" ", "_").lower()
    destino_path = os.path.join(FOTOS_DIR, clean_filename)
    
    try:
        shutil.copy2(img_path, destino_path)
        print(f"Imagen copiada a: {destino_path}")
    except Exception as e:
        messagebox.showerror("Error de archivo", f"No se pudo copiar la imagen:\n{e}")
        return

    exito = actualizar_html(clean_filename, fecha, descripcion)
    
    if exito:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Éxito", f"¡Foto añadida correctamente!\nEl archivo {HTML_FILE} ha sido actualizado.")
        print("Proceso completado exitosamente.")

if __name__ == "__main__":
    main()