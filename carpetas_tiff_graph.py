import tifffile
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import sys
from pathlib import Path
import os

# Configurar encoding para Windows
if sys.platform == 'win32':
    import locale
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')

def procesar_carpeta_tiff(ruta_carpeta):
    """
    Procesa todos los archivos TIFF en una carpeta y genera:
    - Carpeta 'graficas': imágenes con ejes, título y barra de color
    - Carpeta 'imagenes': solo la imagen sin elementos adicionales
    Mantiene la resolución original de 1024x1024
    """
    
    carpeta = Path(ruta_carpeta)
    
    if not carpeta.exists() or not carpeta.is_dir():
        print(f"Error: La ruta '{ruta_carpeta}' no existe o no es una carpeta")
        return
    
    # Crear carpetas de salida
    carpeta_graficas = carpeta / 'graficas'
    carpeta_imagenes = carpeta / 'imagenes'
    
    carpeta_graficas.mkdir(exist_ok=True)
    carpeta_imagenes.mkdir(exist_ok=True)
    
    # Buscar todos los archivos TIFF
    archivos_tiff = list(carpeta.glob('*.tif')) + list(carpeta.glob('*.tiff'))
    
    if not archivos_tiff:
        print(f"No se encontraron archivos TIFF en {ruta_carpeta}")
        return
    
    print(f"Encontrados {len(archivos_tiff)} archivos TIFF")
    print(f"Procesando con resolucion nativa de 1024x1024...")
    
    # Configurar el mapa de color
    cmap_name = 'gist_heat'
    cmap = plt.colormaps[cmap_name].copy()
    cmap.set_bad('black')
    
    # Procesar cada archivo
    for i, archivo_tiff in enumerate(archivos_tiff, 1):
        try:
            print(f"  [{i}/{len(archivos_tiff)}] Procesando: {archivo_tiff.name}")
            
            # Leer la imagen
            data = tifffile.imread(archivo_tiff)
            
            # Verificar dimensiones
            height, width = data.shape
            print(f"    Dimensiones: {width}x{height}")
            
            # Obtener nombre base sin extensión
            nombre_base = archivo_tiff.stem
            
            # --- GENERAR GRÁFICA COMPLETA ---
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
            
            # --- GENERAR SOLO IMAGEN (1024x1024 exactos) ---
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
            
            # Usar caracteres ASCII en lugar de Unicode
            print(f"    [OK] Guardado: {nombre_base}")
            
        except Exception as e:
            # Usar caracteres ASCII en lugar de Unicode
            print(f"    [ERROR] Error procesando {archivo_tiff.name}: {str(e)}")
            continue
    
    print("\nProceso completado!")
    print(f"Graficas guardadas en: {carpeta_graficas}")
    print(f"Imagenes guardadas en: {carpeta_imagenes} (1024x1024 pixeles)")

def main():
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python script.py <ruta_carpeta>")
        print("Ejemplo: python script.py /ruta/a/mi/carpeta/con/tiffs")
        sys.exit(1)
    
    ruta_carpeta = sys.argv[1]
    procesar_carpeta_tiff(ruta_carpeta)

if __name__ == "__main__":
    main()