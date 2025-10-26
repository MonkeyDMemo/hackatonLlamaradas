import subprocess
import sys
from pathlib import Path
import os

# Configurar encoding para Windows
if sys.platform == 'win32':
    import locale
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass  # Si falla, continuamos con encoding por defecto

def procesar_todas_carpetas(ruta_base):
    """
    Procesa todas las carpetas numeradas (01, 02, 03, etc.) 
    y sus subcarpetas 'before' y 'during'
    """
    ruta_base = Path(ruta_base)
    
    if not ruta_base.exists():
        print(f"Error: La ruta '{ruta_base}' no existe")
        return
    
    # Buscar todas las carpetas numeradas
    carpetas_numeradas = sorted([d for d in ruta_base.iterdir() 
                                 if d.is_dir() and d.name.isdigit()])
    
    if not carpetas_numeradas:
        print("No se encontraron carpetas numeradas (01, 02, etc.)")
        return
    
    print(f"Encontradas {len(carpetas_numeradas)} carpetas numeradas")
    print(f"Usando Python del venv: {sys.executable}")
    print("=" * 50)
    
    total_procesadas = 0
    carpetas_exitosas = []
    carpetas_fallidas = []
    
    for carpeta_num in carpetas_numeradas:
        print(f"\nProcesando carpeta: {carpeta_num.name}")
        print("-" * 30)
        
        for subcarpeta in ['before', 'during']:
            ruta_completa = carpeta_num / subcarpeta
            
            if ruta_completa.exists():
                print(f"  -> Procesando {carpeta_num.name}/{subcarpeta}")
                
                # Usar sys.executable para el Python del venv
                comando = [
                    sys.executable,
                    'carpetas_tiff_graph_con_normalizacion.py',
                    str(ruta_completa)
                ]
                
                try:
                    resultado = subprocess.run(
                        comando,
                        capture_output=True,
                        text=True,
                        check=True,
                        encoding='utf-8',  # Especificar encoding
                        errors='replace'   # Reemplazar caracteres problemáticos
                    )
                    
                    print(f"    [OK] Completado: {carpeta_num.name}/{subcarpeta}")
                    carpetas_exitosas.append(f"{carpeta_num.name}/{subcarpeta}")
                    total_procesadas += 1
                    
                    # Mostrar output si hay
                    if resultado.stdout:
                        lineas = resultado.stdout.split('\n')
                        # Mostrar solo información relevante
                        for linea in lineas:
                            if 'Encontrados' in linea or 'Proceso completado' in linea:
                                print(f"      {linea.strip()}")
                    
                except subprocess.CalledProcessError as e:
                    print(f"    [ERROR] Error en: {carpeta_num.name}/{subcarpeta}")
                    carpetas_fallidas.append(f"{carpeta_num.name}/{subcarpeta}")
                    if e.stderr:
                        # Mostrar solo la primera línea del error
                        error_lines = e.stderr.split('\n')
                        if error_lines:
                            print(f"      Detalles: {error_lines[0][:100]}")
                
            else:
                print(f"  [!] No existe: {carpeta_num.name}/{subcarpeta}")
    
    # Resumen
    print("\n" + "=" * 50)
    print("RESUMEN DEL PROCESO")
    print("=" * 50)
    print(f"[OK] Procesadas exitosamente: {len(carpetas_exitosas)}")
    
    if carpetas_exitosas:
        print("\nCarpetas procesadas:")
        for carpeta in carpetas_exitosas[:10]:  # Mostrar solo las primeras 10
            print(f"  - {carpeta}")
        if len(carpetas_exitosas) > 10:
            print(f"  ... y {len(carpetas_exitosas) - 10} mas")
    
    if carpetas_fallidas:
        print(f"\n[ERROR] Carpetas con errores: {len(carpetas_fallidas)}")
        for carpeta in carpetas_fallidas:
            print(f"  - {carpeta}")
    
    print(f"\n[TOTAL] {total_procesadas} carpetas procesadas")

def main():
    if len(sys.argv) < 2:
        print("Uso: python run_subprocess.py <ruta_base>")
        print('Ejemplo: python run_subprocess.py "C:\\Users\\resendizjg\\Downloads\\flares\\tiffs"')
        sys.exit(1)
    
    # Verificar dependencias
    print("Verificando dependencias...")
    try:
        import tifffile
        import matplotlib
        import PIL
        import numpy
        print("  [OK] Todas las dependencias instaladas\n")
    except ImportError as e:
        print(f"  [ERROR] Falta instalar: {e}")
        print("  Ejecuta: pip install tifffile matplotlib pillow numpy")
        sys.exit(1)
    
    ruta_base = sys.argv[1]
    procesar_todas_carpetas(ruta_base)

if __name__ == "__main__":
    main()