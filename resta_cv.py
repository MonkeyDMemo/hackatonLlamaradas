import cv2
import numpy as np
from skimage import io
import matplotlib.pyplot as plt

def detectar_regiones_activas(imagen_path, fondo_path, umbral=10, area_minima=50):
    """
    Detecta regiones activas restando imagen de fondo
    
    Args:
        imagen_path: ruta a imagen TIF con actividad
        fondo_path: ruta a imagen TIF de referencia/fondo
        umbral: valor mínimo de diferencia para considerar activo
        area_minima: área mínima en píxeles para considerar región válida
    """
    
    # Cargar imágenes TIF (preservando profundidad de bits)
    imagen = io.imread(imagen_path)
    fondo = io.imread(fondo_path)
    
    print(f"Imagen shape: {imagen.shape}, dtype: {imagen.dtype}")
    print(f"Rango imagen: [{imagen.min()}, {imagen.max()}]")
    
    # Si las imágenes son de 16 bits, convertir a float para mejor precisión
    if imagen.dtype == np.uint16:
        imagen = imagen.astype(np.float32)
        fondo = fondo.astype(np.float32)
    
    # Realizar la resta
    diferencia = cv2.subtract(imagen, fondo)
    
    # Alternativa: resta con valor absoluto si hay regiones que disminuyen
    # diferencia = cv2.absdiff(imagen, fondo)
    
    # Si quieres solo incrementos (regiones que aumentaron):
    diferencia_positiva = np.where(imagen > fondo, imagen - fondo, 0)
    
    # Normalizar para visualización y análisis
    diff_norm = cv2.normalize(diferencia_positiva, None, 0, 255, cv2.NORM_MINMAX)
    diff_norm = diff_norm.astype(np.uint8)
    
    # Aplicar umbral adaptativo o fijo
    _, mascara = cv2.threshold(diff_norm, umbral, 255, cv2.THRESH_BINARY)
    
    # Limpiar ruido con operaciones morfológicas
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contornos de regiones activas
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, 
                                     cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrar por área mínima
    regiones_validas = []
    for contorno in contornos:
        area = cv2.contourArea(contorno)
        if area >= area_minima:
            regiones_validas.append(contorno)
    
    # Crear imagen de salida con regiones marcadas
    resultado = cv2.cvtColor(diff_norm, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(resultado, regiones_validas, -1, (0, 255, 0), 2)
    
    # Calcular estadísticas
    estadisticas = calcular_estadisticas(diferencia_positiva, mascara, regiones_validas)
    
    return diferencia_positiva, mascara, resultado, regiones_validas, estadisticas

def calcular_estadisticas(diferencia, mascara, contornos):
    """Calcula estadísticas de las regiones activas"""
    
    stats = {
        'num_regiones': len(contornos),
        'intensidad_media': np.mean(diferencia[mascara > 0]) if np.any(mascara > 0) else 0,
        'intensidad_max': np.max(diferencia) if np.any(diferencia > 0) else 0,
        'area_total_activa': np.sum(mascara > 0),
        'regiones': []
    }
    
    for i, contorno in enumerate(contornos):
        # Crear máscara para esta región específica
        mask_region = np.zeros(mascara.shape, np.uint8)
        cv2.drawContours(mask_region, [contorno], -1, 255, -1)
        
        # Calcular propiedades
        area = cv2.contourArea(contorno)
        x, y, w, h = cv2.boundingRect(contorno)
        intensidad_media = np.mean(diferencia[mask_region > 0])
        intensidad_max = np.max(diferencia[mask_region > 0])
        
        # Calcular centroide
        M = cv2.moments(contorno)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + w//2, y + h//2
        
        stats['regiones'].append({
            'id': i + 1,
            'area': area,
            'bbox': (x, y, w, h),
            'centroide': (cx, cy),
            'intensidad_media': intensidad_media,
            'intensidad_max': intensidad_max
        })
    
    return stats

def visualizar_resultados(imagen, fondo, diferencia, mascara, resultado, stats):
    """Visualiza todos los resultados en una figura"""
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Imagen original
    axes[0, 0].imshow(imagen, cmap='gray')
    axes[0, 0].set_title('Imagen Original')
    axes[0, 0].axis('off')
    
    # Fondo
    axes[0, 1].imshow(fondo, cmap='gray')
    axes[0, 1].set_title('Fondo/Referencia')
    axes[0, 1].axis('off')
    
    # Diferencia
    im = axes[0, 2].imshow(diferencia, cmap='hot')
    axes[0, 2].set_title('Diferencia (Regiones Activas)')
    axes[0, 2].axis('off')
    plt.colorbar(im, ax=axes[0, 2])
    
    # Máscara binaria
    axes[1, 0].imshow(mascara, cmap='gray')
    axes[1, 0].set_title(f'Máscara ({stats["num_regiones"]} regiones)')
    axes[1, 0].axis('off')
    
    # Resultado con contornos
    axes[1, 1].imshow(resultado)
    axes[1, 1].set_title('Regiones Detectadas')
    axes[1, 1].axis('off')
    
    # Mostrar estadísticas
    axes[1, 2].axis('off')
    texto = f"Estadísticas:\n"
    texto += f"Regiones encontradas: {stats['num_regiones']}\n"
    texto += f"Área total activa: {stats['area_total_activa']} px\n"
    texto += f"Intensidad media: {stats['intensidad_media']:.2f}\n"
    texto += f"Intensidad máxima: {stats['intensidad_max']:.2f}\n\n"
    
    if stats['num_regiones'] > 0:
        texto += "Top 5 regiones (por área):\n"
        regiones_ordenadas = sorted(stats['regiones'], 
                                   key=lambda x: x['area'], 
                                   reverse=True)[:5]
        for r in regiones_ordenadas:
            texto += f"ID {r['id']}: {r['area']:.0f} px, "
            texto += f"Int: {r['intensidad_media']:.1f}\n"
    
    axes[1, 2].text(0.1, 0.5, texto, fontsize=10, verticalalignment='center')
    
    plt.tight_layout()
    plt.show()

# Función principal de uso
def procesar_imagenes_tif(imagen_path, fondo_path, 
                         umbral=10, area_minima=50,
                         guardar_resultados=True):
    """
    Proceso completo para detectar regiones activas
    """
    
    # Ejecutar detección
    diferencia, mascara, resultado, contornos, stats = detectar_regiones_activas(
        imagen_path, fondo_path, umbral, area_minima
    )
    
    # Visualizar
    imagen = io.imread(imagen_path)
    fondo = io.imread(fondo_path)
    visualizar_resultados(imagen, fondo, diferencia, mascara, resultado, stats)
    
    # Guardar resultados si se requiere
    if guardar_resultados:
        # Guardar diferencia como TIF de 32 bits para preservar valores
        io.imsave('diferencia_activas.tif', diferencia.astype(np.float32))
        
        # Guardar máscara
        cv2.imwrite('mascara_regiones.png', mascara)
        
        # Guardar resultado con contornos
        cv2.imwrite('regiones_detectadas.png', resultado)
        
        # Guardar estadísticas
        import json
        with open('estadisticas_regiones.json', 'w') as f:
            # Convertir arrays numpy a listas para JSON
            stats_json = stats.copy()
            for region in stats_json['regiones']:
                region['bbox'] = list(region['bbox'])
                region['centroide'] = list(region['centroide'])
                region['intensidad_media'] = float(region['intensidad_media'])
                region['intensidad_max'] = float(region['intensidad_max'])
            json.dump(stats_json, f, indent=2)
        
        print("\nResultados guardados:")
        print("- diferencia_activas.tif")
        print("- mascara_regiones.png")
        print("- regiones_detectadas.png")
        print("- estadisticas_regiones.json")
    
    return diferencia, mascara, contornos, stats

# USO
if __name__ == "__main__":
    # Rutas a tus imágenes
    imagen_activa = r"C:\Users\resendizjg\Downloads\flares\tiffs\01\during\AIA20140225_0042_0131.tiff"
    imagen_fondo = r"C:\Users\resendizjg\Downloads\quite_average-131.tif"
    
    # Procesar con parámetros ajustables
    diff, mask, contornos, estadisticas = procesar_imagenes_tif(
        imagen_activa,
        imagen_fondo,
        umbral=10,  # Ajusta según el ruido de tus imágenes
        area_minima=50,  # Píxeles mínimos para considerar región válida
        guardar_resultados=True
    )
    
    # Imprimir resumen
    print(f"\n✓ Detectadas {estadisticas['num_regiones']} regiones activas")
    print(f"✓ Área total activa: {estadisticas['area_total_activa']} píxeles")
    print(f"✓ Intensidad promedio en regiones: {estadisticas['intensidad_media']:.2f}")