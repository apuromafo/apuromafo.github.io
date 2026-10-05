"""Configuración compartida de las auditorías.

Por qué existe: las auditorías son programas sueltos que se pueden correr solos
para depurar (`python utilidades/auditorias/revisar_visual.py`) o desde el CLI
(`ap.py audit visual`). Si cada uno llevara la ruta del repositorio, la del
servidor y el puerto escritos dentro, habría que editarlos cada vez que se
mueve algo, y además se perderían al limpiar la carpeta temporal, que es donde
vivid antes.

De dónde sale cada cosa, en orden de prioridad:

    1. variable de entorno (AP_REPO, AP_BUILD, AP_PUERTO, AP_CAPTURAS)
    2. lo que se pasó por la línea de comandos, que el CLI traduce a esas
       mismas variables
    3. el valor de ap.config.json

El módulo no avisa ni imprime: solo lee. Si algo está mal, avisa con un mensaje
y sale con el código 2, que es el de "no se pudo ni empezar", para que no salga
una traza de Python en medio del trabajo.
"""

import json
import os
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
CONFIG = AQUI.parent / "ap.config.json"

#: Código de salida para "no se pudo arrancar": falta la configuración, está
#: mal escrita, o falta una carpeta que debería estar.
CODIGO_SIN_ARRANQUE = 2

_CLAVES = ("repositorio", "build", "capturas", "ruby", "servidor",
           "paginas", "anchos", "temas", "grupos", "movil", "auditorias")


def _fallar(mensaje):
    print("ap: " + mensaje, file=sys.stderr)
    print("     el archivo de configuración es " + str(CONFIG), file=sys.stderr)
    raise SystemExit(CODIGO_SIN_ARRANQUE)


def cargar():
    """Lee ap.config.json y devuelve el diccionario, comprobando que esté.

    Se comprueba bloque por bloque porque un JSON con un punto y coma de más
    devuelve un error que no dice qué parte del archivo es la que se rompió, y
    en un archivo de configuración eso es justo lo que uno quiere saber.
    """
    if not CONFIG.is_file():
        _fallar("no existe el archivo de configuración")
    try:
        datos = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fallar("el archivo de configuración no es JSON válido "
                f"(línea {e.lineno}, columna {e.colno}): {e.msg}")
    if not isinstance(datos, dict):
        _fallar("el archivo de configuración debería ser un objeto")

    faltan = [k for k in _CLAVES if k not in datos]
    if faltan:
        _fallar("al archivo de configuración le falta: " + ", ".join(faltan))
    for bloque in ("ruby", "servidor"):
        for k in ("bin", "msys") if bloque == "ruby" else ("host", "puerto"):
            if k not in datos[bloque]:
                _fallar(f"dentro de '{bloque}' falta '{k}'")
    for clave in ("paginas", "anchos", "temas", "auditorias"):
        if not isinstance(datos[clave], list) or not datos[clave]:
            _fallar(f"'{clave}' tiene que ser una lista con al menos un elemento")
    if not isinstance(datos["movil"], dict):
        _fallar("'movil' tiene que ser un bloque con la clave 'perfil' y los "
                "límites del teléfono")
    for k in ("perfil", "ancho_mas_estrecho", "minimo_area_tactil"):
        if k not in datos["movil"]:
            _fallar(f"dentro de 'movil' falta '{k}'")
    for p in datos["paginas"]:
        if "nombre" not in p or "ruta" not in p:
            _fallar("cada página necesita 'nombre' y 'ruta': " + str(p))
    for a in datos["anchos"]:
        if not all(k in a for k in ("nombre", "ancho", "alto")):
            _fallar("cada ancho necesita 'nombre', 'ancho' y 'alto': " + str(a))
    for a in datos["auditorias"]:
        if not all(k in a for k in ("nombre", "titulo", "script")):
            _fallar("cada auditoría necesita 'nombre', 'titulo' y 'script': "
                    + str(a))
    # Un grupo con un nombre de página que no existe no produciría un error
    # visible: la auditoría simplemente miraría menos páginas de las que cree.
    nombres = {p["nombre"] for p in datos["paginas"]}
    for grupo, lista in datos["grupos"].items():
        if not isinstance(lista, list) or not lista:
            _fallar(f"el grupo '{grupo}' tiene que ser una lista no vacía")
        for nombre in lista:
            if nombre not in nombres:
                _fallar(f"el grupo '{grupo}' pide la página '{nombre}', que no "
                        "está en la lista de páginas")
    return datos


CFG = cargar()


def _ruta(clave, por_omision):
    """Una ruta de la configuración, con la variable de entorno por encima."""
    return pathlib.Path(os.environ.get(clave) or CFG[por_omision])


#: Carpeta del repositorio: donde están los fuentes, no la compilación.
REPO = _ruta("AP_REPO", "repositorio")

#: Carpeta donde jekyll build deja el sitio.
BUILD = _ruta("AP_BUILD", "build")

#: Donde revisar_visual deja las capturas.
CAPTURAS = _ruta("AP_CAPTURAS", "capturas")

#: Lo que necesitan las auditorías de Ruby.
RUBY_BIN = pathlib.Path(CFG["ruby"]["bin"])
RUBY_MSYS = pathlib.Path(CFG["ruby"]["msys"])

#: El servidor estático de revisión.
HOST = CFG["servidor"]["host"]
PUERTO = int(os.environ.get("AP_PUERTO") or CFG["servidor"]["puerto"])
BASE = f"http://{HOST}:{PUERTO}"

#: Las páginas, en el formato que usan los bucles: (nombre, ruta).
PAGINAS = [(p["nombre"], p["ruta"]) for p in CFG["paginas"]]

#: Las direcciones de cada página por nombre, para las auditorías que apuntan a
#: una página concreta (la entrada del blog, que cambia de dirección cada vez que
#: se le cambia la fecha o el título).
RUTAS = {p["nombre"]: p["ruta"] for p in CFG["paginas"]}


def en_paginas(nombres):
    """[(nombre, ruta)] para un grupo de páginas de la configuración."""
    return [(n, RUTAS[n]) for n in nombres]

#: Los anchos del barrido general: (nombre, ancho, alto).
ANCHOS = [(a["nombre"], a["ancho"], a["alto"]) for a in CFG["anchos"]]

#: Los esquemas de color que se revisan.
TEMAS = list(CFG["temas"])

#: Subconjuntos de páginas que usan algunas auditorías: grupo -> [(nombre, ruta)]
GRUPOS = {g: en_paginas(lista) for g, lista in CFG["grupos"].items()}

#: La hoja de diseño, para las comprobaciones que la leen como texto.
CSS = REPO / "assets" / "css" / "apuromafo.css"

#: Cuántas entradas debe tener el índice (y cuántas carpetas numeradas tiene el
#: Repositorio Python). Vive en la configuración y no en el código: el sitio lo
#: enseña en varios lugares a la vez, y con el número escrito en tres scripts
#: basta con agregar un proyecto para que uno de los tres se quede atrás.
PROYECTOS = int(CFG["cifras"]["proyectos"])

#: Cuánto puede medir de largo la descripción de un proyecto antes de que se
#: considere cortada. Es el techo del que salió el corte de palabras.
LARGO_DESCRIPCION = int(CFG["cifras"]["largo_maximo_descripcion"])


def ruta_de_auditoria(script):
    """La ruta de una auditoría del registro, o None si el archivo no está.

    Que falte el archivo es un error de instalación de la herramienta, no del
    sitio, así que se avisa con un mensaje claro en vez de una traza.
    """
    ruta = AQUI / script
    if not ruta.is_file():
        _fallar("el registro dice que existe " + script + " pero no está en "
                + str(AQUI))
    return ruta


if __name__ == "__main__":
    # Ejecutarlo a mano sirve para ver qué está leyendo de verdad, que es la
    # pregunta que aparece en cuanto algo apunta a la carpeta equivocada.
    print("configuración: " + str(CONFIG))
    for etiqueta, valor in (
        ("repositorio", REPO), ("build", BUILD), ("capturas", CAPTURAS),
        ("ruby bin", RUBY_BIN), ("ruby msys", RUBY_MSYS),
        ("hoja de diseño", CSS),
    ):
        existe = "existe" if pathlib.Path(valor).exists() else "NO EXISTE"
        print(f"  {etiqueta:16} {valor}   ({existe})")
    print(f"  {'servidor':16} {BASE}   (puerto {PUERTO})")
    print(f"  páginas         {len(PAGINAS)}")
    print(f"  anchos          {', '.join(f'{n} {a}x{b}' for n, a, b in ANCHOS)}")
    print(f"  temas           {', '.join(TEMAS)}")
    print(f"  perfil móvil    {CFG['movil']['perfil']}")
    for a in CFG["auditorias"]:
        archivo = aqui = AQUI / a["script"]
        marca = "" if archivo.is_file() else "   NO EXISTE"
        print(f"  auditoría {a['nombre']:11} {a['script']}{marca}")
