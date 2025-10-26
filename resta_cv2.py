import cv2
import numpy as np
import os

#imagen_activa = r"C:\Users\resendizjg\Downloads\flares\tiffs\01\during\AIA20140225_0042_0131.tiff"
imagen_activa =r"C:\Users\resendizjg\Downloads\flares\tiffs\quiet\AIA20140822_2320_0193.tiff"
imagen_fondo = r"C:\Users\resendizjg\Downloads\quite_average-193.tif"
    

# Cargar sin conversiones
imagen = cv2.imread(imagen_activa, cv2.IMREAD_UNCHANGED)
fondo = cv2.imread(imagen_fondo, cv2.IMREAD_UNCHANGED)



# Resta directa
diferencia = cv2.subtract(imagen, fondo)

# Guardar
cv2.imwrite('diferencia_quiet_test.tif', diferencia)
#cv2.imwrite('mascara.png', mascara)

# Función adicional para convertir un solo archivo
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

archivo_tiff = r"C:\Users\resendizjg\desarrollo\llamaradas\diferencia_quiet_test.tif"
convertir_tiff_individual(archivo_tiff)