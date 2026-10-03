"""Auditoría del riel de las páginas de sección.

Mide, no supone:
  (a) que cada enlace del índice del riel resuelve a un elemento real al
      decodificar el href, y que ese elemento es el título que dice;
  (b) que al leer una sección del medio queda activa exactamente una entrada,
      la correcta, con su clase y su aria-current;
  (c) que arriba del todo no hay ninguna marcada;
  (d) que al final queda activa la última;
  (e) que al hacer clic en un enlace del riel se marca esa entrada en el
      mismo clic (midiendo con un observador, no con una foto) y que cuando el
      salto termina la geometría deja marcada la sección de verdad;
  (f) que no hay errores en la consola;
  (g) que el enlace activo aguanta 4.5:1 contra su fondo, en tema claro y
      oscuro, midiendo el color computado (con el fondo compuesto, porque el
      del enlace es un color-mix con alfa sobre el panel).

Y de paso que no se rompió nada: que las demás páginas no desbordan en
horizontal y que sin JavaScript el riel se ve entero.

Uso:  python utilidades/auditorias/revisar_riel.py [dirección del servidor]
"""

import pathlib
import re
import sys
from urllib.parse import unquote

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

# El primer argumento sigue mandando, pero ya no hace falta acordarse de un
# puerto distinto al del resto: por omisión sale de la configuración.
BASE = sys.argv[1] if len(sys.argv) > 1 else contexto.BASE

# Las tres páginas con riel (las que llevan `toc: true` en el front matter) y
# todas las páginas del sitio, para lo que no es del riel pero se comprueba en
# el mismo rato: que ninguna desborde y que la consola esté limpia.
CON_RIEL = [ruta for _, ruta in contexto.GRUPOS["riel"]]
TODAS = [ruta for _, ruta in contexto.PAGINAS]

fallos = []
notas = []


def chequear(ok, texto, detalle=""):
    print(("  OK   " if ok else "  FALLA") + "  " + texto + ("   " + detalle if detalle else ""))
    if not ok:
        fallos.append(texto + (" | " + detalle if detalle else ""))
    return ok


# --------------------------------------------------------------------------
# Ayudas de color (WCAG 2.x, la misma fórmula de la especificación)
# --------------------------------------------------------------------------
def parse_color(valor):
    """rgba(...) o color(srgb r g b / a) -> (r, g, b, a) con 0-255 y 0-1."""
    if not valor:
        return None
    v = valor.strip().lower()
    if v in ("transparent", "rgba(0, 0, 0, 0)"):
        return (0, 0, 0, 0.0)
    m = re.match(r"rgba?\(([^)]+)\)", v)
    if m:
        partes = [p.strip() for p in re.split(r"[,\s/]+", m.group(1)) if p.strip()]
        nums = []
        for p in partes:
            if p.endswith("%"):
                nums.append(float(p[:-1]) / 100 * 255)
            else:
                nums.append(float(p))
        if len(nums) == 3:
            nums.append(1.0)
        return (nums[0], nums[1], nums[2], nums[3])
    m = re.match(r"color\(srgb\s+([^)]+)\)", v)
    if m:
        p = m.group(1).split("/")
        nums = [float(x) * 255 for x in p[0].split()]
        a = float(p[1]) if len(p) > 1 else 1.0
        return (nums[0], nums[1], nums[2], a)
    return None


def encima(arriba, abajo):
    a = arriba[3]
    if a >= 1:
        return (arriba[0], arriba[1], arriba[2], 1.0)
    return (
        arriba[0] * a + abajo[0] * (1 - a),
        arriba[1] * a + abajo[1] * (1 - a),
        arriba[2] * a + abajo[2] * (1 - a),
        1.0,
    )


def luminancia(rgb):
    def canal(v):
        v = v / 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = canal(rgb[0]), canal(rgb[1]), canal(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(uno, otro):
    l1, l2 = luminancia(uno), luminancia(otro)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


# --------------------------------------------------------------------------
# Fragmento de medición que corre dentro de la página
# --------------------------------------------------------------------------
MEDIR = """() => {
  const parse = (v) => {
    if (!v) return null;
    v = v.trim().toLowerCase();
    if (v === 'transparent' || v === 'rgba(0, 0, 0, 0)') return [0, 0, 0, 0];
    let m = v.match(/rgba?\\(([^)]+)\\)/);
    if (m) {
      const p = m[1].split(/[,\\s/]+/).filter(Boolean).map(Number);
      if (p.length < 3) return null;
      return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
    }
    m = v.match(/color\\(srgb\\s+([^)]+)\\)/);
    if (m) {
      const p = m[1].split('/');
      const n = p[0].trim().split(/\\s+/).map(Number).map((x) => x * 255);
      return [n[0], n[1], n[2], p.length > 1 ? Number(p[1]) : 1];
    }
    return null;
  };
  // Fondo pintado de verdad: se compone el alfa del elemento con el del
  // primer ancestro opaco, en vez de suponer que el panel es blanco.
  const fondoReal = (el) => {
    const pila = [];
    let n = el;
    while (n && n.nodeType === 1) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c) {
        pila.push(c);
        if (c[3] >= 1) break;
      }
      n = n.parentElement;
    }
    let rgb = [255, 255, 255, 1];
    for (let i = pila.length - 1; i >= 0; i--) {
      const a = pila[i][3];
      if (a >= 1) rgb = [pila[i][0], pila[i][1], pila[i][2], 1];
      else rgb = [
        pila[i][0] * a + rgb[0] * (1 - a),
        pila[i][1] * a + rgb[1] * (1 - a),
        pila[i][2] * a + rgb[2] * (1 - a),
        1,
      ];
    }
    return rgb;
  };

  const menu = document.querySelector('.ap-toc__menu');
  const out = {
    hay_menu: !!menu,
    ap_js: document.documentElement.classList.contains('ap-js'),
    scroll_padding_top: getComputedStyle(document.documentElement)
      .scrollPaddingTop,
    entradas: [],
  };
  if (!menu) return out;

  for (const a of menu.querySelectorAll('a[href^="#"]')) {
    out.entradas.push({
      texto: a.textContent.trim(),
      href: a.getAttribute('href'),
      activa: a.classList.contains('es-activo'),
      aria: a.getAttribute('aria-current'),
      peso: getComputedStyle(a).fontWeight,
      color: getComputedStyle(a).color,
      fondo: getComputedStyle(a).backgroundColor,
      fondo_real: fondoReal(a),
      transicion: getComputedStyle(a).transitionDuration,
      visible: a.getClientRects().length > 0,
    });
  }
  return out;
}
"""

BUSCAR_ID = """(id) => {
  if (!id) return null;
  const el = document.getElementById(id);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {
    id: el.id,
    etiqueta: el.tagName,
    texto: (el.childNodes[0] ? el.childNodes[0].textContent : el.textContent)
      .trim(),
    existe: true,
    arriba: r.top,
    scrollY: window.scrollY,
    hasta: document.documentElement.scrollHeight - window.innerHeight,
  };
}
"""

# Ojo: behavior 'auto' NO es "de un salto"; el navegador lo resuelve con el
# scroll-behavior del CSS, que en este sitio es smooth. Para colocar la página
# en un punto exacto hay que anularlo por el estilo del elemento (solo en la
# auditoría, no en el sitio) y después esperar a que el marcador se asiente.
DETENER = """() => {
  document.documentElement.style.scrollBehavior = 'auto';
}
"""

IR_A = """(id) => {
  const el = document.getElementById(id);
  if (!el) return null;
  const linea = parseFloat(
    getComputedStyle(document.documentElement).scrollPaddingTop
  ) || 0;
  const destino = el.getBoundingClientRect().top + window.scrollY - linea;
  window.scrollTo({top: destino, behavior: 'auto'});
  return {id: id, destino: destino, linea: linea};
}
"""

# Para el clic hace falta un testigo, y además saber a qué se compara. La marca
# se pone y se quita en cuestión de milisegundos, así que una foto en un
# instante cualquiera dice muy poco: a los 80 ms el salto apenas ha empezado y
# la página va por 96 de 1037 píxeles, con lo cual la geometría (que es la que
# manda) todavía afirma que no se ha leído nada. Este observador apunta al
# enlace que se va a tocar y apunta tres tiempos, en milisegundos desde que se
# instala: cuándo llegó el clic a la página, cuándo ganó el enlace la clase y
# cuándo la perdió. Con el primero se mide lo que promete el sitio —que el clic
# marca en el mismo clic, sin esperar al scroll— sin depender de lo que tarde el
# navegador ni el propio clic de la auditoría.
VIGILAR = """(href) => {
  const menu = document.querySelector('.ap-toc__menu');
  const a = menu.querySelector('a[href="' + href + '"]');
  const y0 = window.scrollY;
  const r = window.__riel = {
    t0: performance.now(), clic: null, anade: null, quita: null, mueve: null,
  };
  const ahora = () => Math.round(performance.now() - r.t0);
  document.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('a[href^="#"]') === a) {
      r.clic = ahora();
    }
  }, true);
  window.addEventListener('scroll', function () {
    if (r.mueve === null && Math.abs(window.scrollY - y0) > 0.5) {
      r.mueve = ahora();
    }
  }, {passive: true});
  window.__rielObs = new MutationObserver(function () {
    if (a.classList.contains('es-activo')) {
      if (r.anade === null) r.anade = ahora();
    } else if (r.anade !== null && r.quita === null) {
      r.quita = ahora();
    }
  });
  window.__rielObs.observe(a, {attributes: true, attributeFilter: ['class']});
  return !!a;
}
"""

LEER_VIGILIA = """() => {
  if (window.__rielObs) {
    window.__rielObs.disconnect();
  }
  return window.__riel;
}
"""


def asentar(pag, vueltas=40, moviendo_esperado=False):
    """Espera a que window.scrollY deje de moverse (el scroll suave termina).

    Con moviendo_esperado=True primero espera a que la página se mueva de
    verdad. Sin eso pasa esto: el clic se despacha, la auditoría lee scrollY
    otra vez a los 30 ms, los dos valores son 0 porque el scroll suave todavía
    no ha dado su primer fotograma (con la máquina ocupada por la auditoría
    anterior tarda más), y la función devuelve "ya está quieto". Lo que se mide
    entonces es el estado de antes del clic, con la entrada todavía sin marcar.
    Es un fallo de la medición y salía cada dos o tres pasadas en la suite
    completa, que es cuando la máquina está ocupada.

    Devuelve (scrollY, se_movio): si con moviendo_esperado=True la página no se
    mueve en el tiempo dado, se_movio=False y quien llama lo dice, porque eso
    no es un fallo del sitio sino de la comprobación.
    """
    if moviendo_esperado:
        y0 = pag.evaluate("window.scrollY")
        for _ in range(vueltas):
            if abs(pag.evaluate("window.scrollY") - y0) > 0.5:
                break
            pag.wait_for_timeout(30)
        else:
            return y0, False
    quieto = -1
    for _ in range(vueltas):
        y = pag.evaluate("window.scrollY")
        if abs(y - quieto) < 0.5:
            return y, True
        quieto = y
        pag.wait_for_timeout(30)
    return quieto, True



def activos(m):
    return [e for e in m["entradas"] if e["activa"]]


def medir_contraste(m, etiqueta, problemas_contraste):
    for e in m["entradas"]:
        fg = parse_color(e["color"])
        bg = e["fondo_real"]
        if fg is None or bg is None:
            problemas_contraste.append((etiqueta, e["texto"], "color ilegible"))
            continue
        ratio = contraste(fg, bg)
        estado = "OK" if ratio >= 4.5 else "FALLA"
        if ratio < 4.5:
            problemas_contraste.append((etiqueta, e["texto"], f"{ratio:.2f}:1"))
        print(f"       {estado}  {ratio:5.2f}:1  {etiqueta:22s} "
              f"texto={e['color']:22s} fondo={tuple(round(x) for x in bg[:3])}"
              f"{'  [activa]' if e['activa'] else ''}")


def main():
    with sync_playwright() as p:
        nav = p.chromium.launch()

        # ------------------------------------------------------------------
        # Consola: se recoge en todas las páginas
        # ------------------------------------------------------------------
        errores = []
        avisos = []

        def vigilar(pag):
            pag.on("console", lambda msg: (
                errores.append(f"{msg.type}: {msg.text}")
                if msg.type == "error"
                else (avisos.append(msg.text) if msg.type == "warning" else None)
            ))
            pag.on("pageerror", lambda exc: errores.append(f"pageerror: {exc}"))

        for ruta in CON_RIEL:
            print("=" * 78)
            print("PÁGINA " + ruta)
            print("=" * 78)
            ctx = nav.new_context(viewport={"width": 1440, "height": 900})
            pag = ctx.new_page()
            vigilar(pag)
            pag.goto(BASE + ruta, wait_until="load")
            pag.wait_for_timeout(500)

            m = pag.evaluate(MEDIR)
            chequear(m["hay_menu"], "hay índice en el riel")
            if not m["hay_menu"]:
                ctx.close()
                continue
            print(f"  ap-js: {m['ap_js']}   "
                  f"scroll-padding-top: {m['scroll_padding_top']}   "
                  f"entradas: {len(m['entradas'])}")
            chequear(m["ap_js"], "app.js corrió (html.ap-js)")

            # (a) resolución de href --------------------------------------
            print("  (a) cada entrada resuelve a su título")
            resueltos = []
            for e in m["entradas"]:
                crudo = e["href"].lstrip("#")
                decodificado = unquote(crudo)
                el = pag.evaluate(BUSCAR_ID, decodificado)
                if el is None:
                    chequear(False, f"{e['href']} no resuelve al decodificar")
                    continue
                bruto = pag.evaluate(BUSCAR_ID, crudo)
                mismo = el["texto"] == e["texto"] or e["texto"] in el["texto"]
                print(f"       {e['href']}")
                print(f"          crudo={crudo!r} decodificado={decodificado!r} "
                      f"percent-en-el-atributo={'%' in crudo}")
                print(f"          resuelve: crudo={bool(bruto)} decodificado=True "
                      f"-> <{el['etiqueta']}> {el['texto']!r}")
                chequear(
                    mismo and el["etiqueta"] in ("H2", "H3", "H4"),
                    f"{e['href']} apunta al título correcto",
                    f"<{el['etiqueta']}> {el['texto']!r}",
                )
                resueltos.append((e, el))

            # (c) arriba del todo -----------------------------------------
            print("  (c) arriba del todo, antes del primer título")
            pag.evaluate(DETENER)
            pag.evaluate("window.scrollTo({top: 0, behavior: 'auto'})")
            pag.wait_for_timeout(250)
            m = pag.evaluate(MEDIR)
            activos_arriba = activos(m)
            primero = resueltos[0][1]
            linea_px = pag.evaluate(
                "() => parseFloat(getComputedStyle(document.documentElement)"
                ".scrollPaddingTop) || 0"
            )
            print(f"       activas: {len(activos_arriba)}  "
                  f"scrollY={pag.evaluate('window.scrollY')}  "
                  f"primer título a {primero['arriba']}px, línea: {linea_px}px")
            chequear(primero["arriba"] > linea_px,
                     "arriba el primer título está por debajo de la línea",
                     f"{primero['arriba']:.0f}px vs {linea_px}px")
            chequear(len(activos_arriba) == 0,
                     "recién cargado arriba no marca ninguna entrada",
                     f"{len(activos_arriba)} marcadas")

            # (b) sección del medio ---------------------------------------
            print("  (b) sección del medio")
            medio = resueltos[len(resueltos) // 2]
            colocacion = pag.evaluate(IR_A, medio[1]["id"])
            pag.wait_for_timeout(250)
            m = pag.evaluate(MEDIR)
            activos_medio = activos(m)
            donde = pag.evaluate(BUSCAR_ID, medio[1]["id"])
            print(f"       se colocó {colocacion['id']!r} en scrollY="
                  f"{colocacion['destino']:.0f} (línea {colocacion['linea']}px) "
                  f"y quedó a {donde['arriba']:.1f}px del borde")
            for a in activos_medio:
                print(f"       marcada: {a['texto']!r} aria={a['aria']} "
                      f"peso={a['peso']}")
            otros = [e for e in m["entradas"] if e["aria"] is not None and not e["activa"]]
            print(f"       entradas con aria-current: "
                  f"{sum(1 for e in m['entradas'] if e['aria'])}   "
                  f"otras con es-activo: {len(activos_medio)}   "
                  f"marcadas de más: {len(otros)}")
            chequear(abs(donde["arriba"] - colocacion["linea"]) < 2,
                     "el título del medio quedó justo en la línea de referencia",
                     f"{donde['arriba']:.1f}px vs {colocacion['linea']}px")
            chequear(len(activos_medio) == 1,
                     "queda activa exactamente una entrada",
                     f"{len(activos_medio)}")
            if activos_medio:
                a = activos_medio[0]
                chequear(a["texto"] == medio[0]["texto"],
                         "la activa es la sección del medio",
                         f"{a['texto']!r} vs {medio[0]['texto']!r}")
                chequear(a["aria"] == "true",
                         "la activa lleva aria-current=true", str(a["aria"]))
            fuera = [e for e in m["entradas"]
                     if not e["activa"] and e["aria"] is not None]
            chequear(not fuera, "las demás no tienen aria-current",
                     str([e["texto"] for e in fuera]))

            # (d) al final -------------------------------------------------
            print("  (d) al final de la página")
            pag.evaluate("window.scrollTo({top: 1e7, behavior: 'auto'})")
            pag.wait_for_timeout(300)
            m = pag.evaluate(MEDIR)
            activos_fin = activos(m)
            print(f"       activas: {len(activos_fin)}  "
                  f"texto: {[e['texto'] for e in activos_fin]}  "
                  f"scrollY={pag.evaluate('window.scrollY')}")
            chequear(len(activos_fin) == 1 and
                     activos_fin[0]["texto"] == m["entradas"][-1]["texto"],
                     "al final queda activa la última entrada",
                     str([e["texto"] for e in activos_fin]))
            chequear(activos_fin and activos_fin[0]["aria"] == "true",
                     "la última lleva aria-current=true")

            # (e) clic en el riel (con el scroll suave del sitio) ----------
            # El scroll se deja como lo deja el sitio (smooth), que es el caso
            # interesante. Los topes de página de más abajo sí se ponen con scroll
            # instantáneo (DETENER), porque la única manera de caer en el punto
            # exacto que se quiere comprobar es quitar el suave.
            print("  (e) clic en un enlace del riel (con scroll suave)")
            # Primero arriba del todo con scroll instantáneo y esperando a que se
            # asiente: si se dejara el suave del sitio, el recorrido desde el
            # final del apartado (d) seguiría en vuelo y el testigo apuntaría a
            # un movimiento de página que no es el del clic.
            pag.evaluate(DETENER)
            pag.evaluate("window.scrollTo({top: 0, behavior: 'auto'})")
            asentar(pag)
            pag.evaluate(
                "() => { document.documentElement.style.scrollBehavior = ''; }"
            )
            objetivo = resueltos[0][0]
            pag.evaluate(VIGILAR, objetivo["href"])
            pag.click('.ap-toc__menu a[href="' + objetivo["href"] + '"]')
            y, se_movio = asentar(pag, moviendo_esperado=True)
            rastro = pag.evaluate(LEER_VIGILIA)
            m = pag.evaluate(MEDIR)
            activos_clic = activos(m)
            print(f"       el clic llega a los {rastro['clic']} ms, la marca a los "
                  f"{rastro['anade']} ms y se pierde a los {rastro['quita']} ms; "
                  f"la página se mueve a los {rastro['mueve']} ms")
            print(f"       asienta en scrollY={y}; marcadas al final del salto: "
                  f"{[(e['texto'], e['aria']) for e in activos_clic]}")
            chequear(se_movio, "al hacer clic la página se mueve de verdad",
                     "" if se_movio else
                     f"se quedó en scrollY={y}: con el scroll en auto el clic "
                     f"no llegó a moverla y no hay nada que medir")
            chequear(rastro["anade"] is not None and rastro["clic"] is not None
                     and 0 <= rastro["anade"] - rastro["clic"] <= 20,
                     "el clic marca esa entrada en el mismo clic",
                     f"clic {rastro['clic']} ms, marca {rastro['anade']} ms")
            chequear(se_movio and len(activos_clic) == 1 and
                     activos_clic[0]["texto"] == objetivo["texto"],
                     "al terminar el salto sigue marcada esa entrada",
                     str([e["texto"] for e in activos_clic]))
            # y la geometría manda: un tope de página manual la deja como debe
            pag.evaluate(DETENER)
            pag.evaluate("window.scrollTo({top: 1e7, behavior: 'auto'})")
            pag.wait_for_timeout(250)
            m = pag.evaluate(MEDIR)
            af = activos(m)
            print(f"       en el tope de página, marcadas: "
                  f"{[e['texto'] for e in af]} (la última es "
                  f"{m['entradas'][-1]['texto']!r})")
            chequear(len(af) == 1 and af[0]["texto"] == m["entradas"][-1]["texto"],
                     "después del clic sigue mandando la geometría",
                     str([e["texto"] for e in af]))
            pag.evaluate("window.scrollTo({top: 0, behavior: 'auto'})")
            pag.wait_for_timeout(250)
            af = activos(pag.evaluate(MEDIR))
            chequear(len(af) == 0,
                     "y arriba del todo vuelve a no marcar ninguna",
                     str([e["texto"] for e in af]))

            # (g) contraste ------------------------------------------------
            print("  (g) contraste del riel (mínimo 4.5:1 para texto normal)")
            problemas_contraste = []
            for tema in ["claro", "oscuro"]:
                pag.evaluate(
                    "(t) => { document.documentElement.setAttribute('data-tema', t); }", tema
                )
                pag.wait_for_timeout(150)
                pag.evaluate(IR_A, medio[1]["id"])
                pag.wait_for_timeout(250)
                medir_contraste(pag.evaluate(MEDIR), "data-tema=" + tema,
                                problemas_contraste)
            pag.evaluate(
                "() => { document.documentElement.removeAttribute('data-tema'); }"
            )
            chequear(not problemas_contraste, "contraste >= 4.5:1 en claro y oscuro",
                     str(problemas_contraste))

            # (f) consola ---------------------------------------------------
            print("  (f) consola")
            print(f"       errores: {errores}")
            print(f"       avisos : {avisos}")
            chequear(not errores, "sin errores de consola", str(errores))
            errores.clear()
            avisos.clear()
            ctx.close()

        # ------------------------------------------------------------------
        # Movimiento reducido
        # ------------------------------------------------------------------
        print("=" * 78)
        print("MOVIMIENTO REDUCIDO (prefers-reduced-motion: reduce)")
        print("=" * 78)
        ctx = nav.new_context(viewport={"width": 1440, "height": 900},
                              reduced_motion="reduce")
        pag = ctx.new_page()
        vigilar(pag)
        pag.goto(BASE + "/sobre-mi/", wait_until="load")
        pag.wait_for_timeout(500)
        encabezado = pag.evaluate(
            "() => { const a = document.querySelector('.ap-toc__menu a');"
            " return {transicion: getComputedStyle(a).transitionDuration,"
            " smooth: getComputedStyle(document.documentElement).scrollBehavior,"
            " entradas: document.querySelectorAll('.ap-toc__menu a').length}; }"
        )
        print(f"       entradas: {encabezado['entradas']}   "
              f"transition-duration del riel: {encabezado['transicion']}")
        print(f"       scroll-behavior del html: {encabezado['smooth']}")
        chequear(encabezado["smooth"] == "auto",
                 "sin scroll suave con movimiento reducido", encabezado["smooth"])
        # el id de /sobre-mi/, no el de la página anterior
        pag.evaluate(IR_A, unquote("#docencia".lstrip("#")))
        asentar(pag)
        mm = pag.evaluate(MEDIR)
        am = activos(mm)
        print(f"       activas: {len(am)} {[e['texto'] for e in am]}")
        chequear(len(am) == 1 and am[0]["texto"] == "Docencia",
                 "el marcado sigue funcionando con movimiento reducido",
                 str([e["texto"] for e in am]))
        if am:
            chequear(am[0]["transicion"] in ("0.001ms", "1e-06s", "0s"),
                     "la transición del enlace activo está anulada",
                     am[0]["transicion"])
        ctx.close()
        errores.clear()
        avisos.clear()

        # ------------------------------------------------------------------
        # Sin JavaScript
        # ------------------------------------------------------------------
        print("=" * 78)
        print("SIN JAVASCRIPT")
        print("=" * 78)
        for ruta in CON_RIEL:
            ctx = nav.new_context(viewport={"width": 1440, "height": 900},
                                  java_script_enabled=False)
            pag = ctx.new_page()
            pag.goto(BASE + ruta, wait_until="load")
            pag.wait_for_timeout(300)
            datos = pag.evaluate(
                """() => {
                  const menu = document.querySelector('.ap-toc__menu');
                  const enlaces = menu
                    ? [...menu.querySelectorAll('a[href^="#"]')]
                    : [];
                  const oculto = [...document.querySelectorAll('[data-reveal]')]
                    .filter((e) => getComputedStyle(e).opacity === '0').length;
                  return {
                    entradas: enlaces.length,
                    texto: enlaces.map((a) => a.textContent.trim()),
                    todas_visibles: enlaces.every(
                      (a) => a.getClientRects().length > 0
                        && a.getBoundingClientRect().height > 0),
                    ap_js: document.documentElement.classList.contains('ap-js'),
                    revelados_ocultos: oculto,
                    titulos_visibles: [...document.querySelectorAll(
                      '.ap-seccion-contenido h2, .ap-seccion-contenido h3')]
                      .every((h) => getComputedStyle(h).opacity !== '0'
                        && h.getClientRects().length > 0),
                  };
                }"""
            )
            print(f"  {ruta}: {datos['entradas']} entradas, "
                  f"todas visibles={datos['todas_visibles']}, "
                  f"ap-js={datos['ap_js']}, "
                  f"[data-reveal] ocultos={datos['revelados_ocultos']}, "
                  f"títulos visibles={datos['titulos_visibles']}")
            chequear(datos["entradas"] > 0 and datos["todas_visibles"]
                     and not datos["ap_js"] and datos["revelados_ocultos"] == 0
                     and datos["titulos_visibles"],
                     f"sin JavaScript el riel se lee entero ({ruta})",
                     str(datos))
            ctx.close()

        # ------------------------------------------------------------------
        # Desborde horizontal en el resto de las páginas
        # ------------------------------------------------------------------
        print("=" * 78)
        print("DESBORDE HORIZONTAL (todas las páginas, claro y oscuro)")
        print("=" * 78)
        for ancho in (1440, 390):
            for tema in ["claro", "oscuro"]:
                ctx = nav.new_context(viewport={"width": ancho, "height": 900})
                pag = ctx.new_page()
                vigilar(pag)
                for ruta in TODAS:
                    pag.goto(BASE + ruta, wait_until="load")
                    pag.evaluate(
                        "(t) => { document.documentElement.setAttribute('data-tema', t); }",
                        tema,
                    )
                    pag.wait_for_timeout(120)
                    d = pag.evaluate(
                        """() => ({
                            scroll: document.documentElement.scrollWidth,
                            inner: window.innerWidth,
                            body: document.body.scrollWidth,
                        })"""
                    )
                    ok = d["scroll"] <= d["inner"] + 1 and d["body"] <= d["inner"] + 1
                    print(f"  {ancho:5d} {tema:7s} {ruta:16s} "
                          f"scrollWidth={d['scroll']:5d} inner={d['inner']:5d} "
                          f"{'OK' if ok else 'FALLA'}")
                    if not ok:
                        fallos.append(
                            f"desborde horizontal {ancho} {tema} {ruta}: "
                            f"{d['scroll']} > {d['inner']}"
                        )
                ctx.close()
        nav.close()

    print("=" * 78)
    if notas:
        for n in notas:
            print("nota: " + n)
    if fallos:
        print(f"FALLOS: {len(fallos)}")
        for f in fallos:
            print("  - " + f)
        return 1
    print("TODO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
