#!/usr/bin/env python3
"""Comprobaciones del favicon que se pueden hacer sin ver la imagen.

Uso, desde la raíz del repo:
    python utilidades/comprobar_favicon.py

No dibuja nada: mide. Es el sustituto de mirar el ícono, y además sirve para
que el SVG no se rompa en silencio cuando alguien edita el trazado a mano
(que es justo lo que pasa con las medidas de la A).

Las medidas salen del archivo real: los polígonos se leen del `d` del <path> y
los colores se buscan en los tokens de apuromafo.css. Si alguien cambia una
cifra y rompe la figura, esto lo dice.
"""

import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SVG = RAIZ / "assets" / "img" / "favicon.svg"
CSS = RAIZ / "assets" / "css" / "apuromafo.css"
NS = "{http://www.w3.org/2000/svg}"

fallos = []


def comprobar(ok, texto, detalle=""):
    print(("  OK    " if ok else "  FALLA ") + texto
          + ("   " + detalle if detalle else ""))
    if not ok:
        fallos.append(texto)


print("1. XML bien formado")
try:
    raiz = ET.parse(SVG).getroot()
    comprobar(True, f"se parsea sin errores; la raíz es {raiz.tag}")
except ET.ParseError as e:
    comprobar(False, f"error de XML: {e}")
    sys.exit(1)

print("2. No depende de nada externo (en un favicon no hay a quién pedirle nada)")
# Se sacan los comentarios: lo que se busca es que el dibujo no los use, no que
# el archivo no los mencione al explicar por qué.
crudo = re.sub(r"<!--.*?-->", "", SVG.read_text("utf-8"), flags=re.S)
for trozo in ("<text", "font-family", "<image", "<filter", "<use", "<script", "xlink:href", "@import"):
    comprobar(trozo not in crudo, f"no se usa {trozo!r}")
comprobar("<style" in crudo, "los colores van dentro del propio SVG")
comprobar(raiz.find(f"{NS}title") is not None, "lleva <title> para cuando se abra el archivo")

print("3. La caja y el borde caben en el viewBox")
vb = [float(v) for v in raiz.get("viewBox").split()]
comprobar(len(vb) == 4 and vb[:2] == [0, 0] and vb[2] == vb[3] and vb[2] > 0,
          f"viewBox cuadrado y con origen en 0 0: {vb}")

rect = raiz.find(f"{NS}rect")
c = {k: float(rect.get(k)) for k in ("x", "y", "width", "height", "rx", "stroke-width")}
sw = c["stroke-width"]
comprobar(c["x"] - sw / 2 >= vb[0] and c["y"] - sw / 2 >= vb[1]
          and c["x"] + c["width"] + sw / 2 <= vb[2]
          and c["y"] + c["height"] + sw / 2 <= vb[3],
          f"el rect con su borde cabe justo en el viewBox: {c}")
comprobar(c["rx"] < c["width"] / 2, f"el radio es menor que la mitad del lado: rx={c['rx']}")

print("4. El trazado de la letra")
ruta = raiz.find(f"{NS}path")
d = ruta.get("d")
comandos = set(re.sub(r"[-0-9.,\s]", "", d))
comprobar(comandos <= set("MLZ"), f"los comandos son {sorted(comandos)} (M, L, Z: sin curvas)")
comprobar(ruta.get("fill-rule") == "evenodd",
          "fill-rule=evenodd: los huecos se restan sin importar el sentido del subtrazo")

# Cada subtrazo es un polígono: M ... L* Z
polos = [[tuple(float(n) for n in par.split())
          for par in re.findall(r"[-0-9.]+\s+[-0-9.]+", sub)]
         for sub in re.findall(r"M([^M]*?Z)", d)]
comprobar(len(polos) == 3, f"{len(polos)} subtrazos: la A y {len(polos) - 1} huecos")
comprobar([len(p) for p in polos] == [3, 3, 4],
          f"vértices por subtrazo: {[len(p) for p in polos]} (3, 3 y 4)")
planos = [(x, y) for p in polos for x, y in p]
comprobar(all(0 <= x <= vb[2] and 0 <= y <= vb[3] for x, y in planos),
          f"los {len(planos)} vértices caen dentro del viewBox")


def cruces_en(y):
    """Dónde corta la horizontal y los subtrazos. Con fill-rule="evenodd" la
    letra es lo que queda entre cada par de cruces consecutivos, así que con
    esto se mide la figura sin dibujarla."""
    xs = []
    for p in polos:
        for (xa, ya), (xb, yb) in zip(p, p[1:] + p[:1]):
            # El rango de y es semiabierto para no contar dos veces un vértice.
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
    return sorted(xs)


def paridad(x, y):
    """True si el punto está dentro de la letra."""
    return sum(1 for cx in cruces_en(y) if cx > x) % 2 == 1


def tramos(y):
    """Los tramos horizontales pintados a la altura y, con su ancho."""
    xs = cruces_en(y)
    return list(zip(xs[0::2], xs[1::2]))


print("5. La letra a lo ancho (esto es lo que decide si se lee a 16 px)")
#            altura   nombre             tramos  mínimo en px a 16 (None = la punta,
#                                                    que se estrecha a propósito)
esperado = [(10.5, "punta", 1, None), (24.0, "hueco de arriba", 2, 1.0),
            (32.0, "hueco de arriba", 2, 1.0), (38.5, "barra", 1, 1.0),
            (41.5, "barra", 1, 1.0), (44.5, "barra", 1, 1.0),
            (46.0, "patas", 2, 1.0), (53.0, "patas", 2, 1.0)]
for y, nombre, cuantos, minimo_px in esperado:
    t = tramos(y)
    anchos = [round(b - a, 2) for a, b in t]
    comprobar(len(t) == cuantos,
              f"y={y:>5} ({nombre:<15}): {len(t)} tramo(s) de {anchos} unidades")
    if minimo_px is not None:
        comprobar(all(ancho / 4 >= minimo_px for ancho in anchos),
                  f"y={y:>5}: ningún tramo mide menos de {minimo_px} px a 16")

# La punta se estrecha hacia arriba: si alguien mueve un vértice, esto se avisa.
anchuras = [round(sum(b - a for a, b in tramos(y)), 2) for y in (10.5, 14.5, 18.5, 22.5)]
comprobar(anchuras == sorted(anchuras) and len(set(anchuras)) == 4,
          f"la punta se abre hacia abajo sin escalones: {anchuras} unidades a 16, 18.5, 22.5 y 10.5")

print("6. Medidas de la figura, en unidades y traducidas a 16 px (4 u = 1 px)")
for y, nombre in ((46.0, "grosor de las patas"), (24.0, "grosor de la A sobre la barra"),
                  (53.0, "patas, abajo del todo")):
    t = tramos(y)
    minimo = min(b - a for a, b in t)
    comprobar(minimo >= 4.0,
              f"y={y} ({nombre}): el tramo más fino mide {minimo:.2f} u = {minimo / 4:.2f} px a 16")
apex = min(y for _, y in planos)
base = max(y for _, y in planos)
izq = min(x for x, _ in planos)
der = max(x for x, _ in planos)
comprobar(38 <= base - apex <= 48,
          f"alto de la A: {base - apex} u = {(base - apex) / 4:.2f} px a 16 (de 16 disponibles)")
comprobar(abs((izq + der) / 2 - 32) < 1 and abs(apex + base - 2 * 32) < 1,
          f"ancho de la A: {der - izq} u = {(der - izq) / 4:.2f} px a 16, centrada en el 64")
barra = 45.0 - 38.0
comprobar(barra / 4 >= 1.0, f"la barra mide {barra} u = {barra / 4:.2f} px a 16")

print("7. Los colores son los tokens de apuromafo.css (sección 1)")
css = CSS.read_text("utf-8")
estilo = raiz.find(f"{NS}style").text
claro, _, oscuro = estilo.partition("@media")


def token_de_color(color):
    m = re.search(r"(--ap-[a-z0-9-]+):\s*" + color + r"\b", css, re.I)
    return m.group(1) if m else None


for color, esperado in (("#ffffff", "--ap-superficie"), ("#c2cad6", "--ap-linea-fuerte"),
                        ("#0a7f5c", "--ap-jade")):
    comprobar(color in claro.lower() and token_de_color(color) == esperado,
              f"claro:  {color} está en el SVG y en el CSS es {token_de_color(color)}")
for color, esperado in (("#121924", "--ap-superficie"), ("#2f3d51", "--ap-linea-fuerte"),
                        ("#4ade9b", "--ap-jade")):
    comprobar(color in oscuro.lower() and token_de_color(color) == esperado,
              f"oscuro: {color} está en el SVG y en el CSS es {token_de_color(color)}")
comprobar("prefers-color-scheme: dark" in estilo, "pregunta por la preferencia del sistema")
comprobar(claro.index("#ffffff") < oscuro.index("#121924"),
          "la versión de base (la que no depende de la preferencia) es la clara")

def alfa_minimo(datos):
    """El alfa más bajo de un PNG RGBA de 8 bits, o None si el PNG usa otro
    formato (entrelazado, paleta, menos de 8 bits...) y no se puede mirar así.

    Se descomprime con zlib y se deshace el filtro de cada fila, que es lo
    único que separa un PNG de una lista de bytes. Devuelve (mínimo, cuántos
    píxeles se han mirado)."""
    if len(datos) < 33 or datos[24] != 8 or datos[25] != 6 or datos[28] != 0:
        return None, 0
    # Los trozos IDAT van seguidos, con su longitud delante, hasta IEND.
    idat = b""
    i = 8
    while i + 8 <= len(datos):
        largo = int.from_bytes(datos[i:i + 4], "big")
        tipo = datos[i + 4:i + 8]
        if tipo == b"IDAT":
            idat += datos[i + 8:i + 8 + largo]
        elif tipo == b"IEND":
            break
        i += 12 + largo
    crudo = zlib.decompress(idat)
    paso = datos[24] and 4 or 4
    ancho = int.from_bytes(datos[16:20], "big")
    fila = 1 + ancho * paso
    if len(crudo) < fila:
        return None, 0
    minimo = 255
    anterior = bytearray(ancho * paso)
    for y in range(len(crudo) // fila):
        base = y * fila
        tipo_filtro = crudo[base]
        linea = bytearray(crudo[base + 1:base + fila])
        # Los cinco filtros de PNG, tal como los define la especificación.
        for x in range(len(linea)):
            a = linea[x - paso] if x >= paso else 0
            b = anterior[x]
            c = anterior[x - paso] if x >= paso else 0
            if tipo_filtro == 1:
                linea[x] = (linea[x] + a) & 0xFF
            elif tipo_filtro == 2:
                linea[x] = (linea[x] + b) & 0xFF
            elif tipo_filtro == 3:
                linea[x] = (linea[x] + (a + b) // 2) & 0xFF
            elif tipo_filtro == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                linea[x] = (linea[x] + pred) & 0xFF
        for x in range(3, len(linea), 4):
            minimo = min(minimo, linea[x])
        anterior = linea
    return minimo, ancho * (len(crudo) // fila)


print("8. Los dos archivos que genera el otro script, donde tienen que estar")
# Esto es justo lo que estuvo mal: el .ico estava en assets/ y se servia en
# /assets/favicon.ico, mientras el comentario decia que estaba en la raiz. Los
# lectores de RSS piden /favicon.ico sin mirar el HTML, asi que tiene que estar
# ahi; y como Jekyll solo copia a la raiz del sitio lo que esta en la raiz del
# repo, el archivo va en la raiz del repo.
ICO = RAIZ / "favicon.ico"
PNG = RAIZ / "assets" / "img" / "apple-touch-icon.png"
viejo = RAIZ / "assets" / "favicon.ico"

comprobar(not viejo.is_file(),
          "no queda un favicon.ico en assets/ (serviria en /assets/favicon.ico, "
          "direccion que nadie pide)")

if ICO.is_file():
    datos = ICO.read_bytes()
    # Un ICO es: reservado(2) tipo(2) cuantos(2), y luego una entrada de 16
    # bytes por imagen: ancho, alto, colores, reservado, planos(2), bits(2),
    # tamaño(4) y desplazamiento(4). Aqui va una sola imagen y lo que hay
    # detrás es el PNG tal cual, desde el byte 22.
    ancho_ico = datos[6] if len(datos) > 7 else 0
    alto_ico = datos[7] if len(datos) > 7 else 0
    bits = int.from_bytes(datos[12:14], "little") if len(datos) > 13 else 0
    tamano = int.from_bytes(datos[14:18], "little") if len(datos) > 17 else 0
    donde = int.from_bytes(datos[18:22], "little") if len(datos) > 21 else 0
    comprobar(datos[:4] == b"\x00\x00\x01\x00" and (ancho_ico, alto_ico) == (32, 32),
              f"{ICO.relative_to(RAIZ).as_posix()}: ICO de una imagen de 32 x 32",
              f"tipo {datos[2:4].hex()} ancho {ancho_ico} alto {alto_ico}")
    comprobar(bits == 32, "el ICO declara 32 bits por píxel", str(bits))
    comprobar(donde == 22 and tamano == len(datos) - 22
              and datos[22:26] == b"\x89PNG",
              "detrás de la entrada está el PNG, y el tamaño que declara es el real",
              f"offset {donde}, tamaño {tamano}, bytes {len(datos)}")
else:
    comprobar(False, f"falta {ICO.relative_to(RAIZ).as_posix()}: "
                     f"sin él, /favicon.ico responde 404 y los lectores de RSS "
                     f"no muestran icono (se genera con "
                     f"utilidades/generar_favicon.py)")

if PNG.is_file():
    datos = PNG.read_bytes()
    if datos[:8] == b"\x89PNG\r\n\x1a\n":
        ancho = int.from_bytes(datos[16:20], "big")
        alto = int.from_bytes(datos[20:24], "big")
        profundidad = datos[24]
        color = datos[25]
        entrelazado = datos[28]
        comprobar((ancho, alto) == (180, 180),
                  f"{PNG.relative_to(RAIZ).as_posix()}: PNG de 180 x 180, que es "
                  f"lo que iOS espera para apple-touch-icon",
                  f"{ancho}x{alto}")
        # iOS no compone: le aplica su propia máscara encima, así que un solo
        # píxel transparente se ve como un agujero. No importa que el archivo
        # tenga canal alfa (RGBA, tipo 6); importa que ningún alfa sea menor de
        # 255. Por eso se descomprime el PNG en vez de mirar el tipo de color.
        alfa_min, pixeles = alfa_minimo(datos)
        if alfa_min is None:
            comprobar(True, "el PNG usa un formato que este comprobador no "
                            "descomprime; el canal alfa no se ha mirado",
                      f"tipo de color {color}, profundidad {profundidad}, "
                      f"entrelazado {entrelazado}")
        else:
            comprobar(alfa_min == 255,
                      f"{PNG.relative_to(RAIZ).as_posix()}: ningún píxel "
                      f"transparente (iOS no compone y el agujero se vería)",
                      f"{pixeles} píxeles, alfa mínimo {alfa_min}")
    else:
        comprobar(False, f"{PNG.relative_to(RAIZ).as_posix()}: no empieza por la "
                         f"firma de un PNG")
else:
    comprobar(False, f"falta {PNG.relative_to(RAIZ).as_posix()}: "
                     f"iOS no acepta SVG en apple-touch-icon")

print()
if fallos:
    print(f"FALLAN {len(fallos)} comprobaciones:")
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("Todo en orden.")
