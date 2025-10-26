# Función adicional para convertir un solo archivo
import cv2
import numpy as np
import os

def convertir_tiff_individual(ruta_tiff, ruta_png=None):
    """
    Convierte un solo archivo TIFF a PNG
    """
    if ruta_png is None:
        ruta_png = ruta_tiff.replace('.tiff', '.png').replace('.tif', '.png')
    
    imagen = cv2.imread(ruta_tiff, cv2.IMREAD_UNCHANGED)
    
    if imagen is None:
        print(f"Error: No se pudo leer {ruta_tiff}")
        return False
    
    # Escalar a 0-255
    img_min = imagen.min()
    img_max = imagen.max()
    
    if img_max > img_min:
        imagen_escalada = ((imagen - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    else:
        imagen_escalada = np.zeros_like(imagen, dtype=np.uint8)
    
    cv2.imwrite(ruta_png, imagen_escalada)
    print(f"✓ Convertido: {os.path.basename(ruta_tiff)} → {os.path.basename(ruta_png)}")
    return True

archivo_tiff = r"C:\Users\resendizjg\Downloads\flares\tiffs\45\during\AIA20140825_2006_0193.tiff"
convertir_tiff_individual(archivo_tiff)