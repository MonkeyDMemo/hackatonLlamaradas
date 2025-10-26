import tifffile
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sys

# --------------------------------------------------

# Proporcionar path compleot al archivo TIFF, o poner fpath directamente.
try:
  fpath = sys.argv[1]
except:
  print("Proporcione el path al archivo TIFF en la línea de comandos, o modifique el código del programa.")
  sys.exit()

# Lee la imagen TIFF usando tifffile
# Retornado es un arreglo de numpy de 1024x1024 con los datos de la imagen
data = tifffile.imread(fpath)
print(type(data), data.shape, data.dtype)

# Fijamos el mapa de color
cmap_name = 'Blues'
cmap = plt.colormaps[cmap_name].copy()
cmap.set_bad('black')

# Graficamos
plt.figure(figsize=(10,8))
plt.imshow(data, cmap, origin='lower', norm=mcolors.LogNorm())
plt.colorbar(label='Pixel value')
plt.title(fpath)
plt.tight_layout()
plt.show()
