"""Genera el icono de la app movil (PNG 512x512) con el estilo de la referencia."""

from PIL import Image, ImageDraw

AZUL = (26, 115, 232, 255)
BLANCO = (255, 255, 255, 255)

L = 512
im = Image.new("RGBA", (L, L), (0, 0, 0, 0))
d = ImageDraw.Draw(im)

# Cuadrado azul redondeado.
d.rounded_rectangle([16, 16, L - 16, L - 16], radius=112, fill=AZUL)

# Termometro: tubo + bulbo.
cx = L * 0.5
y_bulbo = L * 0.70
y_tope = L * 0.24
r_bulbo = 42
ancho = 22

d.rounded_rectangle(
    [cx - ancho / 2, y_tope, cx + ancho / 2, y_bulbo + r_bulbo * 0.5],
    radius=ancho / 2,
    outline=BLANCO,
    width=13,
)
d.ellipse(
    [cx - r_bulbo, y_bulbo - r_bulbo, cx + r_bulbo, y_bulbo + r_bulbo],
    outline=BLANCO,
    width=13,
)
# Mercurio.
d.rounded_rectangle(
    [cx - 9, y_bulbo - 4, cx + 9, y_bulbo + 70],
    radius=9,
    fill=BLANCO,
)
d.ellipse([cx - 20, y_bulbo - 20, cx + 20, y_bulbo + 20], fill=BLANCO)

im.save("assets/app_movil.png")
print("escrito assets/app_movil.png")
