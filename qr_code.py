import qr_code

url = "http://72.60.119.36/"

# crear el QR
img = qr_code.make(url)

# guardar la imagen
img.save("mi_qr.png")
