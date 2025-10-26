import tifffile
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import sys
from pathlib import Path
import os
from PIL import Image

# Configurar encoding para Windows
if sys.platform == 'win32':
    import locale
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

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

def detectar_banda(nombre_archivo):
    """
    Detecta la banda del nombre del archivo
    """
    bandas = ['0131', '0171', '0193', '0211', '0304', '0335', '0094', '1600', '1700']
    for banda in bandas:
        if banda in nombre_archivo:
            return banda
    return None

def procesar_carpeta_tiff(ruta_carpeta):
    """
    Procesa todos los archivos TIFF en una carpeta y genera:
    - Carpeta 'graficas': imágenes con ejes, título y barra de color
    - Carpeta 'imagenes': solo la imagen sin elementos adicionales
    - Carpeta 'normalized': imágenes normalizadas según la banda
    Mantiene la resolución original de 1024x1024
    """
    
    carpeta = Path(ruta_carpeta)
    
    if not carpeta.exists() or not carpeta.is_dir():
        print(f"Error: La ruta '{ruta_carpeta}' no existe o no es una carpeta")
        return
    
    # Crear carpetas de salida
    carpeta_graficas = carpeta / 'graficas'
    carpeta_imagenes = carpeta / 'imagenes'
    carpeta_normalized = carpeta / 'normalized'
    
    carpeta_graficas.mkdir(exist_ok=True)
    carpeta_imagenes.mkdir(exist_ok=True)
    carpeta_normalized.mkdir(exist_ok=True)
    
    # Buscar todos los archivos TIFF
    archivos_tiff = list(carpeta.glob('*.tif')) + list(carpeta.glob('*.tiff'))
    
    if not archivos_tiff:
        print(f"No se encontraron archivos TIFF en {ruta_carpeta}")
        return
    
    print(f"Encontrados {len(archivos_tiff)} archivos TIFF")
    print(f"Procesando con resolucion nativa de 1024x1024...")
    print("Generando: graficas, imagenes y normalizadas")
    print("-" * 50)
    
    # Configurar el mapa de color
    cmap_name = 'gist_heat'
    cmap = plt.colormaps[cmap_name].copy()
    cmap.set_bad('black')
    
    # Estadísticas para el resumen
    procesados = 0
    errores = 0
    
    # Procesar cada archivo
    for i, archivo_tiff in enumerate(archivos_tiff, 1):
        try:
            print(f"\n[{i}/{len(archivos_tiff)}] Procesando: {archivo_tiff.name}")
            
            # Leer la imagen
            data = tifffile.imread(archivo_tiff).astype(np.float32)
            
            # Verificar dimensiones
            height, width = data.shape
            print(f"  Dimensiones: {width}x{height}")
            
            # Obtener nombre base sin extensión
            nombre_base = archivo_tiff.stem
            
            # Detectar banda para normalización
            banda = detectar_banda(nombre_base)
            if banda:
                print(f"  Banda detectada: {banda}")
            else:
                print(f"  Banda no detectada, usando normalización por defecto")
                banda = '0193'
            
            # --- 1. GENERAR GRÁFICA COMPLETA ---
            print("  Generando gráfica con ejes...")
            dpi = 100
            fig_width = 12
            fig_height = 10
            
            plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
            
            # Manejar valores para LogNorm
            if np.all(data <= 0):
                plt.imshow(data, cmap=cmap, origin='lower')
            else:
                plt.imshow(data, cmap=cmap, origin='lower', norm=mcolors.LogNorm())
            
            plt.colorbar(label='Pixel value')
            plt.title(archivo_tiff.name)
            plt.xlabel('X')
            plt.ylabel('Y')
            plt.tight_layout()
            
            # Guardar gráfica completa
            ruta_grafica = carpeta_graficas / f"{nombre_base}_grafica.png"
            plt.savefig(ruta_grafica, dpi=dpi, bbox_inches='tight')
            plt.close()
            
            # --- 2. GENERAR SOLO IMAGEN (1024x1024 exactos) ---
            print("  Generando imagen sin ejes...")
            img_size_inches = 10.24  # 1024 pixels / 100 dpi = 10.24 inches
            img_dpi = 100
            
            fig = plt.figure(figsize=(img_size_inches, img_size_inches), dpi=img_dpi, frameon=False)
            ax = plt.Axes(fig, [0., 0., 1., 1.])
            ax.set_axis_off()
            fig.add_axes(ax)
            
            # Mostrar solo la imagen
            if np.all(data <= 0):
                ax.imshow(data, cmap=cmap, origin='lower', aspect='equal')
            else:
                ax.imshow(data, cmap=cmap, origin='lower', norm=mcolors.LogNorm(), aspect='equal')
            
            # Guardar solo la imagen con resolución exacta
            ruta_imagen = carpeta_imagenes / f"{nombre_base}_imagen.png"
            plt.savefig(ruta_imagen, dpi=img_dpi, pad_inches=0)
            plt.close()
            
            # --- 3. GENERAR IMAGEN NORMALIZADA ---
            print("  Generando imagen normalizada...")
            
            # Normalizar imagen
            data_norm = normalizar_imagen(data, banda)
            
            # Convertir a imagen de 8 bits (0-255)
            data_8bit = (data_norm * 255).astype(np.uint8)
            
            # Guardar imagen normalizada
            nombre_salida_norm = f"{nombre_base}_norm.png"
            ruta_normalizada = carpeta_normalized / nombre_salida_norm
            
            # Guardar con PIL
            img = Image.fromarray(data_8bit, mode='L')  # 'L' para escala de grises
            img.save(ruta_normalizada, 'PNG')
            
            # Mostrar estadísticas
            print(f"  Rango original: [{np.min(data):.3f}, {np.max(data):.3f}]")
            print(f"  Rango normalizado: [0, 255]")
            print(f"  [OK] Archivos guardados:")
            print(f"    - Gráfica: {ruta_grafica.name}")
            print(f"    - Imagen: {ruta_imagen.name}")
            print(f"    - Normalizada: {ruta_normalizada.name}")
            
            procesados += 1
            
        except Exception as e:
            errores += 1
            print(f"  [ERROR] Error procesando {archivo_tiff.name}: {str(e)}")
            continue
    
    # Resumen final
    print("\n" + "=" * 50)
    print("PROCESO COMPLETADO")
    print("=" * 50)
    print(f"Archivos procesados exitosamente: {procesados}/{len(archivos_tiff)}")
    if errores > 0:
        print(f"Archivos con errores: {errores}")
    print(f"\nCarpetas de salida:")
    print(f"  - Gráficas: {carpeta_graficas}")
    print(f"  - Imágenes: {carpeta_imagenes} (1024x1024 píxeles)")
    print(f"  - Normalizadas: {carpeta_normalized} (0-255, 8-bit)")

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python script.py <ruta_carpeta>")
        print("Ejemplo: python script.py /ruta/a/mi/carpeta/con/tiffs")
        print("\nEste script genera tres tipos de salida:")
        print("  1. Gráficas con ejes y barra de color (carpeta 'graficas')")
        print("  2. Imágenes sin ejes (carpeta 'imagenes')")
        print("  3. Imágenes normalizadas por banda (carpeta 'normalized')")
        sys.exit(1)
    
    ruta_carpeta = sys.argv[1]
    procesar_carpeta_tiff(ruta_carpeta)

if __name__ == "__main__":
    main()