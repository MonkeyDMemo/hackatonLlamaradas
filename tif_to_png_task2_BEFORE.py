import cv2
import numpy as np
import os
from pathlib import Path

def convertir_tiff_a_png(ruta_tiff, ruta_png):
    """
    Convierte un archivo TIFF a PNG
    """
    # Cargar TIFF
    imagen = cv2.imread(str(ruta_tiff), cv2.IMREAD_UNCHANGED)
    
    if imagen is None:
        return False
    
    # Escalar a 0-255 para visualización
    img_min = imagen.min()
    img_max = imagen.max()
    
    if img_max > img_min:
        imagen_escalada = ((imagen - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    else:
        imagen_escalada = imagen.astype(np.uint8)
    
    # Guardar PNG
    cv2.imwrite(str(ruta_png), imagen_escalada)
    return True

def procesar_carpetas_numeradas(carpeta_base, subcarpeta_procesar="before"):
    carpeta_base = Path(carpeta_base)
    total_convertidos = 0
    carpetas_procesadas = 0
    
    # Obtener todas las carpetas numeradas
    carpetas_numeradas = sorted([d for d in carpeta_base.iterdir() 
                                if d.is_dir() and d.name.isdigit()])
    
    if not carpetas_numeradas:
        print(f"No se encontraron carpetas numeradas en: {carpeta_base}")
        return
    
    print(f"Encontradas {len(carpetas_numeradas)} carpetas numeradas")
    print(f"Procesando solo subcarpeta: '{subcarpeta_procesar}'\n")
    
    for carpeta_num in carpetas_numeradas:
        # Ruta a la subcarpeta 'before'
        carpeta_origen = carpeta_num / subcarpeta_procesar
        
        if not carpeta_origen.exists():
            print(f"⚠ No existe: {carpeta_origen}")
            continue
        
        # Crear carpeta destino para los PNG (mantener estructura)
        carpeta_destino = carpeta_num / f"{subcarpeta_procesar}_png"
        carpeta_destino.mkdir(exist_ok=True)
        
        print(f"Procesando: {carpeta_num.name}/{subcarpeta_procesar}/")
        
        # Buscar archivos TIFF
        archivos_tiff = list(carpeta_origen.glob("*.tif")) + list(carpeta_origen.glob("*.tiff"))
        
        if not archivos_tiff:
            print(f"  No se encontraron archivos TIFF")
            continue
        
        convertidos_carpeta = 0
        
        for archivo_tiff in archivos_tiff:
            # Definir nombre del archivo PNG
            nombre_png = archivo_tiff.stem + ".png"
            ruta_png = carpeta_destino / nombre_png
            
            # Convertir
            if convertir_tiff_a_png(archivo_tiff, ruta_png):
                print(f"  ✓ {archivo_tiff.name} → {nombre_png}")
                convertidos_carpeta += 1
            else:
                print(f"  ✗ Error: {archivo_tiff.name}")
        
        print(f"  Convertidos: {convertidos_carpeta}/{len(archivos_tiff)}")
        print(f"  PNG guardados en: {carpeta_destino}\n")
        
        total_convertidos += convertidos_carpeta
        carpetas_procesadas += 1
    
    # Resumen final
    print("="*50)
    print(f"RESUMEN FINAL:")
    print(f"Carpetas procesadas: {carpetas_procesadas}/{len(carpetas_numeradas)}")
    print(f"Total archivos convertidos: {total_convertidos}")
    print("="*50)

# USO
if __name__ == "__main__":
    # Ruta base donde están las carpetas 01, 02, 03, etc.
    carpeta_base = r"C:\Users\resendizjg\Downloads\tiffs_no_background\tiffs_no_background"
    
    # Procesar solo la carpeta 'before' de cada carpeta numerada
    procesar_carpetas_numeradas(carpeta_base, subcarpeta_procesar="before")