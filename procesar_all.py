#!/usr/bin/env python
"""
Script para procesar todas las carpetas TIFF incluyendo:
- Carpetas numeradas (01, 02, etc.) con subdirectorios during/before
- Carpeta especial 'quiet'
"""

import subprocess
import sys
from pathlib import Path
import time
from datetime import datetime

# ============================================
# CONFIGURACIÓN - MODIFICA SEGÚN TU SISTEMA
# ============================================
RUTA_BASE = r"C:\Users\resendizjg\Downloads\flares\tiffs"
SCRIPT = r"carpetas_tiff_graph.py"

# Carpetas especiales para procesar (además de las numeradas)
CARPETAS_ESPECIALES = ['quiet']

# Subcarpetas a buscar en carpetas numeradas
SUBCARPETAS_NUMERADAS = ['during', 'before']

# ============================================

class ColoresConsola:
    """Colores para hacer más legible la salida"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def deshabilitar():
        """Deshabilita colores en Windows si no son soportados"""
        ColoresConsola.HEADER = ''
        ColoresConsola.OKBLUE = ''
        ColoresConsola.OKCYAN = ''
        ColoresConsola.OKGREEN = ''
        ColoresConsola.WARNING = ''
        ColoresConsola.FAIL = ''
        ColoresConsola.ENDC = ''
        ColoresConsola.BOLD = ''
        ColoresConsola.UNDERLINE = ''

# En Windows, algunos terminales no soportan colores ANSI
if sys.platform == 'win32':
    try:
        import colorama
        colorama.init()
    except ImportError:
        ColoresConsola.deshabilitar()

def imprimir_encabezado():
    """Imprime el encabezado del programa"""
    print(f"{ColoresConsola.HEADER}{'='*70}{ColoresConsola.ENDC}")
    print(f"{ColoresConsola.HEADER}PROCESADOR AUTOMÁTICO DE CARPETAS TIFF (con carpeta QUIET){ColoresConsola.ENDC}")
    print(f"{ColoresConsola.HEADER}{'='*70}{ColoresConsola.ENDC}")
    print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ruta base: {RUTA_BASE}")
    print(f"Script: {SCRIPT}")
    print()

def ejecutar_script(carpeta, numero_actual, total):
    """
    Ejecuta el script para una carpeta específica
    """
    try:
        tipo = "📁 ESPECIAL" if carpeta.parent.name == RUTA_BASE.split('\\')[-1] else "📂 NUMERADA"
        print(f"\n[{numero_actual}/{total}] {tipo} Procesando: {carpeta}")
        print(f"  Ruta completa: {carpeta}")
        
        inicio = time.time()
        
        # Ejecutar el script
        resultado = subprocess.run(
            [sys.executable, SCRIPT, str(carpeta)],
            capture_output=True,
            text=True,
            check=True
        )
        
        tiempo = time.time() - inicio
        
        # Mostrar salida si hay
        if resultado.stdout:
            lineas = resultado.stdout.strip().split('\n')
            for linea in lineas[:5]:  # Mostrar primeras 5 líneas
                print(f"    {linea}")
            if len(lineas) > 5:
                print(f"    ... ({len(lineas)-5} líneas más)")
        
        print(f"{ColoresConsola.OKGREEN}  ✓ Completado en {tiempo:.2f} segundos{ColoresConsola.ENDC}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"{ColoresConsola.FAIL}  ✗ Error - Código de salida: {e.returncode}{ColoresConsola.ENDC}")
        if e.stderr:
            print(f"    Error: {e.stderr[:200]}")
        return False
    except FileNotFoundError:
        print(f"{ColoresConsola.FAIL}  ✗ No se encontró el script: {SCRIPT}{ColoresConsola.ENDC}")
        return False
    except Exception as e:
        print(f"{ColoresConsola.FAIL}  ✗ Error inesperado: {str(e)}{ColoresConsola.ENDC}")
        return False

def buscar_carpetas_a_procesar():
    """
    Busca todas las carpetas que necesitan ser procesadas
    """
    ruta_base = Path(RUTA_BASE)
    carpetas_a_procesar = []
    
    if not ruta_base.exists():
        print(f"{ColoresConsola.FAIL}Error: No existe la ruta base {RUTA_BASE}{ColoresConsola.ENDC}")
        return carpetas_a_procesar
    
    print(f"{ColoresConsola.BOLD}Buscando carpetas...{ColoresConsola.ENDC}")
    
    # 1. Buscar carpetas numeradas y sus subcarpetas
    carpetas_numeradas = []
    for carpeta in sorted(ruta_base.iterdir()):
        if carpeta.is_dir() and carpeta.name.isdigit():
            carpetas_numeradas.append(carpeta.name)
            for subcarpeta in SUBCARPETAS_NUMERADAS:
                ruta_sub = carpeta / subcarpeta
                if ruta_sub.exists():
                    carpetas_a_procesar.append(ruta_sub)
                    print(f"  ✓ Encontrada: {carpeta.name}/{subcarpeta}")
    
    if carpetas_numeradas:
        print(f"\n{ColoresConsola.OKCYAN}Carpetas numeradas encontradas: {', '.join(carpetas_numeradas)}{ColoresConsola.ENDC}")
    
    # 2. Buscar carpetas especiales
    print(f"\n{ColoresConsola.BOLD}Buscando carpetas especiales...{ColoresConsola.ENDC}")
    for especial in CARPETAS_ESPECIALES:
        carpeta_especial = ruta_base / especial
        if carpeta_especial.exists() and carpeta_especial.is_dir():
            carpetas_a_procesar.append(carpeta_especial)
            print(f"  ✓ Encontrada carpeta especial: {ColoresConsola.WARNING}{especial}{ColoresConsola.ENDC}")
        else:
            print(f"  ✗ No existe carpeta especial: {especial}")
    
    return carpetas_a_procesar

def mostrar_resumen(resultados):
    """
    Muestra un resumen detallado del procesamiento
    """
    print(f"\n{ColoresConsola.HEADER}{'='*70}{ColoresConsola.ENDC}")
    print(f"{ColoresConsola.HEADER}RESUMEN DEL PROCESAMIENTO{ColoresConsola.ENDC}")
    print(f"{ColoresConsola.HEADER}{'='*70}{ColoresConsola.ENDC}")
    
    total = len(resultados['exitosos']) + len(resultados['fallidos'])
    
    print(f"Total de carpetas procesadas: {total}")
    print(f"  {ColoresConsola.OKGREEN}✓ Exitosas: {len(resultados['exitosos'])}{ColoresConsola.ENDC}")
    print(f"  {ColoresConsola.FAIL}✗ Fallidas: {len(resultados['fallidos'])}{ColoresConsola.ENDC}")
    
    if resultados['exitosos']:
        print(f"\n{ColoresConsola.OKGREEN}Carpetas procesadas exitosamente:{ColoresConsola.ENDC}")
        for carpeta in resultados['exitosos']:
            tipo = "ESPECIAL" if Path(carpeta).name in CARPETAS_ESPECIALES else "NUMERADA"
            print(f"  ✓ [{tipo}] {carpeta}")
    
    if resultados['fallidos']:
        print(f"\n{ColoresConsola.FAIL}Carpetas con errores:{ColoresConsola.ENDC}")
        for carpeta in resultados['fallidos']:
            print(f"  ✗ {carpeta}")
    
    return total > 0

def main():
    """
    Función principal del programa
    """
    imprimir_encabezado()
    
    # Buscar carpetas
    carpetas = buscar_carpetas_a_procesar()
    
    if not carpetas:
        print(f"\n{ColoresConsola.WARNING}No se encontraron carpetas para procesar{ColoresConsola.ENDC}")
        return
    
    print(f"\n{ColoresConsola.BOLD}Total de carpetas a procesar: {len(carpetas)}{ColoresConsola.ENDC}")
    
    # Confirmar con el usuario
    print(f"\n{ColoresConsola.WARNING}¿Deseas continuar con el procesamiento? (s/n): {ColoresConsola.ENDC}", end='')
    respuesta = input().strip().lower()
    
    if respuesta != 's':
        print("Procesamiento cancelado por el usuario")
        return
    
    # Iniciar procesamiento
    print(f"\n{ColoresConsola.HEADER}INICIANDO PROCESAMIENTO...{ColoresConsola.ENDC}")
    inicio_total = time.time()
    
    resultados = {
        'exitosos': [],
        'fallidos': []
    }
    
    # Procesar cada carpeta
    for i, carpeta in enumerate(carpetas, 1):
        if ejecutar_script(carpeta, i, len(carpetas)):
            resultados['exitosos'].append(str(carpeta))
        else:
            resultados['fallidos'].append(str(carpeta))
        
        # Pequeña pausa entre procesos
        if i < len(carpetas):
            time.sleep(0.5)
    
    # Mostrar resumen
    tiempo_total = time.time() - inicio_total
    if mostrar_resumen(resultados):
        print(f"\n{ColoresConsola.BOLD}Tiempo total de procesamiento: {tiempo_total:.2f} segundos{ColoresConsola.ENDC}")
        print(f"Tiempo promedio por carpeta: {tiempo_total/len(carpetas):.2f} segundos")
    
    print(f"\n{ColoresConsola.HEADER}{'='*70}{ColoresConsola.ENDC}")
    print(f"{ColoresConsola.OKGREEN}Proceso completado{ColoresConsola.ENDC}")
    print(f"{ColoresConsola.HEADER}{'='*70}{ColoresConsola.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{ColoresConsola.WARNING}Proceso interrumpido por el usuario{ColoresConsola.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{ColoresConsola.FAIL}Error crítico: {e}{ColoresConsola.ENDC}")
        sys.exit(1)