#!/usr/bin/env python3
"""Línea de comandos del sitio.

    python utilidades/ap.py <comando> [opciones]

Un solo punto de entrada para lo que se hacía a mano: compilar el sitio,
levantar el servidor de revisión y correr las auditorías. Antes cada cosa era
un comando que había que acordarse, con el PATH de Ruby escrito a mano y el
puerto repetido en cada auditoría; ahora todo sale de ap.config.json y las
opciones de la línea de comandos pisan lo que haga falta.

Comandos:

    build       compila el sitio con Jekyll
    serve       levanta el servidor de revisión (--dejar lo deja corriendo,
                --detener lo para)
    audit       corre auditorías (con nombre: solo esas)
    doctor      dice si el entorno está en condiciones de trabajar
    estado      dice dónde se está: repositorio, compilación, servidor, git
    todo        build + serve --dejar + audit, que es el ciclo completo
    iconos      rehace los iconos SVG y las máscaras del tema
    favicon     rehace el favicon de iOS y /favicon.ico

Códigos de salida: 0 todo bien, 1 se encontró algo, 2 no se pudo ni empezar
(la configuración, una ruta o una dependencia falta).

Opciones que pisan la configuración en todos los comandos:
    --repo RUTA        --build CARPETA    --puerto N    --capturas CARPETA
"""

import argparse
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "auditorias"))

import contexto  # noqa: E402  (necesita estar en la ruta antes de nada)

#: Dónde se guarda el número de proceso del servidor que quedó corriendo. En la
#: carpeta temporal y no en el repo: es estado de la máquina, no del proyecto.
PID = pathlib.Path(os.environ.get("TEMP", ".")) / "apuromafo-servidor.pid"
LOG = pathlib.Path(os.environ.get("TEMP", ".")) / "apuromafo-servidor.log"


# --------------------------------------------------------------------------
# Ayudas
# --------------------------------------------------------------------------
def titulo(texto):
    print()
    print("== " + texto + " " + "=" * max(4, 62 - len(texto)))


def con_ruby():
    """El entorno con Ruby y Jekyll en el PATH, para este proceso y sus hijos.

    Ruby no está en el PATH del sistema, así que sin esto no hay forma de
    compilar salvo acordarse del one-liner en cada terminal.
    """
    entorno = dict(os.environ)
    partes = [str(contexto.RUBY_BIN), str(contexto.RUBY_MSYS)]
    if entorno.get("PATH"):
        partes.append(entorno["PATH"])
    entorno["PATH"] = os.pathsep.join(partes)
    return entorno


def ruby(*args):
    """Ruby con la ruta completa.

    En Windows, subprocess busca el ejecutable con el PATH del proceso que llama,
    no con el del entorno que se le pasa: poner la carpeta en el entorno no
    alcanza para que aparezca `ruby`. Con la ruta completa no hay que depender
    de eso.
    """
    return [str(contexto.RUBY_BIN / "ruby.exe"), *args]


def lanzador_jekyll():
    """El lanzador de Jekyll de la instalación de Ruby, o None si no está.

    `jekyll` a secas es el script de Ruby; el lanzador de Windows es un .bat (o
    .cmd, según cómo se instaló) y Windows no ejecuta un .bat sin pasar por
    cmd.exe. Se busca el que exista en vez de escribir el nombre fijo, porque
    depende de la instalación.
    """
    for nombre in ("jekyll.bat", "jekyll.cmd"):
        ruta = contexto.RUBY_BIN / nombre
        if ruta.is_file():
            return ruta
    return None


def jekyll(*args):
    """Jekyll con la ruta completa, a través de cmd."""
    lanzador = lanzador_jekyll()
    if lanzador is None:
        raise FileNotFoundError(
            "no hay lanzador de Jekyll (ni jekyll.bat ni jekyll.cmd) en "
            + str(contexto.RUBY_BIN)
            + ". La ruta de Ruby en ap.config.json puede estar mal.")
    return ["cmd", "/c", str(lanzador), *args]


def puerto_escuchando(puerto, host="127.0.0.1"):
    """True si algo está escuchando en ese puerto."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        return s.connect_ex((host, puerto)) == 0


def pedir(pagina, segundos=4):
    """True si la página responde. Se usa un GET de verdad, no un ping."""
    try:
        with urllib.request.urlopen(pagina, timeout=segundos) as r:
            return 200 <= r.status < 400
    except (urllib.error.URLError, OSError, ValueError):
        return False


def proceso_servidor():
    """El PID guardado, si además el proceso sigue escuchando en el puerto."""
    if not PID.is_file():
        return None
    try:
        pid = int(PID.read_text(encoding="utf-8").strip())
    except ValueError:
        return None
    return pid if puerto_escuchando(contexto.PUERTO) else None


def pasar_entorno(args):
    """Traduce las opciones de la línea de comandos a variables de entorno.

    Las auditorías leen la configuración con esa precedencia, así que no hace
    falta que cada una acepte sus propios argumentos: sirve para cualquiera,
    también para las que se agreguen después.
    """
    entorno = dict(os.environ)
    if getattr(args, "repo", None):
        entorno["AP_REPO"] = str(pathlib.Path(args.repo).resolve())
    if getattr(args, "build", None):
        entorno["AP_BUILD"] = str(pathlib.Path(args.build).resolve())
    if getattr(args, "capturas", None):
        entorno["AP_CAPTURAS"] = str(pathlib.Path(args.capturas).resolve())
    if getattr(args, "puerto", None):
        entorno["AP_PUERTO"] = str(args.puerto)
    return entorno


def hace_cuanto(segundos):
    if segundos < 90:
        return "hace menos de un minuto"
    if segundos < 5400:
        return f"hace {segundos / 60:.0f} min"
    if segundos < 172800:
        return f"hace {segundos / 3600:.1f} h"
    return f"hace {segundos / 86400:.1f} días"


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def cmd_build(args, entorno):
    if not contexto.REPO.is_dir():
        print("ap: el repositorio no está en " + str(contexto.REPO),
              file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE
    if lanzador_jekyll() is None:
        print("ap: en " + str(contexto.RUBY_BIN) + " no está Jekyll (ni "
              "jekyll.bat ni jekyll.cmd).\n"
              "     Ruby tampoco está en el PATH del sistema, así que esta ruta "
              "tendría que estar bien puesta en ap.config.json", file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE

    destino = pathlib.Path(args.build or contexto.BUILD)
    titulo("compilando en " + str(destino))
    print("  el tema es remoto: necesita internet y tarda entre 5 y 30 segundos")
    inicio = time.time()
    proceso = subprocess.run(
        jekyll("build", "--destination", str(destino)),
        cwd=str(contexto.REPO), env=entorno)
    dt = time.time() - inicio
    if proceso.returncode != 0:
        print(f"\nap: la compilación falló (Jekyll salió con "
              f"{proceso.returncode}) después de {dt:.0f} s", file=sys.stderr)
        return proceso.returncode
    print(f"  listo en {dt:.0f} s")

    # Comprobar que la carpeta es un sitio de verdad y no quedó a medias.
    faltan = [p for p in ("index.html", "blog/index.html")
              if not (destino / pathlib.PurePosixPath(p)).is_file()]
    if faltan:
        print("ap: la compilación terminó pero faltan: " + ", ".join(faltan),
              file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE
    return 0


# --------------------------------------------------------------------------
# serve
# --------------------------------------------------------------------------
def cmd_serve(args, entorno):
    if args.detener:
        return detener_servidor()

    destino = pathlib.Path(args.build or contexto.BUILD)
    if not destino.is_dir():
        print("ap: no hay nada que servir en " + str(destino)
              + "\n     primero:  ap.py build", file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE
    if puerto_escuchando(contexto.PUERTO):
        print(f"ap: el puerto {contexto.PUERTO} ya está ocupado. Puede ser el "
              "servidor de antes o cualquier otra cosa.\n"
              "     para pararlo:  ap.py serve --detener", file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE

    comando = [sys.executable, "-m", "http.server", str(contexto.PUERTO),
               "--bind", contexto.HOST, "--directory", str(destino)]
    titulo(f"sirviendo {destino} en {contexto.BASE}")

    if args.dejar:
        with LOG.open("w", encoding="utf-8") as salida:
            hijo = subprocess.Popen(
                comando, stdout=salida, stderr=salida,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        PID.write_text(str(hijo.pid), encoding="utf-8")
        for _ in range(30):
            if pedir(contexto.BASE + "/"):
                break
            time.sleep(0.2)
        print(f"  quedó corriendo (proceso {hijo.pid}), registro en {LOG}")
        print("  para pararlo:  ap.py serve --detener")
    else:
        print("  para pararlo: Ctrl+C")
        try:
            subprocess.run(comando)
        except KeyboardInterrupt:
            print()
    return 0


def detener_servidor():
    if not PID.is_file():
        print("ap: no hay ningún servidor registrado por ap.py")
        return 1
    pid = proceso_servidor()
    if pid is None:
        PID.unlink()
        print("ap: el servidor ya no estaba corriendo; se borró el registro")
        return 0
    try:
        os.kill(pid, 15)
    except OSError as e:
        print(f"ap: no se pudo parar el proceso {pid}: {e}", file=sys.stderr)
        return 1
    PID.unlink()
    print(f"ap: servidor detenido (proceso {pid})")
    return 0


# --------------------------------------------------------------------------
# audit
# --------------------------------------------------------------------------
def cmd_audit(args, entorno):
    registro = {a["nombre"]: a for a in contexto.CFG["auditorias"]}
    if args.nombres:
        desconocidos = [n for n in args.nombres if n not in registro]
        if desconocidos:
            print("ap: no conozco la auditoría " + ", ".join(desconocidos),
                  file=sys.stderr)
            print("     las que hay: " + ", ".join(sorted(registro)),
                  file=sys.stderr)
            return contexto.CODIGO_SIN_ARRANQUE
        elegidas = [registro[n] for n in args.nombres]
    else:
        elegidas = list(contexto.CFG["auditorias"])

    faltan_red = [a["nombre"] for a in elegidas
                  if a.get("red") and not pedir(contexto.BASE + "/")]
    if faltan_red:
        print("ap: el servidor no contesta en " + contexto.BASE + "\n"
              + "  necesitan servidor: " + ", ".join(faltan_red) + "\n"
              "  el sitio se compila aparte del servidor, así que para "
              "levantarlo:\n"
              "      ap.py build\n"
              "      ap.py serve --dejar", file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE

    fallos = []
    for a in elegidas:
        script = contexto.ruta_de_auditoria(a["script"])
        titulo(f"auditoría {a['nombre']}: {a['titulo']}")
        inicio = time.time()
        codigo = subprocess.run(
            [sys.executable, str(script)], env=entorno).returncode
        dt = time.time() - inicio
        if codigo == contexto.CODIGO_SIN_ARRANQUE:
            print("\nap: se cortó: la auditoría no pudo ni empezar",
                  file=sys.stderr)
            return codigo
        if codigo == 1:
            fallos.append(a["nombre"])
        print(f"  [{a['nombre']}: {dt:.0f} s, salida {codigo}]")

    titulo("resumen")
    for a in elegidas:
        print(f"  {a['nombre']:12} "
              + ("FALLAS" if a["nombre"] in fallos else "bien"))
    if fallos:
        print("\n  con fallas: " + ", ".join(fallos))
        return 1
    print("\n  todo en orden")
    return 0


# --------------------------------------------------------------------------
# doctor
# --------------------------------------------------------------------------
def cmd_doctor(args, entorno):
    revisado = []

    def fila(ok, etiqueta, detalle=""):
        revisado.append(ok)
        print(f"  [{'ok  ' if ok else 'FALLA'}] {etiqueta:24} {detalle}")

    titulo("entorno")
    fila(contexto.REPO.is_dir(), "repositorio", str(contexto.REPO))
    fila((contexto.REPO / "_config.yml").is_file(), "proyecto Jekyll",
         "_config.yml")
    fila(contexto.RUBY_BIN.is_dir(), "ruby (bin)", str(contexto.RUBY_BIN))
    fila(contexto.RUBY_MSYS.is_dir(), "ruby (msys)", str(contexto.RUBY_MSYS))
    if contexto.RUBY_BIN.is_dir():
        v = subprocess.run(ruby("--version"), capture_output=True,
                           text=True, env=entorno)
        fila(v.returncode == 0, "ruby responde",
             v.stdout.strip() if v.returncode == 0 else v.stderr.strip()[:60])
        j = subprocess.run(jekyll("--version"), capture_output=True,
                           text=True, env=entorno)
        fila(j.returncode == 0, "jekyll",
             j.stdout.strip() if j.returncode == 0 else j.stderr.strip()[:60])
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        fila(True, "playwright", "importable")
    except Exception as e:  # noqa: BLE001 - aquí importa ver cualquier fallo
        fila(False, "playwright", str(e)[:60])

    titulo("carpetas")
    build = pathlib.Path(args.build or contexto.BUILD)
    fila(build.is_dir(), "compilación", str(build))
    if (build / "index.html").is_file():
        dt = time.time() - (build / "index.html").stat().st_mtime
        fila(True, "compilación reciente", hace_cuanto(dt))
    elif build.is_dir():
        fila(False, "compilación reciente", "no está index.html")
    fila(contexto.CAPTURAS.parent.is_dir(), "capturas (carpeta madre)",
         str(contexto.CAPTURAS))

    titulo("red")
    ocupado = puerto_escuchando(contexto.PUERTO)
    contesta = pedir(contexto.BASE + "/")
    if not ocupado:
        fila(True, f"puerto {contexto.PUERTO}", "libre")
    elif proceso_servidor() is not None:
        fila(True, f"puerto {contexto.PUERTO}", "con el servidor de ap.py")
    elif contesta:
        # occupied by something else that answers: usable, but ap.py can't stop
        # it, so it says so instead of pretending all is well.
        fila(True, f"puerto {contexto.PUERTO}",
             "OJO: lo tiene otro proceso, no ap.py (contesta, pero ap.py "
             "serve --detener no lo para)")
    else:
        fila(False, f"puerto {contexto.PUERTO}",
             "lo tiene otro proceso y no contesta")
    fila(contesta, "el sitio contesta", contexto.BASE)

    titulo("configuración")
    carpeta_auditorias = pathlib.Path(contexto.__file__).parent
    for a in contexto.CFG["auditorias"]:
        fila((carpeta_auditorias / a["script"]).is_file(),
             "auditoría " + a["nombre"], a["script"])
    for g in contexto.CFG.get("generadores", []):
        fila((AQUI / g["script"]).is_file(), "generador " + g["nombre"],
             g["script"])

    titulo("git")
    g = subprocess.run(["git", "status", "--short", "--branch"],
                       capture_output=True, text=True, cwd=str(contexto.REPO))
    if g.returncode == 0:
        print("  " + (g.stdout.rstrip().replace("\n", "\n  ") or "(árbol limpio)"))
    else:
        fila(False, "estado de git", g.stderr.strip()[:60])

    malos = revisado.count(False)
    titulo("resumen")
    if malos:
        print(f"  {malos} cosa(s) para mirar antes de trabajar")
        return 1
    print("  el entorno está en condiciones")
    return 0


# --------------------------------------------------------------------------
# estado
# --------------------------------------------------------------------------
def cmd_estado(args, entorno):
    titulo("dónde estoy")
    print(f"  repositorio  {contexto.REPO}")
    print(f"  compilación  {contexto.BUILD}")
    print(f"  servidor     {contexto.BASE}"
          + ("   (contesta)" if pedir(contexto.BASE + "/") else "   (no contesta)"))
    pid = proceso_servidor()
    if pid:
        print(f"               proceso {pid}, registro {PID}")
        print("               para pararlo:  ap.py serve --detener")

    titulo("git")
    for comando in (["git", "log", "--oneline", "-5"],
                    ["git", "status", "--short"]):
        salida = subprocess.run(comando, capture_output=True, text=True,
                                cwd=str(contexto.REPO))
        print("  " + (salida.stdout.rstrip().replace("\n", "\n  ") or "(nada)"))

    titulo("compilación")
    build = pathlib.Path(args.build or contexto.BUILD)
    if not build.is_dir():
        print("  no está compilado:  ap.py build")
        return 0
    html = list(build.rglob("*.html"))
    total = sum(p.stat().st_size for p in build.rglob("*") if p.is_file())
    print(f"  {len(html)} páginas, "
          f"{len(list(build.rglob('*.css')))} hojas, "
          f"{len(list(build.rglob('*.js')))} scripts")
    print(f"  {total / 1024:.0f} KB en total")
    nuevo = max((p.stat().st_mtime for p in html), default=0)
    if nuevo:
        print("  la última compilación fue " + hace_cuanto(time.time() - nuevo))
    return 0


# --------------------------------------------------------------------------
# generadores
# --------------------------------------------------------------------------
def cmd_generador(args, entorno, nombre):
    registro = {g["nombre"]: g for g in contexto.CFG.get("generadores", [])}
    if nombre not in registro:
        print("ap: no hay un generador llamado " + nombre, file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE
    g = registro[nombre]
    script = AQUI / g["script"]
    if not script.is_file():
        print(f"ap: falta el script {script}", file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE
    titulo(g["titulo"])
    if g.get("nota"):
        print("  " + g["nota"])
    return subprocess.run(
        [sys.executable, str(script)] + (getattr(args, "resto", None) or []),
        cwd=str(contexto.REPO), env=entorno).returncode


# --------------------------------------------------------------------------
# todo
# --------------------------------------------------------------------------
def cmd_todo(args, entorno):
    print("ciclo completo: compilar, levantar el servidor y revisar")
    codigo = cmd_build(args, entorno)
    if codigo != 0:
        return codigo
    if not puerto_escuchando(contexto.PUERTO):
        codigo = cmd_serve(argparse.Namespace(
            detener=False, dejar=True, build=args.build), entorno)
        if codigo != 0:
            return codigo
    return cmd_audit(args, entorno)


# --------------------------------------------------------------------------
# Armado de la línea de comandos
# --------------------------------------------------------------------------
def construir_parser():
    p = argparse.ArgumentParser(
        prog="ap.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", metavar="comando")

    def comunes(sp, con_capturas=True):
        sp.add_argument("--repo", metavar="RUTA",
                        help="otra copia del repositorio")
        sp.add_argument("--build", metavar="CARPETA",
                        help="otra carpeta de compilación")
        sp.add_argument("--puerto", type=int, metavar="N",
                        help="otro puerto, para el servidor y las auditorías")
        if con_capturas:
            sp.add_argument("--capturas", metavar="CARPETA",
                            help="otra carpeta para las capturas")

    sp = sub.add_parser("build", help="compila el sitio con Jekyll")
    comunes(sp, con_capturas=False)
    sp.set_defaults(func=cmd_build)

    sp = sub.add_parser("serve", help="levanta el servidor de revisión")
    comunes(sp, con_capturas=False)
    grupo = sp.add_mutually_exclusive_group()
    grupo.add_argument("--dejar", action="store_true",
                       help="que siga corriendo al terminar")
    grupo.add_argument("--detener", action="store_true",
                       help="parar el servidor que quedó corriendo")
    sp.set_defaults(func=cmd_serve)

    sp = sub.add_parser("audit", help="corre auditorías (sin nombre: todas)")
    comunes(sp)
    sp.add_argument("nombres", nargs="*", metavar="nombre",
                    help="auditorías concretas; sin esto, todas")
    sp.set_defaults(func=cmd_audit)

    sp = sub.add_parser("doctor", help="si el entorno está en condiciones")
    comunes(sp, con_capturas=False)
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("estado", help="dónde se está")
    comunes(sp, con_capturas=False)
    sp.set_defaults(func=cmd_estado)

    sp = sub.add_parser("todo", help="build + serve --dejar + audit")
    comunes(sp)
    sp.add_argument("nombres", nargs="*", metavar="nombre",
                    help="auditorías concretas; sin esto, todas")
    sp.set_defaults(func=cmd_todo)

    for nombre, ayuda in (("iconos", "rehace los iconos del sitio"),
                         ("favicon", "rehace el favicon")):
        sp = sub.add_parser(nombre, help=ayuda)
        comunes(sp, con_capturas=False)
        sp.add_argument("resto", nargs=argparse.REMAINDER,
                        help="argumentos para el generador")
        sp.set_defaults(func=(lambda a, e, n=nombre: cmd_generador(a, e, n)))

    # Los títulos de los grupos de opciones salen en inglés; la herramienta es
    # en español y una línea en otro idioma se nota más de lo que parece.
    p._positionals.title = "argumentos"
    p._optionals.title = "opciones"
    for sp in sub.choices.values():
        sp._positionals.title = "argumentos"
        sp._optionals.title = "opciones"
    return p


def main(argv=None):
    parser = construir_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return contexto.CODIGO_SIN_ARRANQUE
    entorno = pasar_entorno(args)
    # Los módulos ya leyeron la configuración al importarse; si se pisó algo
    # desde la línea de comandos, se les avisa para que no workable con lo viejo.
    contexto.BASE = f"http://{contexto.HOST}:{contexto.PUERTO}"
    if args.build:
        contexto.BUILD = pathlib.Path(args.build).resolve()
    try:
        return args.func(args, entorno)
    except KeyboardInterrupt:
        print("\nap: interrumpido")
        return 130
    except Exception as e:  # noqa: BLE001 - aquí el mensaje vale más que la traza
        # Un error de Python a medio camino dice "FileNotFoundError" sin decir
        # de qué archivo, que es justo lo que uno necesita saber. Con AP_TRAZA=1
        # sale la traza entera, para cuando de verdad haya que depurar.
        print(f"\nap: {type(e).__name__}: {e}", file=sys.stderr)
        if os.environ.get("AP_TRAZA"):
            raise
        print("     con AP_TRAZA=1 sale la traza completa", file=sys.stderr)
        return contexto.CODIGO_SIN_ARRANQUE


if __name__ == "__main__":
    sys.exit(main())
