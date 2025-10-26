from roboflow import Roboflow

rf = Roboflow(api_key="cygTL33SntK8etDjvyVD")
project = rf.workspace("llamaradas").project("llamaradas-v2")

# Aplicar etiquetas a múltiples imágenes
for image_id in image_ids:
    project.add_label(image_id, "sinLlamaradaSolar")