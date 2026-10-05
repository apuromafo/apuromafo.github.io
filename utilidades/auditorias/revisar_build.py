"""Comprobaciones sobre el _site ya construido.

No sustituye a mirar la página: sirve para pillar rápido lo que se rompe sin
que se note, sobre todo en el HTML que genera el tema.
"""

import pathlib
import re
import sys
from html import unescape
from urllib.parse import urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

# La carpeta de compilación sale de la configuración. El primer argumento sigue
# mandando, que es como se usaba esto antes y así no rompe los scripts viejos.
RAIZ = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else contexto.BUILD

problemas = []
avisos = []


def revisar(cond, mensaje):
    if not cond:
        problemas.append(mensaje)


# --- 1. Cargas desde otros sitios (no enlaces) -------------------------------
# Solo cuentan las cosas que el navegador descarga: <script src>, <img src>,
# <link rel=stylesheet|preload|preconnect>, <iframe src>, @import, url() de CSS.
externas = set()
recurso_html = re.compile(
    r'<script[^>]+src="([^"]+)"'
    r'|<img[^>]+src="([^"]+)"'
    r'|<link[^>]+(?:rel="stylesheet"|rel="preload"|rel="preconnect")[^>]+href="([^"]+)"'
    r'|<iframe[^>]+src="([^"]+)"', re.I)
for html in RAIZ.rglob("*.html"):
    texto = html.read_text(encoding="utf-8", errors="replace")
    for grupo in recurso_html.findall(texto):
        for url in grupo:
            if url.startswith(("http://", "https://", "//")):
                externas.add(url.split("#")[0])

for css in RAIZ.rglob("*.css"):
    texto = css.read_text(encoding="utf-8", errors="replace")
    for url in re.findall(r"url\(\s*['\"]?(https?:)?//([^'\")]+)", texto):
        externas.add("//" + url[1])

if externas:
    problemas.append(
        "el navegador descarga de sitios de terceros:\n    "
        + "\n    ".join(sorted(externas)))

# --- 2. El head de cada página ----------------------------------------------
for html in sorted(RAIZ.rglob("*.html")):
    rel = html.relative_to(RAIZ)
    texto = html.read_text(encoding="utf-8", errors="replace")
    head = texto.split("</head>", 1)[0]

    revisar("apuromafo.css" in head, f"{rel}: falta la hoja de diseño")
    revisar("fonts.css" in head, f"{rel}: falta la hoja de fuentes")
    revisar("fontawesome" not in head, f"{rel}: sigue la CDN de iconos")
    revisar(
        re.search(r'getAttribute\("data-tema"\)', head) is not None,
        f"{rel}: la hoja no comprueba el tema (habría fogonazo de color)")
    revisar('id="ap-tema-hoja"' in head, f"{rel}: falta el enlace con id")
    revisar(
        head.count("preload") >= 2, f"{rel}: no se adelantan las tipografías")

# --- 3. Estructura de la portada -------------------------------------------
inicio = (RAIZ / "index.html").read_text(encoding="utf-8", errors="replace")
cuerpo = inicio.split("<body", 1)[1]
revisar(cuerpo.count("<h1") == 1, f"portada: {cuerpo.count('<h1')} <h1> (debe ser 1)")
revisar("<title" in inicio.split("</head>")[0], "portada: sin <title>")
for clase in ("hero__titulo", "cifras", "ap-area", "ap-canal", "ap-chips",
              "ap-btn--primario", "ap-volver", "ap-progreso"):
    revisar(clase in cuerpo, f"portada: falta .{clase}")
revisar("data-reveal" in cuerpo, "portada: nada se revela al bajar")
revisar("<svg" in cuerpo, "portada: los iconos SVG no se drawearon")

# Las dos fichas de "Destacado" tienen que seguir siendo fichas con título.
fichas = re.findall(r'<div class="card"[^>]*>(.*?)</div>', cuerpo, re.S)
revisar(len(fichas) == 2, f"portada: {len(fichas)} fichas (deben ser 2)")
for i, ficha in enumerate(fichas, 1):
    revisar("<h3" in ficha, f"portada: la ficha {i} quedó sin <h3>")
    revisar("class=\"tag\"" in ficha, f"portada: la ficha {i} quedó sin etiquetas")

# --- 4. El índice de proyectos ----------------------------------------------
indice = (RAIZ / "indice" / "index.html").read_text(encoding="utf-8",
                                                     errors="replace")
lista = re.search(r'<div class="ap-indice-lista"[^>]*id="lista-proyectos"'
                  r'[^>]*>(.*?)</div>', indice, re.S)
revisar(lista is not None, "índice: no se encontró la lista de proyectos")
if lista:
    interior = lista.group(1)
    titulos = re.findall(r"<h3", interior)
    revisar(len(titulos) == contexto.PROYECTOS,
            f"índice: {len(titulos)} proyectos "
            f"(deben ser {contexto.PROYECTOS})")
    revisar("<pre>" not in interior and "<code>" not in interior,
            "índice: algún proyecto se convirtió en bloque de código")
    # Cada proyecto es un <h3> seguido de su descripción. La descripción se
    # acorta para que la lista no quede sin fin, y al acortarla se pasó a
    # cortar palabras a mitad: 48 de las 73 entradas acababan en "detectar posi"
    # o "validación cr". Se comprueba que ninguna descripción termine a media
    # frase y que ninguna pase del largo que dice la configuración.
    entradas = re.findall(r"<h3[^>]*>.*?</h3>\s*(.*?)(?=<h3|</div>|\Z)",
                          interior, re.S)
    sin_frase = []
    demasiado_largo = []
    sin_texto = []
    for trozo in entradas:
        # La descripción es lo que va entre el </h3> y el siguiente <h3>, sin
        # las etiquetas: el texto es lo que se lee en la página. Las entidades
        # se deshacen antes de medir, porque "ATT&amp;CK" ocupa 10 caracteres
        # en el archivo y "ATT&CK" son 6 los que lee el lector; sin deshacerlo,
        # esa descripción parecía 4 caracteres más larga de lo que es.
        desc = re.sub(r"<[^>]+>", " ", trozo)
        desc = re.sub(r"\s+", " ", unescape(desc)).strip()
        if not desc:
            sin_texto.append("una entrada sin descripción")
            continue
        if len(desc) > contexto.LARGO_DESCRIPCION:
            demasiado_largo.append(f"{len(desc)} caracteres")
        if desc[-1] not in ".!?\"'…)":
            sin_frase.append(desc[-24:] + "…")
    revisar(not sin_texto,
            f"alguna entrada del índice se quedó sin descripción "
            f"({len(sin_texto)}): {'; '.join(sin_texto[:5])}")
    revisar(not demasiado_largo,
            f"alguna descripción pasa de los "
            f"{contexto.LARGO_DESCRIPCION} caracteres "
            f"({len(demasiado_largo)}): "
            f"{'; '.join(demasiado_largo[:5])}")
    revisar(not sin_frase,
            f"{len(sin_frase)} descripciones del índice quedan cortadas a "
            f"media palabra (tienen que acabar en punto o similar): "
            f"{'; '.join(sin_frase[:5])}")
revisar('id="buscar-proyecto"' in indice, "índice: falta el campo de búsqueda")
revisar('id="lista-proyectos-vacio"' in indice, "índice: falta el aviso de vacío")

# --- 4-bis. El número de proyectos, el mismo en todos los lados --------------
# El total aparece en el antetítulo, en la cifra grande, en la etiqueta de la
# cifra, en el texto del buscador, en el contador y en el botón del 404. Cuando
# el repositorio creció de 73 a 74, cinco de esos seis seguían diciendo 73 y
# nadie se dio cuenta: el sitio no se rompe, solo miente. Ahora se comparan
# todos contra el número de la configuración.
patron_numero = re.compile(r"\b(\d{1,4})\s+proyectos\b", re.I)
for html in sorted(RAIZ.rglob("*.html")):
    rel = html.relative_to(RAIZ)
    texto = re.sub(r"<[^>]+>", " ", html.read_text(encoding="utf-8",
                                                    errors="replace"))
    for numero in patron_numero.findall(texto):
        revisar(int(numero) == contexto.PROYECTOS,
                f"{rel}: dice '{numero} proyectos' y el índice tiene "
                f"{contexto.PROYECTOS}")

# --- 5. Enlaces y anclas internas ------------------------------------------
id_de_html = re.compile(r'\bid="([^"]+)"')
for html in sorted(RAIZ.rglob("*.html")):
    rel = html.relative_to(RAIZ)
    texto = html.read_text(encoding="utf-8", errors="replace")
    ids = set(id_de_html.findall(texto))
    for ancla in set(re.findall(r'href="#([^"]+)"', texto)):
        revisar(ancla in ids, f"{rel}: ancla rota #{ancla}")

    for src in re.findall(r'<img[^>]+src="([^"]+)"', texto):
        if src.startswith(("http://", "https://", "//")):
            avisos.append(f"{rel}: imagen externa {src}")

# --- 6. Hojas de estilo de página ------------------------------------------
for pagina in ("indice", "red-team", "programacion", "herramientas",
               "sobre-mi", "novedades"):
    archivo = RAIZ / pagina / "index.html"
    revisar(archivo.exists(), f"falta la página /{pagina}/")

# --- salida -----------------------------------------------------------------
if avisos:
    print("AVISOS")
    for a in avisos:
        print("  - " + a)
if problemas:
    print("FALLAS")
    for p in problemas:
        print("  - " + p)
    sys.exit(1)
print("todo en orden")
