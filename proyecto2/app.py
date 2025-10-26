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
os.makedirs('templates', exist_ok=True)  # Asegurar que existe templates

# Configuración Roboflow - MODELOS POR TAREA
API_KEY = "cygTL33SntK8etDjvyVD"
MODEL_TASK1 = "llamaradas-v2-h7wcc/5"  # Task 1: Clasificación
MODEL_TASK2 = "llamaradas-v2-h7wcc/6"  # Task 2: Probabilidad

# Rutas de imágenes de fondo (ajusta estas rutas)
# Ajustar las rutas a una ruta relativa
FONDO_131_PATH = r"C:\Users\resendizjg\Downloads\quite_average-131.tif"
FONDO_193_PATH = r"C:\Users\resendizjg\Downloads\quite_average-193.tif"
# Rutas de imágenes de fondo (ajusta estas rutas)
#FONDO_131_PATH = "/var/www/hackatonLlamaradas/proyecto2/backgrounds/quite_average-131.tif"
#FONDO_193_PATH = "/var/www/hackatonLlamaradas/proyecto2/backgrounds/quite_average-193.tif"

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

#Esta normalizando la escala de colores del tiff a png. No debería dejarse 
def convertir_tiff_a_png(imagen_tiff):
    """
    Convierte una imagen TIFF a formato PNG escalando para mejor visualización
    """
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
        if imagen.dtype != fondo.dtype:
            print(f"Convirtiendo tipos: imagen={imagen.dtype}, fondo={fondo.dtype}")
            imagen_float = imagen.astype(np.float32)
            fondo_float = fondo.astype(np.float32)
            diferencia = imagen_float - fondo_float
            diferencia = np.clip(diferencia, 0, None)
        else:
            diferencia = cv2.subtract(imagen, fondo)
        
        return diferencia
        
    except Exception as e:
        print(f"Error en resta de fondo: {e}")
        raise

def ejecutar_modelo_segun_tarea(imagen_rgb, task_selected):
    """
    Ejecuta el modelo según la tarea seleccionada
    Task 1: Clasificación (modelo v5)
    Task 2: Probabilidad (modelo v6)
    """
    print(f"\n{'='*50}")
    print(f"🤖 EJECUTANDO ANÁLISIS - TAREA {task_selected}")
    print(f"{'='*50}")
    
    # Seleccionar modelo según tarea
    if task_selected == "1":
        model_id = MODEL_TASK1
        task_name = "Clasificación de Llamaradas"
        task_description = "Detecta si hay llamaradas solares activas"
    else:  # task_selected == "2"
        model_id = MODEL_TASK2
        task_name = "Probabilidad de Llamaradas"
        task_description = "Predice la probabilidad de llamaradas futuras"
    
    print(f"📋 Tarea: {task_name}")
    print(f"📊 Modelo: {model_id}")
    print(f"📝 Descripción: {task_description}")
    print("-" * 50)
    
    try:
        # Ejecutar modelo
        print("Ejecutando inferencia...")
        model = get_model(model_id=model_id, api_key=API_KEY)
        results = model.infer(imagen_rgb)
        
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
                    'confidence': float(pred.confidence),
                    'task': f"Task {task_selected}",
                    'task_name': task_name,
                    'model': model_id.split('/')[-1]
                })
                print(f"  ✓ {pred.class_name}: {pred.confidence:.2%}")
        
        # Análisis de resultados según la tarea
        analysis_message = ""
        alert_level = "normal"  # normal, warning, danger
        
        if task_selected == "1":  # Clasificación
            # Buscar clases específicas
            con_llamarada = next((p for p in predictions if 'conLlamaradaSolar' in p['class']), None)
            sin_llamarada = next((p for p in predictions if 'sinLlamaradaSolar' in p['class']), None)
            
            if con_llamarada and con_llamarada['confidence'] > 0.6:
                #analysis_message = f"🔥 Llamarada solar ACTIVA detectada con {con_llamarada['confidence']:.1%} de confianza"
                alert_level = "danger"
            elif sin_llamarada and sin_llamarada['confidence'] > 0.6:
                #analysis_message = f"✅ Sin llamaradas activas ({sin_llamarada['confidence']:.1%} de confianza)"
                alert_level = "normal"
            else:
                #analysis_message = "⚠️ Resultado incierto, revisar manualmente"
                alert_level = "warning"
                
        else:  # task_selected == "2" - Probabilidad
            # Analizar probabilidades futuras
            prob_alta = next((p for p in predictions if any(x in p['class'].lower() for x in ['alta', 'high', 'conllamarada'])), None)
            prob_baja = next((p for p in predictions if any(x in p['class'].lower() for x in ['baja', 'low', 'sinllamarada'])), None)
            
            if prob_alta and prob_alta['confidence'] > 0.5:
                analysis_message = f"⚡ ALERTA: Alta probabilidad de llamarada futura ({prob_alta['confidence']:.1%})"
                alert_level = "warning"
            elif prob_baja and prob_baja['confidence'] > 0.6:
                analysis_message = f"☁️ Baja probabilidad de llamaradas futuras ({prob_baja['confidence']:.1%})"
                alert_level = "normal"
            else:
                # Usar la predicción más alta
                if predictions:
                    top_pred = max(predictions, key=lambda x: x['confidence'])
                    #analysis_message = f"📊 Predicción: {top_pred['class']} ({top_pred['confidence']:.1%})"
                    alert_level = "warning" if top_pred['confidence'] < 0.6 else "normal"
        
        print(f"\n📋 Análisis: {analysis_message}")
        print("=" * 50)
        
        return {
            'predictions': predictions,
            'task': task_selected,
            'task_name': task_name,
            'task_description': task_description,
            'model_used': model_id,
            'analysis_message': analysis_message,
            'alert_level': alert_level
        }
        
    except Exception as e:
        print(f"❌ Error en modelo: {e}")
        return {
            'predictions': [],
            'task': task_selected,
            'task_name': task_name,
            'task_description': task_description,
            'model_used': model_id,
            'analysis_message': f"Error al ejecutar el modelo: {str(e)}",
            'alert_level': "danger",
            'error': str(e)
        }

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        # Obtener tarea seleccionada
        task_selected = request.form.get('task', '1')  # Por defecto Task 1
        
        # Detectar tipo de imagen por nombre
        tipo_detectado = detectar_tipo_imagen(file.filename)
        if tipo_detectado is None:
            tipo_detectado = request.form.get('wavelength', '131')
        
        print(f"\n{'='*60}")
        print(f"📸 Procesando imagen: {file.filename}")
        print(f"🌟 Tipo detectado: {tipo_detectado} Å")
        print(f"📋 Tarea seleccionada: Task {task_selected}")
        print(f"{'='*60}")
        
        # Guardar archivo original
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = secure_filename(file.filename)
        base_name = Path(filename).stem
        
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(upload_path)
        
        # Leer imagen TIFF
        imagen = cv2.imread(upload_path, cv2.IMREAD_UNCHANGED)
        if imagen is None:
            return jsonify({'error': 'No se pudo leer la imagen'}), 400
        
        print(f"Imagen cargada: shape={imagen.shape}, dtype={imagen.dtype}")
        
        # Convertir TIFF a PNG para la imagen original
        imagen_original_png = convertir_tiff_a_png(imagen)
        original_png_filename = f"{timestamp}_{base_name}_original.png"
        original_png_path = os.path.join(app.config['RESULTS_FOLDER'], original_png_filename)
        cv2.imwrite(original_png_path, imagen_original_png)
        print(f"✓ Original convertida a PNG")
        
        # Seleccionar fondo
        if tipo_detectado == '131':
            fondo = FONDO_131
            if fondo is None:
                return jsonify({'error': 'Imagen de fondo 131 no disponible'}), 500
        else:
            fondo = FONDO_193
            if fondo is None:
                return jsonify({'error': 'Imagen de fondo 193 no disponible'}), 500
        
        # Ajustar dimensiones si es necesario
        if imagen.shape[:2] != fondo.shape[:2]:
            print(f"Ajustando dimensiones: {imagen.shape} -> {fondo.shape}")
            imagen = cv2.resize(imagen, (fondo.shape[1], fondo.shape[0]))
        
        # Aplicar resta de fondo
        diferencia = procesar_resta_fondo(imagen, fondo)
        print(f"✓ Resta de fondo aplicada")
        
        # Convertir diferencia a PNG
        diferencia_png = convertir_tiff_a_png(diferencia)
        processed_filename = f"{timestamp}_{base_name}_diff_{tipo_detectado}.png"
        processed_path = os.path.join(app.config['RESULTS_FOLDER'], processed_filename)
        cv2.imwrite(processed_path, diferencia_png)
        print(f"✓ Diferencia guardada como PNG")
        
        # Preparar imagen para modelo (RGB)
        if len(diferencia_png.shape) == 2:
            imagen_para_modelo = cv2.cvtColor(diferencia_png, cv2.COLOR_GRAY2RGB)
        else:
            imagen_para_modelo = diferencia_png
        
        # EJECUTAR MODELO SEGÚN TAREA SELECCIONADA
        analysis_result = ejecutar_modelo_segun_tarea(imagen_para_modelo, task_selected)
        
        # Usar las predicciones
        predictions = analysis_result['predictions']
        
        # Crear imagen anotada
        if len(diferencia_png.shape) == 2:
            annotated = cv2.cvtColor(diferencia_png, cv2.COLOR_GRAY2BGR)
        else:
            annotated = diferencia_png.copy()
        
        if predictions:
            # Agregar texto con la predicción principal
            main_pred = max(predictions, key=lambda x: x['confidence'])
            text = f"{main_pred['class']}: {main_pred['confidence']:.1%}"
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1
            thickness = 2
            (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Rectángulo de fondo
            cv2.rectangle(annotated, (20, 20), (30 + text_width, 60), (0, 0, 0), -1)
            cv2.putText(annotated, text, (30, 50), font, font_scale, (0, 255, 0), thickness)
            
            # Agregar información de la tarea
            task_text = f"Task {task_selected}: {analysis_result['task_name']}"
            cv2.putText(annotated, task_text, (30, 90), font, 0.6, (255, 255, 255), 1)
            
            # Agregar tipo de imagen
            tipo_text = f"Wavelength: {tipo_detectado} A"
            cv2.putText(annotated, tipo_text, (30, 115), font, 0.6, (255, 255, 255), 1)
            
            # Si hay alerta, agregarla
            if analysis_result['alert_level'] == "danger":
                alert_color = (0, 0, 255)  # Rojo
            elif analysis_result['alert_level'] == "warning":
                alert_color = (0, 165, 255)  # Naranja
            else:
                alert_color = (0, 255, 0)  # Verde
                
            # Agregar mensaje de análisis
            if len(analysis_result['analysis_message']) > 50:
                # Si es muy largo, dividir en dos líneas
                msg_lines = [analysis_result['analysis_message'][:50], 
                            analysis_result['analysis_message'][50:]]
                for i, line in enumerate(msg_lines):
                    cv2.putText(annotated, line, (30, 140 + i*25), font, 0.6, alert_color, 2)
            else:
                cv2.putText(annotated, analysis_result['analysis_message'], 
                           (30, 140), font, 0.6, alert_color, 2)
        
        # Guardar imagen anotada
        annotated_filename = f"{timestamp}_{base_name}_task{task_selected}_annotated_{tipo_detectado}.png"
        annotated_path = os.path.join(app.config['RESULTS_FOLDER'], annotated_filename)
        cv2.imwrite(annotated_path, annotated)
        print(f"✓ Imagen anotada guardada")
        
        # Preparar respuesta
        response = {
            'success': True,
            'original': f"/results/{original_png_filename}",
            'processed': f"/results/{processed_filename}",
            'annotated': f"/results/{annotated_filename}",
            'predictions': predictions,
            'analysis': analysis_result,
            'timestamp': timestamp,
            'wavelength': tipo_detectado,
            'task': task_selected,
            'image_info': {
                'original_shape': imagen.shape,
                'detected_wavelength': tipo_detectado,
                'task_executed': f"Task {task_selected}"
            }
        }
        
        print(f"\n{'='*60}")
        print("✅ PROCESO COMPLETADO")
        if predictions:
            top_pred = max(predictions, key=lambda x: x['confidence'])
            print(f"📊 Predicción principal: {top_pred['class']} ({top_pred['confidence']:.2%})")
        print(f"📋 {analysis_result['analysis_message']}")
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
    print("🔥 SERVIDOR DE DETECCIÓN DE LLAMARADAS SOLARES")
    print("   Con selector de tareas")
    print("="*60)
    print(f"📋 Task 1 - Clasificación: {MODEL_TASK1}")
    print(f"📋 Task 2 - Probabilidad: {MODEL_TASK2}")
    print("-"*60)
    print(f"Fondo 131 cargado: {FONDO_131 is not None}")
    if FONDO_131 is not None:
        print(f"  - Dimensiones: {FONDO_131.shape}")
    
    print(f"Fondo 193 cargado: {FONDO_193 is not None}")
    if FONDO_193 is not None:
        print(f"  - Dimensiones: {FONDO_193.shape}")
    
    print("="*60)
    print("Servidor iniciado en http://localhost:5000")
    print("="*60)
    app.run(debug=True, port=5000)