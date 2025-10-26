import tifffile
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
import sys

def normalizar_para_ml(data, metodo='zscore', stats_banda=None):
    """
    Normaliza datos para modelo de ML
    
    Métodos:
    - 'zscore': (x - mean) / std
    - 'minmax': (x - min) / (max - min)
    - 'robust': (x - median) / (p75 - p25)
    """
    valid_data = data[np.isfinite(data)]
    
    if len(valid_data) == 0:
        return np.zeros_like(data)
    
    if metodo == 'zscore':
        if stats_banda and 'mean' in stats_banda and 'std' in stats_banda:
            # Usar estadísticas globales de la banda
            mean = stats_banda['mean']
            std = stats_banda['std']
        else:
            # Calcular localmente
            mean = np.mean(valid_data)
            std = np.std(valid_data)
        
        if std == 0:
            std = 1
        
        data_norm = (data - mean) / std
        # Típicamente clipear a [-3, 3] para z-score
        data_norm = np.clip(data_norm, -3, 3)
        # Escalar a [0, 1]
        data_norm = (data_norm + 3) / 6
        
    elif metodo == 'minmax':
        if stats_banda and 'min' in stats_banda and 'max' in stats_banda:
            vmin = stats_banda['min']
            vmax = stats_banda['max']
        else:
            vmin = np.percentile(valid_data, 1)
            vmax = np.percentile(valid_data, 99)
        
        if vmax == vmin:
            vmax = vmin + 1
        
        data_norm = (data - vmin) / (vmax - vmin)
        data_norm = np.clip(data_norm, 0, 1)
        
    elif metodo == 'robust':
        # Robusto a outliers
        median = np.median(valid_data)
        p25 = np.percentile(valid_data, 25)
        p75 = np.percentile(valid_data, 75)
        iqr = p75 - p25
        
        if iqr == 0:
            iqr = 1
        
        data_norm = (data - median) / iqr
        # Clipear a rango razonable
        data_norm = np.clip(data_norm, -3, 3)
        # Escalar a [0, 1]
        data_norm = (data_norm + 3) / 6
    
    # Reemplazar NaN con 0
    data_norm = np.nan_to_num(data_norm, nan=0.0)
    
    return data_norm

def procesar_para_cv(archivo_tiff, metodo_norm='zscore'):
    """
    Procesa un archivo TIFF para computer vision
    """
    
    # Leer datos
    data = tifffile.imread(archivo_tiff).astype(np.float32)
    
    # Detectar banda
    nombre = Path(archivo_tiff).stem
    banda = None
    for b in ['0131', '0171', '0193', '0211', '0304', '0335', '0094', '1600', '1700']:
        if b in nombre:
            banda = b
            break
    
    print(f"Procesando: {nombre}")
    print(f"Banda: {banda}")
    print(f"Método normalización: {metodo_norm}")
    
    # Normalizar
    data_norm = normalizar_para_ml(data, metodo=metodo_norm)
    
    # Estadísticas
    print(f"Rango original: [{np.min(data):.3f}, {np.max(data):.3f}]")
    print(f"Rango normalizado: [{np.min(data_norm):.3f}, {np.max(data_norm):.3f}]")
    print(f"Media normalizada: {np.mean(data_norm):.3f}")
    print(f"Std normalizada: {np.std(data_norm):.3f}")
    
    return data_norm, banda

def main():
    if len(sys.argv) < 2:
        print("Uso: python script.py <archivo.tiff>")
        sys.exit()
    
    archivo = sys.argv[1]
    
    # Procesar para ML
    data_norm, banda = procesar_para_cv(archivo, metodo_norm='zscore')
    
    # Visualizar comparación
    data_original = tifffile.imread(archivo).astype(np.float32)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Original con escala automática
    im1 = axes[0, 0].imshow(data_original, cmap='gray', origin='lower')
    axes[0, 0].set_title(f'Original\nRango: [{np.min(data_original):.1f}, {np.max(data_original):.1f}]')
    plt.colorbar(im1, ax=axes[0, 0])
    
    # Normalizado [0, 1]
    im2 = axes[0, 1].imshow(data_norm, cmap='gray', origin='lower', vmin=0, vmax=1)
    axes[0, 1].set_title(f'Normalizado [0, 1]\nBanda: {banda}')
    plt.colorbar(im2, ax=axes[0, 1])
    
    # Histogramas
    axes[1, 0].hist(data_original.flatten()[::100], bins=50, color='blue', alpha=0.7)
    axes[1, 0].set_title('Distribución original')
    axes[1, 0].set_ylabel('Frecuencia')
    axes[1, 0].set_xlabel('Valor')
    axes[1, 0].set_yscale('log')
    
    axes[1, 1].hist(data_norm.flatten()[::100], bins=50, color='green', alpha=0.7)
    axes[1, 1].set_title('Distribución normalizada')
    axes[1, 1].set_ylabel('Frecuencia')
    axes[1, 1].set_xlabel('Valor normalizado [0, 1]')
    axes[1, 1].axvline(0.5, color='red', linestyle='--', label='Centro')
    axes[1, 1].legend()
    
    plt.suptitle(f'Normalización para Computer Vision\n{Path(archivo).name}')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()