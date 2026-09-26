#!/usr/bin/env python3
"""Convierte los SVG de Font Awesome en lo que el sitio necesita para dibujar
iconos, sin depender de ninguna fuente externa.

Por qué existe: el sitio dibuja sus iconos con SVG en línea en vez de con una
fuente de iconos alojada en otro sitio. Así no hay peticiones a terceros ni un
salto de iconos mientras carga la página. Este script deja registrado de dónde
salió cada trazado y permite rehacerlo.

Genera dos archivos:

  _data/apuromafo_iconos.yml   los trazados, para el include apuromafo/icono.html
  assets/css/iconos-tema.css    los mismos trazados como máscara, para los iconos
                                que escribe el tema con clases de Font Awesome
                                (el perfil de autor, el pie, la tabla de
                                contenido). Con esto el sitio no necesita ni la
                                CDN ni copiar ningún include del tema.

Uso:
    curl -sSfL -o fa.tar.gz \\
      https://codeload.github.com/FortAwesome/Font-Awesome/tar.gz/refs/heads/6.x
    tar -xzf fa.tar.gz --strip-components=2 -C fa FontAwesome-Font-Awesome-6.x/svgs
    python utilidades/generar_iconos.py fa

Iconos: Font Awesome Free 6 (CC BY 4.0), Copyright Fonticons, Inc.
"""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ORIGEN = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("fa")
DATOS = RAIZ / "_data" / "apuromafo_iconos.yml"
HOJA = RAIZ / "assets" / "css" / "iconos-tema.css"

# `nombre que pide el sitio` -> `carpeta/archivo` dentro de los SVG de Font Awesome.
# Los que llevan el nombre viejo de Font Awesome 5 son los que escribe el tema
# (Minimal Mistakes 4.26.2); el resto son los que usa el contenido.
ICONOS = {
    "arrow-right": "solid/arrow-right",
    "arrow-up": "solid/arrow-up",
    "book": "solid/book",
    "cap": "solid/graduation-cap",
    "chevron-right": "solid/chevron-right",
    "code": "solid/code",
    "crosshairs": "solid/crosshairs",
    "flag": "solid/flag",
    "github": "brands/github",
    "globe": "solid/globe",
    "instagram": "brands/instagram",
    "linkedin": "brands/linkedin",
    "list": "solid/list",
    "moon": "solid/moon",
    "rss": "solid/rss",
    "search": "solid/magnifying-glass",
    "shield": "solid/shield-halved",
    "sun": "solid/sun",
    "telegram": "brands/telegram",
    "terminal": "solid/terminal",
    "x-twitter": "brands/x-twitter",
    "xmark": "solid/xmark",
    # --- los que escribe el tema, con su nombre de Font Awesome 5 ---
    "calendar-alt": "solid/calendar-days",
    "file-alt": "solid/file-lines",
    "link": "solid/link",
    "map-marker-alt": "solid/map-location-dot",
    "rss-square": "solid/rss",
}

COMENTARIO = re.compile(r"<!--.*?-->", re.S)
ESPACIOS = re.compile(r"\s+")
ANCHO = 88

CABECERA_YAML = """\
# Generado por utilidades/generar_iconos.py — no editar a mano.
# Font Awesome Free 6 (CC BY 4.0), Copyright Fonticons, Inc.
# El sitio los pinta con currentColor: el color lo pone el CSS.
#
# Cada cuerpo va en bloque literal (|-) y nunca se parte en mitad de un número:
# un "-1.6" partido en dos renglones ("-1." + "6") convierte el trazado en
# basura y el icono desaparece sin avisar. generar_iconos.py lo comprueba.
"""

CABECERA_CSS = """\
/* ===========================================================================
   Iconos que escribe el tema — generado por utilidades/generar_iconos.py
   ===========================================================================
   Minimal Mistakes dibuja algunos iconos con clases de Font Awesome 5
   (el perfil de autor, el pie, la tabla de contenido). El sitio ya no carga
   la CDN de Font Awesome, así que aquí se vuelve a pintar cada uno como
   máscara: así hereda el color del texto, sirve en tema claro y oscuro, y no
   hace falta copiar ningún include del tema.

   Cada icono es un ::before con el color actual y el trazado de máscara. Si
   algún día el tema escribe un icono que no está en esta lista, simplemente no
   se verá: por eso conviene revisar la lista al actualizar el tema.

   Font Awesome Free 6 (CC BY 4.0), Copyright Fonticons, Inc.
   =========================================================================== */
"""


def cuerpo_de(svg: str) -> tuple[str, str]:
    """Devuelve (viewBox, contenido interno) del SVG, sin espacios dobles."""
    if "<svg" not in svg or "</svg>" not in svg:
        raise SystemExit("el archivo no parece un SVG")
    caja = re.search(r'viewBox="([^"]+)"', svg)
    if not caja:
        raise SystemExit("SVG sin viewBox")
    interior = svg[svg.index(">", svg.index("<svg")) + 1: svg.rindex("</svg>")]
    return caja.group(1), ESPACIOS.sub(" ", COMENTARIO.sub("", interior)).strip()


def partir_por_palabras(texto: str, ancho: int = ANCHO) -> list[str]:
    """Parte el texto en renglones de unos `ancho` caracteres, sin partir nunca
    una palabra. Un salto dentro de un número rompe el trazado."""
    renglones, actual = [], ""
    for palabra in texto.split(" "):
        if actual and len(actual) + 1 + len(palabra) > ancho:
            renglones.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}" if actual else palabra
    if actual:
        renglones.append(actual)
    return renglones


def comprobar(cuerpo: str, renglones: list[str]) -> None:
    """El texto parts mañana tiene que ser el mismo que el de hoy, salvo los
    espacios. Es lo que garantiza que ningún número quede partido."""
    joined = " ".join(renglones)
    if ESPACIOS.sub(" ", joined) != ESPACIOS.sub(" ", cuerpo):
        raise SystemExit("el reparto de renglones cambió el trazado; revisa ANCHO")


def url_para_mascara(viewbox: str, cuerpo: str) -> str:
    """Arma el data-URI de un SVG mínimo, apto para url() de una máscara."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">'
           f"{cuerpo}</svg>")
    # Rompen un data-URI dentro de url("..."): el propio símbolo de porcentaje,
    # las comillas, el almohadón (#, que abre un color), y los signos de
    # menor y mayor.
    for viejo, nuevo in (("%", "%25"), ("#", "%23"), ('"', "'"),
                         ("<", "%3C"), (">", "%3E"), ("\n", " ")):
        svg = svg.replace(viejo, nuevo)
    return "data:image/svg+xml," + svg


def main() -> None:
    faltantes = [n for n, ruta in ICONOS.items()
                 if not (ORIGEN / f"{ruta}.svg").exists()]
    if faltantes:
        raise SystemExit("Faltan: " + ", ".join(sorted(faltantes)))

    yml = [CABECERA_YAML]
    css = [CABECERA_CSS]
    reglas = []

    for nombre in sorted(ICONOS):
        fuente = (ORIGEN / f"{ICONOS[nombre]}.svg").read_text("utf-8")
        viewbox, cuerpo = cuerpo_de(fuente)
        renglones = partir_por_palabras(cuerpo)
        comprobar(cuerpo, renglones)

        yml.append(f"{nombre}:")
        yml.append(f'  viewBox: "{viewbox}"')
        yml.append("  cuerpo: |-")
        yml += [f"    {r}" for r in renglones]
        yml.append("")

        reglas.append(f'  [class~="fa-{nombre}"]::before {{')
        reglas.append("    -webkit-mask: url("
                      f'"{url_para_mascara(viewbox, cuerpo)}") '
                      "no-repeat center / contain;")
        reglas.append(f'    mask: url("{url_para_mascara(viewbox, cuerpo)}") '
                      "no-repeat center / contain;")
        reglas.append("  }")

    css += [
        ".fa-tema::before,",
        "[class*='fa-']::before {",
        "  content: '';",
        "  display: inline-block;",
        "  width: 1.05em;",
        "  height: 1.05em;",
        "  background-color: currentColor;",
        "  vertical-align: -0.16em;",
        "}",
        "",
    ]
    css += reglas
    css += [
        "",
        "/* Los iconos del tema que no están en la lista (por ejemplo los de",
        "   redes sociales que el autor no usa) se quedan sin dibujo, pero sin",
        "   ocupar espacio raro: el <i> vacío no empuja nada. */",
        "[class*='fa-']:empty {",
        "  display: inline-block;",
        "}",
        "",
    ]

    DATOS.parent.mkdir(parents=True, exist_ok=True)
    DATOS.write_text("\n".join(yml), encoding="utf-8", newline="\n")
    HOJA.parent.mkdir(parents=True, exist_ok=True)
    HOJA.write_text("\n".join(css), encoding="utf-8", newline="\n")

    print(f"OK  {DATOS.name}  ({len(ICONOS)} iconos)")
    print(f"OK  {HOJA.name}  ({len(reglas) // 4} reglas de máscara)")


if __name__ == "__main__":
    main()
