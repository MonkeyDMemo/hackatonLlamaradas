import cv2
import numpy as np
import os

def convertir_tiff_a_png(imagen_tiff, ruta_salida_png):
    """
    Convierte una imagen TIFF a PNG escalando para mejor visualización
    """
    # Escalar a 0-255 para mejor visualización en PNG
    img_min = imagen_tiff.min()
    img_max = imagen_tiff.max()
    
    if img_max > img_min:
        imagen_escalada = ((imagen_tiff - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    else:
        imagen_escalada = imagen_tiff.astype(np.uint8)
    
    # Guardar como PNG
    cv2.imwrite(ruta_salida_png, imagen_escalada)

def procesar_quiet_flares():
    """
    Procesa las imágenes de la carpeta quiet aplicando resta de fondo y guarda PNG
    """
    
    # Rutas
    ruta_quiet = r"C:\Users\resendizjg\Downloads\flares\tiffs\quiet"
    imagen_fondo_131 = r"C:\Users\resendizjg\Downloads\quite_average-131.tif"
    imagen_fondo_193 = r"C:\Users\resendizjg\Downloads\quite_average-193.tif"
    
    # Verificar que exista la carpeta quiet
    if not os.path.exists(ruta_quiet):
        print(f"ERROR: No se encuentra la carpeta: {ruta_quiet}")
        return
    
    # Verificar que existan las imágenes de fondo
    if not os.path.exists(imagen_fondo_131):
        print(f"ERROR: No se encuentra la imagen de fondo 131: {imagen_fondo_131}")
        return
    
    if not os.path.exists(imagen_fondo_193):
        print(f"ERROR: No se encuentra la imagen de fondo 193: {imagen_fondo_193}")
        return
    
    # Cargar las imágenes de fondo
    print("Cargando imágenes de fondo...")
    fondo_131 = cv2.imread(imagen_fondo_131, cv2.IMREAD_UNCHANGED)
    fondo_193 = cv2.imread(imagen_fondo_193, cv2.IMREAD_UNCHANGED)
    
    if fondo_131 is None or fondo_193 is None:
        print("ERROR: No se pudieron cargar las imágenes de fondo")
        return
    
    print(f"Fondo 131: {fondo_131.shape}")
    print(f"Fondo 193: {fondo_193.shape}")
    
    # Crear carpeta de salida
    carpeta_salida = os.path.join(ruta_quiet, "diferencia_png")
    os.makedirs(carpeta_salida, exist_ok=True)
    print(f"\nCarpeta de salida: {carpeta_salida}")
    
    # Contadores
    procesadas_131 = 0
    procesadas_193 = 0
    errores = 0
    
    print(f"\nProcesando archivos en: {ruta_quiet}")
    print("-" * 60)
    
    # Procesar archivos directamente en quiet
    for archivo in os.listdir(ruta_quiet):
        archivo_path = os.path.join(ruta_quiet, archivo)
        
        # Solo procesar archivos TIFF
        if not archivo.lower().endswith('.tiff'):
            continue
            
        # Procesar archivos _0131.tiff
        if '_0131' in archivo.lower():
            try:
                imagen = cv2.imread(archivo_path, cv2.IMREAD_UNCHANGED)
                
                if imagen is None:
                    print(f"  ✗ Error leyendo: {archivo}")
                    errores += 1
                    continue
                
                if imagen.shape != fondo_131.shape:
                    print(f"  ✗ Error dimensiones: {archivo}")
                    print(f"    Imagen: {imagen.shape}, Fondo: {fondo_131.shape}")
                    errores += 1
                    continue
                
                # Resta
                diferencia = cv2.subtract(imagen, fondo_131)
                
                # Guardar PNG
                nombre_salida = archivo.replace('.tiff', '_diff.png')
                ruta_salida = os.path.join(carpeta_salida, nombre_salida)
                convertir_tiff_a_png(diferencia, ruta_salida)
                
                print(f"  ✓ 131: {nombre_salida}")
                procesadas_131 += 1
                
            except Exception as e:
                print(f"  ✗ Error con {archivo}: {str(e)}")
                errores += 1
                
        # Procesar archivos _0193.tiff
        elif '_0193' in archivo.lower():
            try:
                imagen = cv2.imread(archivo_path, cv2.IMREAD_UNCHANGED)
                
                if imagen is None:
                    print(f"  ✗ Error leyendo: {archivo}")
                    errores += 1
                    continue
                
                if imagen.shape != fondo_193.shape:
                    print(f"  ✗ Error dimensiones: {archivo}")
                    print(f"    Imagen: {imagen.shape}, Fondo: {fondo_193.shape}")
                    errores += 1
                    continue
                
                # Resta
                diferencia = cv2.subtract(imagen, fondo_193)
                
                # Guardar PNG
                nombre_salida = archivo.replace('.tiff', '_diff.png')
                ruta_salida = os.path.join(carpeta_salida, nombre_salida)
                convertir_tiff_a_png(diferencia, ruta_salida)
                
                print(f"  ✓ 193: {nombre_salida}")
                procesadas_193 += 1
                
            except Exception as e:
                print(f"  ✗ Error con {archivo}: {str(e)}")
                errores += 1
    
    # Resumen
    total_procesadas = procesadas_131 + procesadas_193
    
    print("\n" + "="*60)
    print("RESUMEN - CARPETA QUIET")
    print("="*60)
    print(f"Total procesadas: {total_procesadas}")
    print(f"  - Imágenes _0131: {procesadas_131}")
    print(f"  - Imágenes _0193: {procesadas_193}")
    if errores > 0:
        print(f"Errores: {errores}")
    print("="*60)
    
    if total_procesadas > 0:
        print(f"\n✓ Completado!")
        print(f"Los PNG están en: {carpeta_salida}")
    else:
        print("\n⚠ No se procesaron imágenes")

if __name__ == "__main__":
    print("="*60)
    print("PROCESADOR DE FLARES SOLARES - CARPETA QUIET")
    print("="*60)
    
    print("\nEste script:")
    print("1. Lee las imágenes TIFF de la carpeta 'quiet'")
    print("2. Aplica resta de fondo (131 o 193 según corresponda)")
    print("3. Guarda PNG en 'quiet/diferencia_png/'")
    
    respuesta = input("\n¿Proceder? (s/n): ").strip().lower()
    
    if respuesta == 's':
        procesar_quiet_flares()
    else:
        print("Cancelado.")