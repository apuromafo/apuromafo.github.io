"""Los iconos del sitio: los del tema (clases de Font Awesome) y los propios.

Al quitar la CDN de Font Awesome, cualquier <i class="fas fa-..."> que escriba
el tema se queda sin dibujo. La red de seguridad es assets/css/iconos-tema.css,
que vuelve a pintar cada uno como máscara con currentColor. Lo que se comprueba
aquí es exactamente eso:

  (a) que cada clase fa-* que aparece en el sitio construido tenga su regla
      [class~="fa-..."]::before en iconos-tema.css (si no, se ve un hueco);
  (b) que esas reglas traigan la máscara con y sin prefijo (Safari sólo lee la
      que lleva -webkit-);
  (c) que los iconos propios de _data/apuromafo_iconos.yml tengan viewBox y
      cuerpo, y que ningún cuerpo haya quedado partido a la mitad.

De paso se listan los bloques del encabezado y del pie, para tenerlos a mano al
revisar un cambio de tema. Antes este script solo informaba; sale con 1 en
cuanto encuentra algo.

Uso:  python utilidades/auditorias/revisar_iconos.py
"""

import collections
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

BUILD = contexto.BUILD
CSS = contexto.REPO / "assets" / "css" / "iconos-tema.css"
YAML = contexto.REPO / "_data" / "apuromafo_iconos.yml"

fallos = []


def chequear(ok, texto, detalle=""):
    print(("  OK   " if ok else "  FALLA") + "  " + texto
          + ("   " + detalle if detalle else ""))
    if not ok:
        fallos.append(texto + (" | " + detalle if detalle else ""))
    return ok


# --------------------------------------------------------------------------
# Las clases que el tema deja escritas en el sitio construido
# --------------------------------------------------------------------------
# Un <i> con clase de icono es el caso que hay que vigilar: sin CDN no tiene
# dibujo. Se buscan en todas las páginas construidas, no en una sola, porque el
# tema escribe los suyos en el encabezado, en el pie y en cosas que aparecen
# según la página.
CLASES_EN_UN_I = re.compile(
    r'<i[^>]*class="([^"]*(?:fa-|fas|fasl|fab|far|fal|fad)[^"]*)"[^>]*>')
# En Font Awesome el nombre del icono es la última de las clases fa-; las demás
# (fa-fw, fa-lg, fa-2x...) son modificadores de tamaño y no se dibujan. Pedir
# una máscara para "fa-fw" daría un falso positivo.
ULTIMA_FA = re.compile(r'(fa-[a-z0-9-]+)["\']?\s*$')

usadas = collections.Counter()
donde = collections.defaultdict(set)
paginas = sorted(BUILD.rglob("*.html"))
chequear(bool(paginas), "el sitio está construido", f"{len(paginas)} páginas")

for html in paginas:
    texto = html.read_text(encoding="utf-8", errors="replace")
    for m in CLASES_EN_UN_I.finditer(texto):
        ultimo = ULTIMA_FA.search(m.group(1))
        if ultimo:
            usadas[ultimo.group(1)] += 1
            donde[ultimo.group(1)].add(
                str(html.relative_to(BUILD).as_posix()))

print("== <i> con clase de icono en el sitio construido ==")
for nombre, n in usadas.most_common():
    print(f"   {n:3}  {nombre:18} en {', '.join(sorted(donde[nombre]))}")
if not usadas:
    print("   (ninguno)")

# --------------------------------------------------------------------------
# La red de seguridad: las reglas de máscara
# --------------------------------------------------------------------------
css = CSS.read_text(encoding="utf-8")
# Cada bloque empieza por [class~="fa-..."]::before { y termina en su llave de
# cierre; como viene generado, ese es el único sitio donde hay que mirar.
reglas = {}
for m in re.finditer(
        r'\[class~="(fa-[a-z0-9-]+)"\]::before\s*\{(.*?)\}', css, re.S):
    reglas[m.group(1)] = m.group(2)

print(f"\n== reglas de máscara en {CSS.relative_to(contexto.REPO)}: "
      f"{len(reglas)} ==")

print("\n== (a) cada clase del sitio tiene su máscara ==")
for nombre in sorted(usadas):
    chequear(nombre in reglas, f"{nombre} tiene su ::before con máscara",
             "" if nombre in reglas else f"aparece en {len(donde[nombre])} "
             f"página(s) y no se dibujaría")

print("\n== (b) cada máscara viene con y sin prefijo ==")
for nombre, cuerpo in sorted(reglas.items()):
    sin_prefijo = re.search(r'(?<![-\w])mask\s*:', cuerpo) is not None
    con_prefijo = "-webkit-mask:" in cuerpo
    chequear(con_prefijo and sin_prefijo,
             f"{nombre} declara -webkit-mask y mask",
             "" if con_prefijo and sin_prefijo
             else f"webkit={con_prefijo} mask={sin_prefijo}")

# Al revés: una regla de máscara que no usa ninguna página es peso muerto.
huerfanas = sorted(set(reglas) - set(usadas))
print(f"\n== reglas que hoy no usa ninguna página: {len(huerfanas)} ==")
for nombre in huerfanas:
    print(f"   {nombre}")

# --------------------------------------------------------------------------
# Los iconos propios
# --------------------------------------------------------------------------
print("\n== (c) iconos propios en _data/apuromafo_iconos.yml ==")
VIEWBOX = re.compile(r'^(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+'
                     r'(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$')

lineas = YAML.read_text(encoding="utf-8").splitlines()
nombre = None
viewbox = None
cuerpo = []
largo_min = None
largo_max = 0
cuenta = 0

def cerrar():
    """Mira el icono que se acaba de leer del archivo y lo comprueba."""
    global largo_min, largo_max, cuenta
    if nombre is None:
        return
    cuenta += 1
    texto = "\n".join(cuerpo).strip()
    largo = len(texto)
    largo_min = largo if largo_min is None else min(largo_min, largo)
    largo_max = max(largo_max, largo)
    m = VIEWBOX.match((viewbox or "").strip().strip('"'))
    chequear(m is not None and float(m.group(3)) > 0 and float(m.group(4)) > 0,
             f"{nombre}: viewBox con cuatro números y tamaño mayor que cero",
             viewbox)
    chequear(largo > 0, f"{nombre}: el cuerpo no está vacío", f"{largo} caracteres")
    # Un cuerpo partido justo después de un signo o de un punto deja un trazado
    # que parece válido y no dibuja nada; el generador avisa, pero el archivo
    # puede venir de otra parte.
    chequear(not re.search(r'[-\d]\.\s*$', "\n".join(cuerpo[:-1])),
             f"{nombre}: ninguna línea del cuerpo corta un número",
             cuerpo[-1][:40] if len(cuerpo) > 1 else "")

for linea in lineas:
    # El archivo lleva una cabecera de comentarios y alguno acaba en dos puntos:
    # sin esta guarda, un "#" se tomaba por el nombre de un icono.
    if linea.lstrip().startswith("#"):
        continue
    if re.match(r"^\S[^:]*:$", linea):
        cerrar()
        nombre = linea[:-1]
        viewbox = None
        cuerpo = []
    elif nombre and "viewBox:" in linea:
        viewbox = linea.split("viewBox:", 1)[1].strip()
    elif nombre is not None and re.match(r"^\s{4,}\S", linea):
        cuerpo.append(linea.strip())
cerrar()

print(f"   {cuenta} iconos; cuerpo de {largo_min} a {largo_max} caracteres")

# --------------------------------------------------------------------------
# Los bloques que el tema escribe, por si hay que revisarlos
# --------------------------------------------------------------------------
print("\n== bloques del encabezado y del pie (informativo) ==")
muestra = (BUILD / "indice" / "index.html")
texto = muestra.read_text(encoding="utf-8", errors="replace")
for etiqueta, patron in [
    ("cabecera", r'(<header class="ap-cabecera".*?</header>)'),
    ("pie", r'(<div id="footer".*?page__footer-copyright.*?</footer>)'),
]:
    m = re.search(patron, texto, re.S)
    if m:
        bloque = m.group(1)
        print(f"\n-- {etiqueta} de {muestra.relative_to(BUILD)}: "
              f"{len(bloque)} bytes, {bloque.count('<svg')} svg, "
              f"{len(CLASES_EN_UN_I.findall(bloque))} <i> de icono")
    else:
        print(f"\n-- {etiqueta}: no encontrado (¿cambió el tema o el layout?)")

print()
if fallos:
    print(f"FALLAS: {len(fallos)}")
    for f in fallos:
        print("  - " + f)
    sys.exit(1)
print("TODO OK")