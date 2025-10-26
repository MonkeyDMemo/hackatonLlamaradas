from roboflow import Roboflow

# Inicializa con tu API key

rf = Roboflow(api_key="cygTL33SntK8etDjvyVD")

# Ver información del workspace actual
print(rf.workspace())

# Listar todos los workspaces disponibles
workspaces = rf.workspace_list()
for ws in workspaces:
    print(f"Workspace: {ws}")