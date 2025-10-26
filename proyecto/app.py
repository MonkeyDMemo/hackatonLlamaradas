from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import cv2
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from inference import get_model
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)

# Configuración
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Crear carpetas necesarias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Configuración Roboflow
API_KEY = "cygTL33SntK8etDjvyVD"
MODEL_ID = "llamaradas-v2-h7wcc/5"

# Rutas de imágenes de fondo (ajusta estas rutas)
FONDO_131_PATH = r"C:\Users\resendizjg\Downloads\quite_average-131.tif"
FONDO_193_PATH = r"C:\Users\resendizjg\Downloads\quite_average-193.tif"

# Cargar fondos al iniciar
print("Cargando imágenes de fondo...")
FONDO_131 = cv2.imread(FONDO_131_PATH, cv2.IMREAD_UNCHANGED) if os.path.exists(FONDO_131_PATH) else None
FONDO_193 = cv2.imread(FONDO_193_PATH, cv2.IMREAD_UNCHANGED) if os.path.exists(FONDO_193_PATH) else None

if FONDO_131 is not None:
    print(f"Fondo 131 cargado: {FONDO_131.shape}, tipo: {FONDO_131.dtype}")
else:
    print("⚠️ No se pudo cargar fondo 131")
    
if FONDO_193 is not None:
    print(f"Fondo 193 cargado: {FONDO_193.shape}, tipo: {FONDO_193.dtype}")
else:
    print("⚠️ No se pudo cargar fondo 193")

@app.route('/')
def index():
    return render_template('index.html')

def detectar_tipo_imagen(filename):
    """Detecta si es imagen 131 o 193 basándose en el nombre"""
    filename_lower = filename.lower()
    if '_0131' in filename_lower or '131' in filename_lower:
        return '131'
    elif '_0193' in filename_lower or '193' in filename_lower:
        return '193'
    return None

def convertir_tiff_a_png(imagen_tiff):
    """
    Convierte una imagen TIFF a formato PNG escalando para mejor visualización
    Basado en tu función original
    """
    # Escalar a 0-255 para mejor visualización en PNG
    img_min = imagen_tiff.min()
    img_max = imagen_tiff.max()
    
    if img_max > img_min:
        imagen_escalada = ((imagen_tiff - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    else:
        imagen_escalada = np.zeros_like(imagen_tiff, dtype=np.uint8)
    
    return imagen_escalada

def procesar_resta_fondo(imagen, fondo):
    """Procesa la resta de fondo manejando diferentes tipos de datos"""
    try:
        # Asegurar que ambas imágenes tengan el mismo tipo de datos
        if imagen.dtype != fondo.dtype:
            print(f"Convirtiendo tipos: imagen={imagen.dtype}, fondo={fondo.dtype}")
            
            # Convertir ambos a float32 para la operación
            imagen_float = imagen.astype(np.float32)
            fondo_float = fondo.astype(np.float32)
            
            # Realizar la resta
            diferencia = imagen_float - fondo_float
            
            # Asegurar que no hay valores negativos
            diferencia = np.clip(diferencia, 0, None)
            
        else:
            # Si tienen el mismo tipo, usar cv2.subtract directamente
            diferencia = cv2.subtract(imagen, fondo)
        
        return diferencia
        
    except Exception as e:
        print(f"Error en resta de fondo: {e}")
        raise

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        # Detectar tipo de imagen por nombre
        tipo_detectado = detectar_tipo_imagen(file.filename)
        
        # Si no se puede detectar por nombre, usar el parámetro del formulario
        if tipo_detectado is None:
            tipo_detectado = request.form.get('wavelength', '131')
        
        print(f"\n{'='*60}")
        print(f"Procesando imagen: {file.filename}")
        print(f"Tipo detectado: {tipo_detectado} Å")
        print(f"{'='*60}")
        
        # Guardar archivo original
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(file.filename)
        base_name = Path(filename).stem
        
        # Guardar archivo subido
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(upload_path)
        
        # Leer imagen TIFF manteniendo su profundidad de bits original
        imagen = cv2.imread(upload_path, cv2.IMREAD_UNCHANGED)
        if imagen is None:
            return jsonify({'error': 'No se pudo leer la imagen'}), 400
        
        print(f"Imagen cargada: shape={imagen.shape}, dtype={imagen.dtype}, rango=[{imagen.min()}, {imagen.max()}]")
        
        # PASO 1: Convertir TIFF a PNG para la imagen original
        imagen_original_png = convertir_tiff_a_png(imagen)
        original_png_filename = f"{timestamp}_{base_name}_original.png"
        original_png_path = os.path.join(app.config['RESULTS_FOLDER'], original_png_filename)
        cv2.imwrite(original_png_path, imagen_original_png)
        print(f"✓ Original convertida a PNG: {original_png_filename}")
        
        # Seleccionar fondo según tipo detectado
        if tipo_detectado == '131':
            fondo = FONDO_131
            if fondo is None:
                return jsonify({'error': 'Imagen de fondo 131 no disponible'}), 500
        else:
            fondo = FONDO_193
            if fondo is None:
                return jsonify({'error': 'Imagen de fondo 193 no disponible'}), 500
        
        print(f"Usando fondo {tipo_detectado}: shape={fondo.shape}, dtype={fondo.dtype}")
        
        # Verificar y ajustar dimensiones si es necesario
        if imagen.shape[:2] != fondo.shape[:2]:
            print(f"Ajustando dimensiones: {imagen.shape} -> {fondo.shape}")
            imagen = cv2.resize(imagen, (fondo.shape[1], fondo.shape[0]))
        
        # PASO 2: Aplicar resta de fondo
        diferencia = procesar_resta_fondo(imagen, fondo)
        print(f"Resta de fondo calculada: shape={diferencia.shape}, dtype={diferencia.dtype}, rango=[{diferencia.min():.2f}, {diferencia.max():.2f}]")
        
        # PASO 3: Convertir diferencia a PNG
        diferencia_png = convertir_tiff_a_png(diferencia)
        processed_filename = f"{timestamp}_{base_name}_diff_{tipo_detectado}.png"
        processed_path = os.path.join(app.config['RESULTS_FOLDER'], processed_filename)
        cv2.imwrite(processed_path, diferencia_png)
        print(f"✓ Diferencia guardada como PNG: {processed_filename}")
        
        # PASO 4: Preparar imagen para Roboflow (necesita RGB)
        print("\nEjecutando modelo Roboflow...")
        
        # Convertir a RGB si es escala de grises
        if len(diferencia_png.shape) == 2:
            imagen_para_modelo = cv2.cvtColor(diferencia_png, cv2.COLOR_GRAY2RGB)
            print(f"Convertido a RGB para modelo: {imagen_para_modelo.shape}")
        else:
            imagen_para_modelo = diferencia_png
        
        # Ejecutar modelo
        model = get_model(model_id=MODEL_ID, api_key=API_KEY)
        results = model.infer(imagen_para_modelo)
        
        # Procesar resultados
        predictions = []
        if isinstance(results, list):
            result = results[0]
        else:
            result = results
        
        if hasattr(result, 'predictions'):
            for pred in result.predictions:
                predictions.append({
                    'class': pred.class_name,
                    'confidence': float(pred.confidence)
                })
                print(f"  Predicción: {pred.class_name} - {pred.confidence:.2%}")
        
        # PASO 5: Crear imagen anotada
        # Convertir a BGR para poder agregar texto en color
        if len(diferencia_png.shape) == 2:
            annotated = cv2.cvtColor(diferencia_png, cv2.COLOR_GRAY2BGR)
        else:
            annotated = diferencia_png.copy()
        
        if predictions:
            # Agregar texto con la predicción principal
            main_pred = max(predictions, key=lambda x: x['confidence'])
            text = f"{main_pred['class']}: {main_pred['confidence']:.1%}"
            
            # Agregar fondo al texto para mejor visibilidad
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1
            thickness = 2
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Rectángulo de fondo
            cv2.rectangle(annotated, (20, 20), (30 + text_width, 60), (0, 0, 0), -1)
            # Texto principal
            cv2.putText(annotated, text, (30, 50), font, font_scale, (0, 255, 0), thickness)
            
            # Agregar tipo de imagen
            tipo_text = f"Wavelength: {tipo_detectado} A"
            cv2.putText(annotated, tipo_text, (30, 90), font, 0.7, (255, 255, 255), 1)
        
        # Guardar imagen anotada
        annotated_filename = f"{timestamp}_{base_name}_annotated_{tipo_detectado}.png"
        annotated_path = os.path.join(app.config['RESULTS_FOLDER'], annotated_filename)
        cv2.imwrite(annotated_path, annotated)
        print(f"✓ Imagen anotada guardada: {annotated_filename}")
        
        # Preparar respuesta
        response = {
            'success': True,
            'original': f"/results/{original_png_filename}",
            'processed': f"/results/{processed_filename}",
            'annotated': f"/results/{annotated_filename}",
            'predictions': predictions,
            'timestamp': timestamp,
            'wavelength': tipo_detectado,
            'image_info': {
                'original_shape': imagen.shape,
                'detected_wavelength': tipo_detectado,
                'min_value': float(imagen.min()),
                'max_value': float(imagen.max()),
                'dtype': str(imagen.dtype)
            }
        }
        
        print(f"\n{'='*60}")
        print("✓ Proceso completado exitosamente")
        print(f"  - Original PNG: {original_png_filename}")
        print(f"  - Diferencia PNG: {processed_filename}")
        print(f"  - Anotada PNG: {annotated_filename}")
        print(f"  - Predicciones: {len(predictions)}")
        print(f"{'='*60}\n")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/results/<filename>')
def result_file(filename):
    return send_from_directory(app.config['RESULTS_FOLDER'], filename)

@app.route('/check_backgrounds')
def check_backgrounds():
    """Endpoint para verificar el estado de las imágenes de fondo"""
    return jsonify({
        'fondo_131': {
            'loaded': FONDO_131 is not None,
            'shape': FONDO_131.shape if FONDO_131 is not None else None,
            'dtype': str(FONDO_131.dtype) if FONDO_131 is not None else None
        },
        'fondo_193': {
            'loaded': FONDO_193 is not None,
            'shape': FONDO_193.shape if FONDO_193 is not None else None,
            'dtype': str(FONDO_193.dtype) if FONDO_193 is not None else None
        }
    })

if __name__ == '__main__':
    print("="*60)
    print("SERVIDOR DE DETECCIÓN DE LLAMARADAS SOLARES")
    print("="*60)
    print(f"Fondo 131 cargado: {FONDO_131 is not None}")
    if FONDO_131 is not None:
        print(f"  - Dimensiones: {FONDO_131.shape}")
        print(f"  - Tipo de datos: {FONDO_131.dtype}")
    
    print(f"Fondo 193 cargado: {FONDO_193 is not None}")
    if FONDO_193 is not None:
        print(f"  - Dimensiones: {FONDO_193.shape}")
        print(f"  - Tipo de datos: {FONDO_193.dtype}")
    
    print("="*60)
    print("Servidor iniciado en http://localhost:5000")
    print("="*60)
    app.run(debug=True, port=5000)