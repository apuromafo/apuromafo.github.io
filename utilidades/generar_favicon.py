#!/usr/bin/env python3
"""Pasa el favicon SVG a los dos formatos que el SVG no cubre.

Por qué existe este script: los navegadores actuales toman el icono de
`assets/img/favicon.svg`, pero hay dos que no lo aceptan y a los que ni
siquiera se les puede pasar el mismo dibujo:

  · el ícono de iOS (el que sale al agregar la página a la pantalla de inicio)
    solo admite PNG, y es un cuadrado opaco al que iOS le aplica su propia
    máscara. Por eso sale sin esquinas redondeadas ni borde, con el fondo
    entero y la A en el centro.
  · /favicon.ico en la raíz. No lo pide ningún navegador que encuentre el
    <link rel="icon"> del SVG, pero sí lo piden a ciegas los lectores de RSS y
    los que hacen vista previa de enlaces (Slack, Telegram), que no leen el
    HTML. Sin ese archivo contestan 404 y no muestran nada.

Con eso se acaba: no se genera un PNG de 32 px como alternativa al SVG, porque
se ha visto que muchos navegadores eligen el PNG y dejan el SVG, que es
justamente el que se ve bien en pantallas grandes y en el modo oscuro.

Cómo se dibuja: se leen el viewBox, el <rect> y el `d` del <path> del propio
SVG, así que el SVG es la única fuente de la verdad. No hay que interpretar
curvas ni comandos raros: el script acepta solo M, L y Z absolutos y avisa con
un mensaje claro si algún día aparece otra cosa. El suavizado sale de tomar
varias filas de muestra por píxel y de calcular la cobertura exacta a lo
ancho: no hay nada que instalar ni que descargar.

Uso:
    python utilidades/generar_favicon.py

Escribe:
    assets/img/apple-touch-icon.png   180 x 180, opaco, sin esquinas redondeadas
    favicon.ico                       32 x 32, con la ficha y su borde

El .ico va en la raíz del repo y no en assets/: los lectores de RSS piden
/favicon.ico tal cual, y Jekyll solo lo sirve en la raíz del sitio si el archivo
está en la raíz del repositorio. En assets/ se serviría en /assets/favicon.ico,
que es una dirección que nadie pide.

El SVG no lo genera este script: ese se dibuja a mano y se mide con
utilidades/comprobar_favicon.py.
"""

import math
import pathlib
import re
import struct
import xml.etree.ElementTree as ET
import zlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SVG = RAIZ / "assets" / "img" / "favicon.svg"
NS = "{http://www.w3.org/2000/svg}"

# Cuántas filas de muestra se toman por píxel a lo alto. A 32 px de lado una
# fila son dos unidades del dibujo, así que con 16 muestras el borde de la
# ficha queda en un doceavo de píxel, que es lo que se ve bien en un ícono
# chico. De más sólo cuesta tiempo: esto corre una vez y a mano.
FILAS_POR_PIXEL = 16


# --------------------------------------------------------------------------
# Leer el SVG
# --------------------------------------------------------------------------
def leer_svg() -> dict:
    raiz = ET.parse(SVG).getroot()
    caja = [float(v) for v in raiz.get("viewBox").split()]
    if caja[0] or caja[1] or caja[2] != caja[3]:
        raise SystemExit("el viewBox tiene que ser un cuadrado con origen en 0 0")

    rect = raiz.find(f"{NS}rect")
    ficha = {k: float(rect.get(k)) for k in ("x", "y", "width", "height", "rx", "stroke-width")}

    ruta = raiz.find(f"{NS}path")
    if ruta.get("fill-rule") != "evenodd":
        raise SystemExit("la letra tiene que ir con fill-rule=evenodd")
    if set(re.sub(r"[-0-9.,\s]", "", ruta.get("d"))) - set("MLZ"):
        raise SystemExit("el trazado usa comandos que este script no sabe leer")
    letra = [[tuple(float(n) for n in par.split())
               for par in re.findall(r"[-0-9.]+\s+[-0-9.]+", sub)]
              for sub in re.findall(r"M([^M]*?Z)", ruta.get("d"))]

    # Los colores se toman de las reglas de base del <style> y no de las del
    # @media: un PNG no puede cambiar con la preferencia del sistema, así que
    # se dibuja con la versión clara, que es la que también se ve bien sola.
    estilo = raiz.find(f"{NS}style").text.partition("@media")[0]

    def color(selector, propiedad):
        busca = re.escape(selector) + r"\s*\{[^}]*" + propiedad + r":\s*(#[0-9a-fA-F]{6})"
        m = re.search(busca, estilo)
        if not m:
            raise SystemExit(f"el <style> del SVG no declara {propiedad} para {selector}")
        return tuple(int(m.group(1)[i:i + 2], 16) for i in (1, 3, 5))

    return {
        "lado": caja[2],
        "ficha": ficha,
        "letra": letra,
        "fondo": color(".fondo", "fill"),
        "borde": color(".fondo", "stroke"),
        "tinta": color(".letra", "fill"),
    }


# --------------------------------------------------------------------------
# Medir el dibujo
# --------------------------------------------------------------------------
def tramos_letra(letra, y):
    """Los tramos horizontales de la letra a la altura `y`.

    Con la regla par, la letra es lo que queda entre cada par de cruces de la
    horizontal con los subtrazos. El rango de cada lado es semiabierto para no
    contar dos veces un vértice."""
    xs = []
    for p in letra:
        for (xa, ya), (xb, yb) in zip(p, p[1:] + p[:1]):
            if (ya <= y < yb) or (yb <= y < ya):
                xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
    xs.sort()
    return list(zip(xs[0::2], xs[1::2]))


def fila_redondeada(y, x0, x1, y0, y1, r):
    """El tramo horizontal que ocupa un rectángulo de esquinas redondeadas a la
    altura `y`. Al engrosar o adelgazar el rectángulo los centros de las
    esquinas no se mueven, así que el borde sale de la misma cuenta: primero el
    rectángulo por fuera y después por dentro."""
    if r <= 0:
        return (x0, x1)
    if y < y0 + r:
        dy = y0 + r - y
    elif y > y1 - r:
        dy = y - (y1 - r)
    else:
        return (x0, x1)
    dx = r - math.sqrt(max(0.0, r * r - dy * dy))
    return (x0 + dx, x1 - dx)


# --------------------------------------------------------------------------
# Dibujar
# --------------------------------------------------------------------------
def dibujar(svg, lado_px, con_ficha):
    """Devuelve las filas de píxeles (RGBA) del icono de `lado_px` px.

    `con_ficha` decide si se pinta la ficha redondeada con su borde (para el
    ícono de escritorio, que tiene que dejar ver el fondo de la pestaña) o el
    cuadrado entero (para el de iOS, al que iOS le aplica su propia máscara y no
    le sirve una ficha con las esquinas ya redondeadas)."""
    lado = svg["lado"]
    escala = lado_px / lado
    ficha = svg["ficha"]
    peso = 1 / FILAS_POR_PIXEL

    def extentos(inset):
        """El rectángulo engrosado (`inset` positivo) o adelgazado. El rx
        cambia en la misma medida, y por eso las esquinas quedan en el mismo
        lugar en los dos casos."""
        return (ficha["x"] - inset, ficha["x"] + ficha["width"] + inset,
                ficha["y"] - inset, ficha["y"] + ficha["height"] + inset,
                max(0.0, ficha["rx"] + inset))

    medio = ficha["stroke-width"] / 2
    fuera, dentro = extentos(medio), extentos(-medio)

    pixeles = []
    for fila in range(lado_px):
        cov_ficha = [0.0] * lado_px
        cov_borde = [0.0] * lado_px
        cov_tinta = [0.0] * lado_px

        def marcar(destino, xa, xb):
            xa, xb = max(0.0, xa * escala), min(float(lado_px), xb * escala)
            for i in range(int(xa), min(lado_px, int(xb) + 1)):
                destino[i] += (min(xb, i + 1) - max(xa, i)) * peso

        for muestra in range(FILAS_POR_PIXEL):
            y = (fila + (muestra + 0.5) / FILAS_POR_PIXEL) * lado / lado_px
            for xa, xb in tramos_letra(svg["letra"], y):
                marcar(cov_tinta, xa, xb)
            if con_ficha:
                af, bf = fila_redondeada(y, *fuera)
                ai, bi = fila_redondeada(y, *dentro)
                marcar(cov_ficha, af, bf)
                marcar(cov_borde, af, ai)
                marcar(cov_borde, bi, bf)
            else:
                for i in range(lado_px):
                    cov_ficha[i] += peso

        salida = []
        for i in range(lado_px):
            col, alfa = (svg["fondo"], 0.0)
            for capa, cov in ((svg["fondo"], cov_ficha[i]), (svg["borde"], cov_borde[i]),
                              (svg["tinta"], cov_tinta[i])):
                cov = min(1.0, cov)
                if cov <= 0.0:
                    continue
                # Una capa encima de otra, como el "over" del CSS pero hecho a
                # mano: primero se ve la de arriba y por debajo asoma la otra.
                nuevo_alfa = cov + alfa * (1 - cov)
                if nuevo_alfa <= 0.0:
                    continue
                mezcla = alfa * (1 - cov)
                col = tuple(round((c * cov + p * mezcla) / nuevo_alfa) for c, p in zip(capa, col))
                alfa = nuevo_alfa
            salida.append(col + (round(alfa * 255),))
        pixeles.append(salida)
    return pixeles


# --------------------------------------------------------------------------
# Escribir PNG y ICO
# --------------------------------------------------------------------------
def construir_png(ancho, alto, pixeles):
    """PNG RGBA de 8 bits, con una fila de filtro por píxel (filtro 0)."""
    crudo = b"".join(b"\x00" + bytes(v for pixel in fila for v in pixel) for fila in pixeles)

    def trozo(tipo, datos):
        return (struct.pack(">I", len(datos)) + tipo + datos
                + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF))

    cabecera = struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + trozo(b"IHDR", cabecera)
            + trozo(b"IDAT", zlib.compress(crudo, 9)) + trozo(b"IEND", b""))


def escribir_ico(ruta, png, lado):
    """Un ICO es un directorio de 22 bytes y, detrás, la imagen. Se guarda el
    PNG tal cual: Windows y los lectores de RSS saben mostrarlo, y no hace falta
    codificar BMP."""
    cabecera = struct.pack("<HHH", 0, 1, 1)
    entrada = struct.pack("<BBBBHHII", lado, lado, 0, 0, 1, 32, len(png), 22)
    ruta.write_bytes(cabecera + entrada + png)
    return ruta.stat().st_size


def main():
    svg = leer_svg()
    hexa = lambda c: "#%02x%02x%02x" % c
    print(f"leído {SVG.relative_to(RAIZ).as_posix()}: {svg['lado']:.0f} u de lado, "
          f"{len(svg['letra'])} subtrazos, fondo {hexa(svg['fondo'])}, "
          f"borde {hexa(svg['borde'])}, letra {hexa(svg['tinta'])}")

    # iOS: 180 x 180 opaco y sin ficha redondeada (la máscara la pone iOS).
    apple = RAIZ / "assets" / "img" / "apple-touch-icon.png"
    bytes_png = construir_png(180, 180, dibujar(svg, 180, con_ficha=False))
    apple.write_bytes(bytes_png)
    print(f"OK  {apple.relative_to(RAIZ).as_posix()}  180x180  {len(bytes_png)} bytes")

    # /favicon.ico: 32 x 32 con la ficha y su borde, que es lo que se ve en la
    # pestaña del navegador y en la barra del escritorio. Va en la raíz del
    # repo para que Jekyll lo sirva en /favicon.ico, que es lo que piden a ciegas
    # los lectores de RSS y las vistas previas de enlaces.
    bytes_32 = construir_png(32, 32, dibujar(svg, 32, con_ficha=True))
    ico = RAIZ / "favicon.ico"
    total = escribir_ico(ico, bytes_32, 32)
    print(f"OK  {ico.relative_to(RAIZ).as_posix()}  32x32  {total} bytes "
          f"({len(bytes_32)} de PNG)")
    # El .ico viejo en assets/ dejaría un /assets/favicon.ico que no pide nadie
    # y que confunde al leer el repo.
    viejo = RAIZ / "assets" / "favicon.ico"
    if viejo.is_file():
        viejo.unlink()
        print(f"    borrado {viejo.relative_to(RAIZ).as_posix()}, que sobraba")


if __name__ == "__main__":
    main()
