import tifffile
import numpy as np
from pathlib import Path
import sys
from PIL import Image
import json

def normalizar_imagen(data, banda, stats_por_banda=None):
    """
    Normaliza la imagen al rango [0, 1] según la banda
    """
    valid_data = data[np.isfinite(data)]
    
    if len(valid_data) == 0:
        return np.zeros_like(data)
    
    # Usar estadísticas por banda si están disponibles
    if stats_por_banda and banda in stats_por_banda:
        banda_stats = stats_por_banda[banda]
        if 'global_min' in banda_stats and 'global_max' in banda_stats:
            vmin = banda_stats['global_min']
            vmax = banda_stats['global_max']
        else:
            vmin = np.percentile(valid_data, 1)
            vmax = np.percentile(valid_data, 99)
    else:
        # Usar percentiles locales
        vmin = np.percentile(valid_data, 1)
        vmax = np.percentile(valid_data, 99)
    
    # Asegurar vmin < vmax
    if vmin >= vmax:
        vmin = np.min(valid_data)
        vmax = np.max(valid_data)
        if vmin >= vmax:
            vmax = vmin + 1
    
    # Clipear y normalizar a [0, 1]
    data_clipped = np.clip(data, vmin, vmax)
    data_normalized = (data_clipped - vmin) / (vmax - vmin)
    
    # Reemplazar NaN con 0
    data_normalized = np.nan_to_num(data_normalized, nan=0.0)
    
    return data_normalized

def procesar_y_guardar_imagen(archivo_tiff, carpeta_salida=None):
    """
    Procesa un archivo TIFF y guarda la imagen normalizada
    """
    archivo_path = Path(archivo_tiff)
    
    if not archivo_path.exists():
        print(f"Error: No existe el archivo {archivo_tiff}")
        return False
    
    # Leer imagen
    data = tifffile.imread(archivo_path).astype(np.float32)
    
    # Detectar banda del nombre del archivo
    nombre = archivo_path.stem
    banda = None
    for b in ['0131', '0171', '0193', '0211', '0304', '0335', '0094', '1600', '1700']:
        if b in nombre:
            banda = b
            break
    
    if not banda:
        print(f"Advertencia: No se detectó banda, usando normalización por defecto")
        banda = '0193'
    
    print(f"Procesando: {nombre}")
    print(f"Banda detectada: {banda}")
    
    # Normalizar imagen
    data_norm = normalizar_imagen(data, banda)
    
    # Convertir a imagen de 8 bits (0-255)
    data_8bit = (data_norm * 255).astype(np.uint8)
    
    # Determinar carpeta de salida
    if carpeta_salida is None:
        # Crear carpeta 'normalized' al mismo nivel
        carpeta_salida = archivo_path.parent / 'normalized'
    else:
        carpeta_salida = Path(carpeta_salida)
    
    carpeta_salida.mkdir(exist_ok=True)
    
    # Guardar imagen
    nombre_salida = f"{nombre}_norm.png"
    ruta_salida = carpeta_salida / nombre_salida
    
    # Guardar con PIL
    img = Image.fromarray(data_8bit, mode='L')  # 'L' para escala de grises
    img.save(ruta_salida, 'PNG')
    
    print(f"  Rango original: [{np.min(data):.3f}, {np.max(data):.3f}]")
    print(f"  Imagen normalizada guardada: {ruta_salida}")
    print(f"  Dimensiones: {data.shape}")
    
    return True

def procesar_carpeta_completa(ruta_carpeta):
    """
    Procesa todos los archivos TIFF en una carpeta
    """
    carpeta = Path(ruta_carpeta)
    
    if not carpeta.exists():
        print(f"Error: No existe la carpeta {ruta_carpeta}")
        return
    
    # Buscar archivos TIFF
    archivos_tiff = list(carpeta.glob('*.tif')) + list(carpeta.glob('*.tiff'))
    
    if not archivos_tiff:
        print(f"No se encontraron archivos TIFF en {ruta_carpeta}")
        return
    
    print(f"Encontrados {len(archivos_tiff)} archivos TIFF")
    
    # Crear carpeta de salida
    carpeta_salida = carpeta / 'normalized'
    carpeta_salida.mkdir(exist_ok=True)
    
    # Procesar cada archivo
    exitosos = 0
    for i, archivo in enumerate(archivos_tiff, 1):
        print(f"\n[{i}/{len(archivos_tiff)}]")
        if procesar_y_guardar_imagen(archivo, carpeta_salida):
            exitosos += 1
    
    print(f"\n{'='*50}")
    print(f"Proceso completado: {exitosos}/{len(archivos_tiff)} archivos procesados")
    print(f"Imágenes guardadas en: {carpeta_salida}")

def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python script.py <archivo.tiff>          # Procesar un archivo")
        print("  python script.py <carpeta>                # Procesar toda una carpeta")
        sys.exit()
    
    ruta = Path(sys.argv[1])
    
    if ruta.is_file():
        # Procesar archivo individual
        procesar_y_guardar_imagen(ruta)
    elif ruta.is_dir():
        # Procesar carpeta completa
        procesar_carpeta_completa(ruta)
    else:
        print(f"Error: {ruta} no es un archivo ni carpeta válida")

if __name__ == "__main__":
    main()