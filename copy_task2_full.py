import os
import shutil

def consolidar_todos_los_tiffs():
    """
    Consolida todos los archivos TIFF de todas las carpetas before_png en una sola carpeta
    """
    
    # Ruta base donde están las carpetas 01, 02, 03, etc.
    ruta_base = r"C:\Users\resendizjg\Downloads\tiffs_no_background\tiffs_no_background"
    
    # Carpeta destino donde se consolidarán TODOS los TIFFs
    carpeta_consolidada = os.path.join(ruta_base, "todos_los_tiffs")
    
    # Crear carpeta destino
    os.makedirs(carpeta_consolidada, exist_ok=True)
    
    print(f"Consolidando todos los TIFFs en:\n{carpeta_consolidada}\n")
    print("="*60)
    
    total_archivos = 0
    carpetas_procesadas = 0
    
    # Buscar en cada carpeta numerada
    for carpeta_num in sorted(os.listdir(ruta_base)):
        carpeta_path = os.path.join(ruta_base, carpeta_num)
        
        # Saltar si no es directorio o si es la carpeta de consolidación
        if not os.path.isdir(carpeta_path) or carpeta_num == "todos_los_tiffs":
            continue
        
        # Buscar carpeta before_png dentro de cada carpeta numerada
        before_png_path = os.path.join(carpeta_path, "before_png")
        
        if os.path.exists(before_png_path):
            print(f"\nProcesando: {carpeta_num}/before_png")
            archivos_carpeta = 0
            
            # Copiar todos los TIFFs de esta carpeta
            for archivo in os.listdir(before_png_path):
                if archivo.lower().endswith('.tiff') or archivo.lower().endswith('.tif'):
                    origen = os.path.join(before_png_path, archivo)
                    
                    # Agregar prefijo para evitar duplicados (ej: 01_archivo.tiff)
                    nuevo_nombre = f"{carpeta_num}_{archivo}"
                    destino = os.path.join(carpeta_consolidada, nuevo_nombre)
                    
                    try:
                        shutil.copy2(origen, destino)
                        archivos_carpeta += 1
                        total_archivos += 1
                        print(f"  ✓ {archivo}")
                    except Exception as e:
                        print(f"  ✗ Error con {archivo}: {str(e)}")
            
            if archivos_carpeta > 0:
                print(f"  → {archivos_carpeta} archivos copiados")
                carpetas_procesadas += 1
        else:
            print(f"- No existe: {carpeta_num}/before_png")
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    print(f"Carpetas procesadas: {carpetas_procesadas}")
    print(f"Total de archivos TIFF consolidados: {total_archivos}")
    print(f"\n✓ Todos los TIFFs están en:\n  {carpeta_consolidada}")

# Versión alternativa sin prefijos si no hay duplicados
def consolidar_tiffs_sin_prefijo():
    """
    Consolida sin agregar prefijos (usar solo si no hay nombres duplicados)
    """
    
    ruta_base = r"C:\Users\resendizjg\Downloads\tiffs_no_background\tiffs_no_background"
    carpeta_consolidada = os.path.join(ruta_base, "todos_los_tiffs_sin_prefijo")
    
    os.makedirs(carpeta_consolidada, exist_ok=True)
    
    print(f"Consolidando TIFFs sin prefijos en:\n{carpeta_consolidada}\n")
    
    total_archivos = 0
    duplicados = 0
    
    for carpeta_num in sorted(os.listdir(ruta_base)):
        carpeta_path = os.path.join(ruta_base, carpeta_num)
        
        if not os.path.isdir(carpeta_path) or "todos_los_tiffs" in carpeta_num:
            continue
        
        before_png_path = os.path.join(carpeta_path, "before_png")
        
        if os.path.exists(before_png_path):
            for archivo in os.listdir(before_png_path):
                if archivo.lower().endswith(('.tiff', '.tif')):
                    origen = os.path.join(before_png_path, archivo)
                    destino = os.path.join(carpeta_consolidada, archivo)
                    
                    # Verificar si ya existe
                    if os.path.exists(destino):
                        print(f"⚠ Duplicado encontrado: {archivo} (carpeta {carpeta_num})")
                        duplicados += 1
                        # Renombrar con prefijo solo los duplicados
                        destino = os.path.join(carpeta_consolidada, f"{carpeta_num}_{archivo}")
                    
                    try:
                        shutil.copy2(origen, destino)
                        total_archivos += 1
                    except Exception as e:
                        print(f"Error: {str(e)}")
    
    print(f"\n✓ Total consolidados: {total_archivos}")
    if duplicados > 0:
        print(f"⚠ Se encontraron {duplicados} duplicados (se agregó prefijo)")

if __name__ == "__main__":
    print("="*60)
    print("CONSOLIDADOR DE ARCHIVOS TIFF")
    print("="*60)
    
    print("\n¿Cómo quieres consolidar?")
    print("1. Con prefijos (01_archivo.tiff) - Recomendado")
    print("2. Sin prefijos (archivo.tiff) - Solo si no hay duplicados")
    print("3. Cancelar")
    
    opcion = input("\nElige (1/2/3): ").strip()
    
    if opcion == '1':
        consolidar_todos_los_tiffs()
    elif opcion == '2':
        consolidar_tiffs_sin_prefijo()
    else:
        print("Cancelado.")