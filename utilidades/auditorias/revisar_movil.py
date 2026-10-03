"""Auditoría del teléfono: el sitio en la mano, no en una ventana angosta.

Por qué esta auditoría existe aparte de la visual: la visual mide 390 px con
un ratón, y con un ratón la mitad de los problemas del teléfono no aparecen.
Un perfil de teléfono de verdad en Playwright trae pantalla táctil, factor de
escala y las métricas de un móvil, y además cambia lo que el navegador hace con
el meta viewport, con el hover y con el toque.

Qué se mide, y por qué cada cosa:

  A. el meta viewport y que no se bloquee el zoom        (WCAG 1.4.4)
  B. que a 320 px de ancho nada se salga de lado          (WCAG 1.4.10)
  C. el teléfono en horizontal, que es donde el encabezado fijo se come la
     pantalla
  D. el área de cada cosa que se toca con el dedo         (WCAG 2.5.8, 2.5.5)
  E. que las cosas funcionen TOCANDO, no con .click():
     el menú, el tema, volver arriba, el filtro, el buscador y la barra
  F. que al tocar no se quede pegado el estado hover, que es el clásico fallo
     de teléfono: en el escritorio no se nota porque el ratón siempre está
     encima de algo

Y al final, lo que un emulador no puede saber, dicho explícitamente para que
nadie lo tome por comprobado: el texto inflado de iOS, los huecos seguros de
la pantalla con muesca, el teclado en pantalla tapando el campo de búsqueda y
el comportamiento real de Safari, que no es Chromium.

Uso:  python utilidades/auditorias/revisar_movil.py
"""

import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

BASE = contexto.BASE
MOVIL = contexto.CFG["movil"]
MINIMO = MOVIL["minimo_area_tactil"]
RECOMENDADO = MOVIL["area_tactil_recomendada"]
MIN_FUENTE = MOVIL["minimo_fuente_campos"]

#: Porcentaje de la pantalla que puede ocupar el encabezado fijo en horizontal
#: antes de darlo por malo. Es un criterio, no una norma: WCAG no pone un
#: número aquí, así que por encima de este valor se avisa y por debajo también,
#: con la medida a la vista, para que quien decida lo haga con el dato delante.
MAX_ENCABEZADO = 0.40

fallos = []
notas = []


def chequear(ok, texto, detalle=""):
    """Imprime el resultado de una comprobación.

    `detalle` es siempre una MEDIDA, nunca una conclusión: si se le pasa la
    conclusión, la línea dice "ok" y después "el desplegable sigue cerrado", que
    es peor que no decir nada.
    """
    print(("  ok    " if ok else "  FALLA") + "  " + texto
          + ("   " + detalle if detalle else ""))
    if not ok:
        fallos.append(texto + (" | " + detalle if detalle else ""))
    return ok


def nota(texto):
    notas.append(texto)
    print("  nota  " + texto)


def seccion(titulo):
    print()
    print("-- " + titulo + " " + "-" * max(4, 58 - len(titulo)))


def esperar_scroll(pag, margen=1, minimo_ms=400, tope=60):
    """Espera a que el scroll se detenga, en lugar de mirar a los X ms.

    El sitio tiene scroll-behavior: smooth, así que un toque en "volver arriba"
    tarda lo que tarde la animación. Medir en un instante fijo daba un fallo
    falso la mitad de las veces.

    El mínimo importa: al pedir el scroll y medir enseguida sale 0, y si se dan
    por bueno dos lecturas iguales se cree que ya terminó cuando ni ha
    empezado. Por eso primero se espera un momento y luego se exige que las
    últimas dos lecturas coincidan.
    """
    pag.wait_for_timeout(minimo_ms)
    anterior = None
    estable = 0
    for _ in range(tope):
        actual = pag.evaluate("() => Math.round(window.scrollY)")
        if anterior is not None and abs(actual - anterior) <= margen:
            estable += 1
            if estable >= 2:
                return actual
        else:
            estable = 0
        anterior = actual
        pag.wait_for_timeout(70)
    return anterior if anterior is not None else 0


# --------------------------------------------------------------------------
# Lo que se mide dentro de la página
# --------------------------------------------------------------------------
MEDIR_DESBORDE = """(limite) => {
  // Se ignoran los que están dentro de una caja con desplazamiento propio: un
  // bloque de código largo dentro de un <pre> con overflow auto se sale a
  // propósito y no empuja la página. En un teléfono esto es todavía más
  // importante, porque un bloque ancho es justo lo que se desplaza con el dedo.
  const rueda = (el) => {
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      const ox = getComputedStyle(n).overflowX;
      if (ox === 'auto' || ox === 'scroll') return true;
    }
    return false;
  };
  const malos = [];
  document.querySelectorAll('body *').forEach((el) => {
    const c = el.getBoundingClientRect();
    if (c.width === 0 && c.height === 0) return;
    if (c.right <= limite + 1 && c.left >= -1) return;
    if (rueda(el)) return;
    if (getComputedStyle(el).position === 'fixed') return;
    malos.push({
      etiqueta: el.tagName.toLowerCase() +
        (typeof el.className === 'string' && el.className.trim()
          ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : ''),
      izquierda: Math.round(c.left), derecha: Math.round(c.right),
    });
  });
  return {
    documento: Math.round(document.documentElement.scrollWidth),
    ventana: Math.round(document.documentElement.clientWidth),
    malos: malos.slice(0, 6),
  };
}"""

MEDIR_AREA = """(minimo) => {
  // Cada cosa que se puede tocar. Se descartan los que no se ven de verdad,
  // que es lo que hace la clase .visually-hidden del tema (1 px con clip), y los
  // que no reciben el toque (pointer-events: none), como el botón de volver
  // arriba cuando está escondido: si no puede pulsarse no es un objetivo, y
  // contarlo hacía creer que tapaba los enlaces del pie de las páginas cortas.
  const selector = 'a[href], button, input, select, textarea, summary,'
    + ' [role="button"], [role="tab"], [role="switch"]';
  const cajas = [];
  const chicos = [];   // chicos pero con espacio libre alrededor: cumplen
  const malos = [];    // chicos y con otro objetivo encima: no cumplen
  const nombre = (el) => el.tagName.toLowerCase() +
    (typeof el.className === 'string' && el.className.trim()
      ? '.' + el.className.trim().split(/\\s+/).slice(0, 2).join('.') : '');

  document.querySelectorAll(selector).forEach((el) => {
    const c = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    if (cs.pointerEvents === 'none') return;
    if (c.width === 0 || c.height === 0) return;
    if (c.width <= 2 || c.height <= 2) return;
    const r = {x: c.left, y: c.top, w: c.width, h: c.height, el: el};
    cajas.push(r);
    if (r.w >= minimo && r.h >= minimo) return;

    // Excepción "en línea": un enlace en medio de un texto no tiene que medir
    // 24 px, porque el texto de alrededor ya es el área. Se reconoce
    // comparando el texto del bloque con el del enlace: si el bloque tiene
    // bastante más, el enlace está en una frase.
    const bloque = el.closest('p, li, dd, dt, td, blockquote, figcaption, h1, h2,'
      + ' h3, h4, h5, h6, label');
    const enFrase = cs.display.startsWith('inline') && bloque &&
      (bloque.textContent || '').trim().length >
        (el.textContent || '').trim().length + 3;
    if (enFrase) return;

    // Excepción de espaciado (WCAG 2.5.8): si el círculo de 24 px centrado en
    // el objetivo no toca a ningún otro objetivo, el área alrededor está
    // libre y cumple igual. Es la excepción que salva a los enlaces de un pie
    // de página, que son bajitos pero están separados.
    const cx = r.x + r.w / 2;
    const cy = r.y + r.h / 2;
    const radio = minimo / 2;
    let choca = false;
    for (const o of cajas) {
      if (o === r) continue;
      const dx = Math.max(o.x - cx, 0, cx - (o.x + o.w));
      const dy = Math.max(o.y - cy, 0, cy - (o.y + o.h));
      if (dx * dx + dy * dy < radio * radio) { choca = true; break; }
    }
    const ficha = {etiqueta: nombre(el), ancho: Math.round(r.w),
                   alto: Math.round(r.h),
                   texto: (el.textContent || '').trim().slice(0, 26)};
    if (choca) {
      malos.push(ficha);
    } else {
      chicos.push(ficha);
    }
  });
  return {malos: malos.slice(0, 8), cuantosMalos: malos.length,
          chicos: chicos.slice(0, 4), cuantosChicos: chicos.length,
          medibles: cajas.length};
}"""

MEDIR_ESTILO = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const c = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  return {ancho: Math.round(c.width), alto: Math.round(c.height),
          top: Math.round(c.top), bottom: Math.round(c.bottom),
          fuente: cs.fontSize, position: cs.position, display: cs.display,
          familia: cs.fontFamily.split(',')[0], padding: cs.padding,
          texto: (el.textContent || '').trim()};
}"""

MEDIR_VIEWPORT = """() => {
  const metas = [...document.querySelectorAll('meta[name="viewport"]')]
    .map((m) => m.getAttribute('content') || '');
  const raiz = getComputedStyle(document.documentElement);
  const cuerpo = getComputedStyle(document.body);
  return {metas: metas,
          overflowRaiz: raiz.overflowY + '/' + raiz.overflowX,
          overflowCuerpo: cuerpo.overflowY + '/' + cuerpo.overflowX};
}"""


def abrir_perfil(p, nombre, respaldo):
    """Las medidas de un contexto de navegador para un teléfono, y si es real.

    Se usa el perfil de la lista de Playwright si existe, porque es lo que
    activa el modo táctil de verdad: con `is_mobile` y `has_touch` el navegador
    se comporta como en un móvil (el meta viewport manda, el hover no se queda
    pegado, el toque no es un clic). Si el nombre no estuviera en la lista
    --que cambia entre versiones-- se arma a mano con las mismas medidas y se
    avisa, porque una emulación a medias parece mejor de lo que es.
    """
    datos = dict(p.devices.get(nombre, {})) or dict(respaldo)
    datos.pop("default_browser_type", None)
    return datos, bool(p.devices.get(nombre))


# Respaldo para cuando el perfil de la configuración no exista: un teléfono
# android razonable, con pantalla táctil y escala 3, que es lo que cambia el
# comportamiento respecto de una ventana con ratón.
MOVIL_RESPALDO = {
    "viewport": {"width": 384, "height": 832},
    "device_scale_factor": 3,
    "is_mobile": True,
    "has_touch": True,
}

# El mismo teléfono en horizontal. La escala 3 se deja: es lo que hace un
# teléfono real y no cambia el ancho en px CSS.
PAIS_RESPALDO = {
    "viewport": {"width": 832, "height": 384},
    "device_scale_factor": 3,
    "is_mobile": True,
    "has_touch": True,
}


def main():
    estrecho = MOVIL["ancho_mas_estrecho"]
    resumen_chicos = {}

    with sync_playwright() as p:
        vertical, habia = abrir_perfil(p, MOVIL["perfil"], MOVIL_RESPALDO)
        if not habia:
            nota("el perfil '" + MOVIL["perfil"] + "' no está en la lista de "
                 "Playwright; se armó a mano con las mismas medidas")
        tam = vertical.get("viewport", {})
        print("perfil del teléfono: " + MOVIL["perfil"]
              + f"  {tam.get('width', '?')}x{tam.get('height', '?')} px, "
              + f"táctil={vertical.get('has_touch')}, "
              + f"móvil={vertical.get('is_mobile')}, "
              + f"escala={vertical.get('device_scale_factor')}")
        navegador = p.chromium.launch()

        # ------------------------------------------------------------------
        seccion("A. el meta viewport y el zoom (WCAG 1.4.4)")
        # Se miran todas las páginas pero se informa una vez: el meta lo pone
        # el tema en todas y lo interesante es si alguna se sale del patrón.
        ctx = navegador.new_context(**vertical)
        pag = ctx.new_page()
        sin_meta, sin_ancho, bloqueado = [], [], []
        for nombre, ruta in contexto.PAGINAS:
            pag.goto(BASE + ruta, wait_until="load")
            d = pag.evaluate(MEDIR_VIEWPORT)
            meta = d["metas"][0] if d["metas"] else ""
            if not meta:
                sin_meta.append(nombre)
                continue
            if "width=device-width" not in meta.replace(" ", ""):
                sin_ancho.append(f"{nombre}: {meta}")
            for trozo in meta.split(","):
                t = trozo.strip().lower().replace(" ", "")
                if t.startswith("user-scalable=") and t.split("=")[1] in ("no", "0"):
                    bloqueado.append(f"{nombre}: {trozo.strip()}")
                if t.startswith(("maximum-scale", "minimum-scale")):
                    try:
                        if float(t.split("=")[1]) < 2:
                            bloqueado.append(f"{nombre}: {trozo.strip()}")
                    except (IndexError, ValueError):
                        pass
        chequear(not sin_meta, f"las {len(contexto.PAGINAS)} páginas tienen "
                 "meta viewport", ", ".join(sin_meta))
        chequear(not sin_ancho, "todas dicen width=device-width",
                 "; ".join(sin_ancho))
        chequear(not bloqueado, "ninguna bloquea el zoom con los dedos",
                 "; ".join(bloqueado))
        ctx.close()

        # ------------------------------------------------------------------
        seccion(f"B. a {estrecho['ancho']} px de ancho no se sale nada "
                f"(WCAG 1.4.10)")
        angosto = dict(vertical)
        angosto["viewport"] = {"width": estrecho["ancho"],
                               "height": estrecho["alto"]}
        ctx = navegador.new_context(**angosto)
        pag = ctx.new_page()
        for nombre, ruta in contexto.PAGINAS:
            pag.goto(BASE + ruta, wait_until="load")
            pag.wait_for_timeout(250)
            d = pag.evaluate(MEDIR_DESBORDE, angosto["viewport"]["width"])
            detalle = f"documento {d['documento']} / ventana {d['ventana']}"
            if d["documento"] > d["ventana"] + 1:
                detalle += "  " + ", ".join(
                    f"{m['etiqueta']} ({m['izquierda']}..{m['derecha']})"
                    for m in d["malos"])
            chequear(d["documento"] <= d["ventana"] + 1,
                     f"{nombre}: nada se sale de lado", detalle)
        # La columna de lectura es lo que más se estrecha. El texto de lectura
        # está en px a propósito (no en rem) para que no encogamos al angostar
        # la pantalla; si alguna vez bajara de 15 px, en el teléfono se leería
        # con lupa.
        pag.goto(BASE + contexto.RUTAS["articulo"], wait_until="load")
        d = pag.evaluate(MEDIR_ESTILO, ".ap-seccion-contenido")
        if d:
            chequear(float(d["fuente"].replace("px", "")) >= 15,
                     f"el texto de lectura no baja de 15 px a {estrecho['ancho']}",
                     f"{d['fuente']} en una columna de {d['ancho']} px")
        ctx.close()

        # ------------------------------------------------------------------
        seccion("C. el teléfono en horizontal")
        apaisado, habia2 = abrir_perfil(
            p, (MOVIL.get("perfiles_horizontales") or [None])[0], PAIS_RESPALDO)
        if not habia2:
            nota("el perfil en horizontal de la configuración no está en la "
                 "lista de Playwright; se armó a mano")
        ctx = navegador.new_context(**apaisado)
        pag = ctx.new_page()
        alto_ventana = apaisado["viewport"]["height"]
        for nombre, ruta in contexto.PAGINAS:
            pag.goto(BASE + ruta, wait_until="load")
            pag.wait_for_timeout(250)
            d = pag.evaluate(MEDIR_DESBORDE, apaisado["viewport"]["width"])
            chequear(d["documento"] <= d["ventana"] + 1,
                     f"{nombre}: en horizontal no se sale de lado",
                     f"documento {d['documento']} / ventana {d['ventana']}")
        # El encabezado es sticky, así que en horizontal se come parte de la
        # pantalla mientras se lee. No hay norma que ponga un número, así que
        # se mide y se informa siempre; solo se marca como falla si se pasa del
        # 40%, que es donde el texto queda de verdad apretado.
        cab = pag.evaluate(MEDIR_ESTILO, ".masthead")
        if cab:
            proporcion = cab["alto"] / alto_ventana
            detalle = (f"{cab['alto']} px de {alto_ventana} "
                       f"({proporcion * 100:.0f}%), {cab['position']}")
            if proporcion < MAX_ENCABEZADO:
                chequear(True, "el encabezado no se come la pantalla en "
                         "horizontal", detalle)
            else:
                chequear(False, "el encabezado se come la pantalla en "
                         "horizontal", detalle)
            if proporcion > 0.25:
                nota("en horizontal el encabezado fijo ocupa el "
                     f"{proporcion * 100:.0f}% de la pantalla ({cab['alto']} "
                     f"de {alto_ventana} px). No incumple nada, pero en un "
                     "teléfono de verdad se nota")
        else:
            nota("no se encontró .masthead para medirlo en horizontal")
        ctx.close()

        # ------------------------------------------------------------------
        seccion(f"D. área táctil: nada por debajo de {MINIMO}x{MINIMO} px "
                f"(WCAG 2.5.8)")
        # Se cuentan como falla solo los que están por debajo del mínimo Y
        # tienen otro objetivo encima. Los que están por debajo pero con
        # espacio libre alrededor cumplen por la excepción de espaciado, y se
        # informan aparte y una sola vez, porque si no se repite once por
        # página y no dice nada nuevo.
        ctx = navegador.new_context(**vertical)
        pag = ctx.new_page()
        for nombre, ruta in contexto.PAGINAS:
            pag.goto(BASE + ruta, wait_until="load")
            pag.wait_for_timeout(250)
            d = pag.evaluate(MEDIR_AREA, MINIMO)
            detalle = f"{d['medibles']} elementos, {d['cuantosMalos']} sin espacio"
            if d["cuantosMalos"]:
                detalle += "; " + ", ".join(
                    f"{m['etiqueta']} {m['ancho']}x{m['alto']} \"{m['texto']}\""
                    for m in d["malos"])
            chequear(d["cuantosMalos"] == 0,
                     f"{nombre}: todo lo que se toca tiene sitio",
                     detalle)
            if d["cuantosChicos"]:
                resumen_chicos[nombre] = d["chicos"]
        ctx.close()

        # ------------------------------------------------------------------
        seccion("E. con el dedo, no con el ratón")
        ctx = navegador.new_context(**vertical)
        pag = ctx.new_page()

        # E1. el menú desplegable, que es lo único que el tema esconde en
        # pantallas chicas y por lo tanto lo primero que hay que probar.
        pag.goto(BASE + contexto.RUTAS["red-team"], wait_until="load")
        pag.wait_for_timeout(400)
        boton = pag.locator("button.greedy-nav__toggle")
        visible = bool(boton.count()) and boton.first.is_visible()
        chequear(visible, "el botón del menú aparece en el teléfono",
                 "no aparece" if not visible else "visible")
        if visible:
            aria_antes = boton.first.get_attribute("aria-expanded")
            boton.first.tap()
            pag.wait_for_timeout(350)
            lista = pag.locator("#site-nav ul.hidden-links")
            abierta = bool(lista.count()) and lista.first.is_visible()
            chequear(abierta, "el menú abre al tocarlo",
                     f"enlaces visibles: {lista.first.locator('a').count() if lista.count() else 0}")
            if not abierta:
                print("        (el desplegable sigue cerrado)")
            aria_despues = boton.first.get_attribute("aria-expanded")
            if aria_antes is None and aria_despues is None:
                nota("el botón del menú no pone aria-expanded: un lector de "
                     "pantalla no puede decir si el menú está abierto (WCAG "
                     "4.1.2). Lo pone el tema, no el diseño del sitio")
            else:
                chequear(aria_antes != aria_despues,
                         "el botón del menú avisa si está abierto",
                         f"aria-expanded: {aria_antes} -> {aria_despues}")
            if abierta:
                entrada = pag.evaluate(MEDIR_ESTILO, "#site-nav ul.hidden-links a")
                if entrada:
                    chequear(entrada["ancho"] >= MINIMO
                             and entrada["alto"] >= MINIMO,
                             "las entradas del menú se pueden tocar",
                             f"{entrada['ancho']}x{entrada['alto']}")
            boton.first.tap()
            pag.wait_for_timeout(300)
            cerrada = (not lista.count()) or not lista.first.is_visible()
            chequear(cerrada, "el menú se cierra al volver a tocarlo",
                     "cerrado" if cerrada else "sigue abierto")

        # E2. el interruptor de tema
        pag.goto(BASE + "/", wait_until="load")
        pag.wait_for_timeout(300)
        if pag.locator(".theme-toggle").count():
            antes = pag.evaluate(
                "() => document.documentElement.getAttribute('data-tema')")
            pag.locator(".theme-toggle").first.tap()
            pag.wait_for_timeout(400)
            despues = pag.evaluate(
                "() => document.documentElement.getAttribute('data-tema')")
            chequear(antes != despues, "el tema cambia al tocarlo",
                     f"data-tema: {antes} -> {despues}")
        else:
            nota("no hay .theme-toggle en la portada")

        # E3. la barra de progreso y volver arriba. Se baja hasta el final, no a
        # una posición fija: el botón aparece cuando se ha pasado el 80% del
        # alto de la pantalla, así que en una página más corta que eso no puede
        # llegar a aparecer nunca, y eso hay que decirlo en vez de contarlo como
        # falla del botón.
        pag.goto(BASE + contexto.RUTAS["sobre-mi"], wait_until="load")
        pag.wait_for_timeout(300)
        alto = pag.evaluate(
            "() => [document.documentElement.scrollHeight, window.innerHeight]")
        umbral = int(alto[1] * 0.8)
        pag.evaluate("() => window.scrollTo(0, 99999)")
        y_final = esperar_scroll(pag)
        ancho = pag.evaluate(
            """() => { const e = document.querySelector('[data-progress]');
               if (!e) return null;
               const c = e.getBoundingClientRect();
               return [Math.round(c.width), Math.round(c.height)]; }""")
        if ancho:
            chequear(ancho[0] > 0, "la barra de progreso avanza al bajar",
                     f"{ancho[0]}x{ancho[1]} px a {y_final} px de scroll")
        else:
            nota("no hay barra de progreso en esta página")
        if pag.locator("[data-back-top]").count():
            if y_final >= umbral:
                visible = pag.evaluate(
                    "() => document.querySelector('[data-back-top]')"
                    ".classList.contains('es-visible')")
                chequear(visible, "el botón de volver arriba aparece al bajar",
                         f"es-visible a {y_final} px (umbral {umbral})"
                         if visible else
                         f"sigue escondido a {y_final} px (umbral {umbral})")
            else:
                nota("en esta página el botón de volver arriba no puede "
                     f"aparecer: sólo se puede bajar {y_final} px y el sitio lo "
                     f"enseña a partir de {umbral}. En el teléfono se baja del "
                     "todo y el botón no aparece nunca")
            caja = pag.evaluate(MEDIR_ESTILO, "[data-back-top]")
            if caja:
                chequear(caja["ancho"] >= MINIMO and caja["alto"] >= MINIMO,
                         "el botón de volver arriba se puede tocar",
                         f"{caja['ancho']}x{caja['alto']}")
                if caja["ancho"] < RECOMENDADO or caja["alto"] < RECOMENDADO:
                    nota(f"el botón de volver arriba es de {caja['ancho']}x"
                         f"{caja['alto']} y la guía de Android pide "
                         f"{RECOMENDADO}x{RECOMENDADO}")
            pag.locator("[data-back-top]").first.tap()
            y = esperar_scroll(pag)
            chequear(y < 80, "volver arriba funciona con el dedo",
                     f"quedó en {y} px")
        else:
            nota("no hay [data-back-top] en esta página")

        # E4. el filtro por etiquetas. No todas las páginas lo tienen (solo las
        # de sección con `filtro: true` en el front matter), así que se busca
        # una que lo tenga en vez de suponer cuál es.
        con_filtro = None
        for nombre, ruta in contexto.PAGINAS:
            pag.goto(BASE + ruta, wait_until="load")
            pag.wait_for_timeout(300)
            if pag.locator("[data-fichas-barra]").count():
                con_filtro = (nombre, ruta)
                break
        if con_filtro:
            chip = pag.locator(".ap-ficha-etiqueta").first
            chip.tap()
            pag.wait_for_timeout(350)
            ocultas = pag.evaluate(
                "() => [...document.querySelectorAll('.card')]"
                ".filter(c => c.hidden).length")
            visibles = pag.evaluate(
                "() => [...document.querySelectorAll('.card')]"
                ".filter(c => !c.hidden).length")
            chequear(ocultas > 0 and visibles > 0,
                     f"el filtro por etiquetas funciona al tocar ({con_filtro[0]})",
                     f"{visibles} visibles, {ocultas} ocultas")
            if pag.locator(".ap-fichas-barra__limpiar").count():
                pag.locator(".ap-fichas-barra__limpiar").first.tap()
                pag.wait_for_timeout(300)
                todas = pag.evaluate(
                    "() => [...document.querySelectorAll('.card')]"
                    ".filter(c => !c.hidden).length")
                chequear(todas == visibles + ocultas,
                         "limpiar el filtro funciona al tocar",
                         f"{todas} visibles de nuevo")
            else:
                nota("la barra de filtros no tiene botón de limpiar")
        else:
            nota("ninguna página tiene barra de filtros")

        # E5. el buscador, y la letra del campo: iOS agranda la página si el
        # campo tiene menos de 16 px, y después no vuelve a su tamaño.
        pagina_indice = contexto.RUTAS["indice"]
        pag.goto(BASE + pagina_indice, wait_until="load")
        pag.wait_for_timeout(400)
        if pag.locator("[data-buscador] input").count():
            info = pag.evaluate(MEDIR_ESTILO, "[data-buscador] input")
            if info:
                chequear(float(info["fuente"].replace("px", "")) >= MIN_FUENTE,
                         f"el campo de búsqueda no tiene menos de "
                         f"{MIN_FUENTE} px de letra", info["fuente"])
            extras = pag.evaluate(
                """() => { const e = document.querySelector('[data-buscador] input');
                   return {tipo: e.type,
                           enterkey: e.getAttribute('enterkeyhint'),
                           nombre: e.getAttribute('aria-label')
                             || (document.querySelector('label[for="' + e.id + '"]')
                                 || {}).textContent}; }""")
            chequear(bool(extras["nombre"]), "el buscador tiene nombre accesible",
                     str(extras["nombre"]))
            if not extras["enterkey"]:
                nota("el buscador no declara enterkeyhint, así que en el "
                     "teclado del teléfono la tecla no diría 'buscar'")
            campo = pag.locator("[data-buscador] input").first
            campo.tap()
            campo.type("python", delay=60)
            pag.wait_for_timeout(400)
            encontrados = pag.evaluate(
                "() => [...document.querySelectorAll('.ap-indice-lista > *')]"
                ".filter(e => !e.hidden).length")
            chequear(encontrados > 0,
                     "el buscador responde con el teclado del teléfono",
                     f"{encontrados} resultados para 'python'")
            campo.fill("")
        else:
            nota("el índice no tiene buscador")
        ctx.close()

        # ------------------------------------------------------------------
        seccion("F. lo que se queda pegado después de tocar")
        # En un teléfono, al tocar un elemento se le queda el estado hover
        # encima hasta que se toca otra cosa. Si ese hover cambia el aspecto,
        # el elemento queda discolorido y así se queda. La pregunta directa al
        # navegador es si el elemento sigue en :hover, y con eso se responde
        # sin depender del color: tocar el botón de tema cambia de tema, así que
        # comparar colores daría dos colores distintos por buenas razones y no
        # diría nada de si el estado se quedó pegado.
        ctx = navegador.new_context(**vertical)
        pag = ctx.new_page()
        pag.goto(BASE + "/", wait_until="load")
        pag.wait_for_timeout(400)
        EN_HOVER = "() => { const a = document.querySelector('.theme-toggle');"
        EN_HOVER += " return a ? a.matches(':hover') : null; }"
        if not pag.locator(".theme-toggle").count():
            nota("no hay botón de tema para probar el hover pegado")
        else:
            pag.locator("h1, .hero__titulo").first.tap()
            pag.wait_for_timeout(400)
            antes = pag.evaluate(EN_HOVER)
            pag.locator(".theme-toggle").first.tap()
            pag.wait_for_timeout(400)
            durante = pag.evaluate(EN_HOVER)
            pag.locator("h1, .hero__titulo").first.tap()
            pag.wait_for_timeout(400)
            despues = pag.evaluate(EN_HOVER)
            if durante is not True:
                # Si el emulador no pone :hover al tocar, esta prueba no está
                # midiendo lo que dice medir y no se puede concluir nada.
                nota("el navegador de emulación no pone :hover al tocar, así "
                     "que aquí no se puede comprobar si el estado se queda "
                     "pegado: eso hay que verlo en un teléfono de verdad")
                print("  (prueba sin valor en este emulador)")
            else:
                chequear(antes is False and despues is False,
                         "el estado hover del botón se suelta al tocar otra "
                         "cosa",
                         f":hover antes={antes}, con el dedo={durante}, "
                         f"después={despues}")
                if despues is not False:
                    nota("el botón de tema se queda con el estilo de hover "
                         "después de tocar otra cosa: en un teléfono eso se ve "
                         "como un botón que se quedó pulsado")
        ctx.close()

        navegador.close()

    # ----------------------------------------------------------------------
    seccion("D-bis. los chicos que cumplen por excepción de espaciado")
    if resumen_chicos:
        total = sum(len(v) for v in resumen_chicos.values())
        primero = next(iter(resumen_chicos.values()))
        detalle = "; ".join(
            f"{c['etiqueta']} {c['ancho']}x{c['alto']} \"{c['texto']}\""
            for c in primero)
        nota(f"hay {total} elementos por debajo de {MINIMO} px en el sitio, "
             "pero con espacio libre alrededor, así que cumplen por la "
             f"excepción de espaciado. Los más bajos, en la página "
             f"'{next(iter(resumen_chicos))}': {detalle}")
        if any(c["etiqueta"].endswith("header-link") or c["etiqueta"] == "a.header-link"
               for v in resumen_chicos.values() for c in v):
            nota("el enlace de permalink de los títulos (a.header-link) es de "
                 "22 px de alto y no tiene relleno: dos píxeles por debajo del "
                 "mínimo, y salva porque alrededor está libre")
    else:
        print("  (no hay elementos por debajo del mínimo)")

    # ----------------------------------------------------------------------
    seccion("G. lo que un emulador no puede comprobar")
    # No son fallas ni aciertos: son cosas que hay que mirar en un teléfono de
    # verdad, y conviene tenerlas escritas para no creer que el sitio está
    # comprobado en la mano cuando no lo está.
    css = contexto.CSS.read_text("utf-8")
    if "text-size-adjust" in css and "-webkit-text-size-adjust" in css:
        nota("el CSS solo trae -webkit-text-size-adjust. Safari ya entiende "
             "la propiedad sin prefijo; conviene tener las dos")
    else:
        nota("el CSS no declara text-size-adjust: en iPhone, al girar el "
             "teléfono el texto se infla solo y puede romper la maqueta")
    if "safe-area-inset" in css:
        print("  ok    el CSS ya usa env(safe-area-inset-) para la muesca")
    else:
        nota("el CSS no usa env(safe-area-inset-): en un iPhone con muesca, "
             "el botón de volver arriba y el pie pueden quedar bajo la barra "
             "de inicio. Es lo primero que se mira en un teléfono de verdad")
    if re.search(r"touch-action\s*:\s*none", css):
        fallos.append("el CSS pone touch-action: none en algún sitio, que "
                      "impide hacer zoom con los dedos")
        print("  FALLA  touch-action: none impide el zoom con los dedos")
    else:
        print("  ok    no hay touch-action: none, el zoom con los dedos anda")
    if re.search(r"(html|body)\s*\{[^}]*overflow-y\s*:\s*hidden", css):
        nota("el CSS oculta el desbordamiento vertical en html o body: en iOS "
             "eso puede dejar la página sin poder desplazarse con el dedo")
    else:
        print("  ok    el desbordamiento vertical no está bloqueado")

    print()
    if notas:
        print("== notas ==")
        for n in notas:
            print("  - " + n)
    if fallos:
        print(f"\nFALLOS: {len(fallos)}")
        for f in fallos:
            print("  - " + f)
        return 1
    print("TODO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
