from inference import get_model
import cv2
from pathlib import Path
from datetime import datetime

# Configuración
API_KEY = "cygTL33SntK8etDjvyVD"
MODEL_ID = "llamaradas-v2-h7wcc/3"
IMAGE_FILE = r"C:\Users\resendizjg\Downloads\AIA20140104_1916_0193_diff (1).png"

# Crear carpeta de resultados
output_folder = Path("front_resultados")
output_folder.mkdir(exist_ok=True)

# Ejecutar
image = cv2.imread(IMAGE_FILE)
model = get_model(model_id=MODEL_ID, api_key=API_KEY)
results = model.infer(image)

# Obtener resultado
if isinstance(results, list):
    result = results[0]
else:
    result = results

# Mostrar predicciones
print("\nRESULTADOS:")
prediction_text = ""
if hasattr(result, 'predictions'):
    for pred in result.predictions:
        text = f"{pred.class_name}: {pred.confidence:.1%}"
        print(f"  {text}")
        prediction_text = text  # Guardar la predicción principal

# Agregar texto a la imagen
image_with_text = image.copy()
cv2.putText(image_with_text, prediction_text, (30, 50), 
           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

# Guardar imagen con resultado
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = output_folder / f"resultado_{timestamp}.jpg"
cv2.imwrite(str(output_path), image_with_text)

print(f"\n✅ Imagen guardada: {output_path}")

# También guardar imagen original
original_path = output_folder / f"original_{timestamp}.jpg"
cv2.imwrite(str(original_path), image)
print(f"✅ Original guardada: {original_path}")

# Mostrar imagen (opcional)
cv2.imshow("Resultado", image_with_text)
print("\nPresiona cualquier tecla para cerrar...")
cv2.waitKey(0)
cv2.destroyAllWindows()