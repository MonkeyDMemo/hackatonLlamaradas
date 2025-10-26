import cv2
import numpy as np
import os

def convertir_carpeta_tiff_a_png(carpeta_origen, carpeta_destino="diferencia_png_quiet"):
    """
    Convierte todos los TIFF de una carpeta a PNG
    """
    
    # Crear carpeta destino
    os.makedirs(carpeta_destino, exist_ok=True)
    
    # Contador
    convertidos = 0
    
    # Procesar cada archivo TIFF
    for archivo in os.listdir(carpeta_origen):
        if archivo.lower().endswith('.tiff') or archivo.lower().endswith('.tif'):
            # Rutas
            ruta_tiff = os.path.join(carpeta_origen, archivo)
            nombre_png = archivo.replace('.tiff', '.png').replace('.tif', '.png')
            ruta_png = os.path.join(carpeta_destino, nombre_png)
            
            # Cargar TIFF
            imagen = cv2.imread(ruta_tiff, cv2.IMREAD_UNCHANGED)
            
            if imagen is None:
                print(f"Error: {archivo}")
                continue
            
            # Escalar a 0-255 para visualización
            img_min = imagen.min()
            img_max = imagen.max()
            
            if img_max > img_min:
                imagen_escalada = ((imagen - img_min) / (img_max - img_min) * 255).astype(np.uint8)
            else:
                imagen_escalada = imagen.astype(np.uint8)
            
            # Guardar PNG
            cv2.imwrite(ruta_png, imagen_escalada)
            print(f"✓ {nombre_png}")
            convertidos += 1
    
    print(f"\nTotal convertidos: {convertidos}")

# USO
if __name__ == "__main__":
    carpeta_tiff = r"C:\Users\resendizjg\Downloads\flares\tiffs\quiet"  # CAMBIA ESTA RUTA
    convertir_carpeta_tiff_a_png(carpeta_tiff)