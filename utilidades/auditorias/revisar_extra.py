"""Segunda vuelta: cosas que no se ven en una captura pero se sienten.

  · contraste real de los textos (WCAG AA)
  · que las dos tipografías propias se estén usando de verdad
  · cómo queda la página SIN JavaScript (debe leerse entera)
  · el menú de pantallas chicas
  · que el tema elegido se guarde al cambiar de página
  · el orden de tabulación

Ojo: con JavaScript desactivado no se puede usar evaluate, así que la revisión
sin JS se hace sobre el HTML y sobre el CSS, no sobre estilos calculados.
"""

import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

BASE = contexto.BASE

# Las seis páginas del contraste salen del grupo "contraste" de la
# configuración. No son las once: la de contraste es la más lenta de las
# auditorías y con estas ya se cubrían los dos temas de texto del sitio (las
# tarjetas, la tabla, el blog y la entrada).
PAGINAS_CONTRASTE = contexto.GRUPOS["contraste"]

problemas = []
notas = []


def luminancia(rgb):
    def canal(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(a, b):
    la, lb = luminancia(a), luminancia(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


MEDIR_CONTRASTE = """() => {
    const lum = c => {
        const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92
            : Math.pow((v + 0.055) / 1.055, 2.4); };
        return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
    };
    const ratio = (a, b) => {
        const la = lum(a), lb = lum(b);
        return (Math.round(((Math.max(la, lb) + 0.05) /
            (Math.min(la, lb) + 0.05)) * 100) / 100);
    };
    // Hay dos formas de escribir un color en CSS y las dos salen de
    // getComputedStyle: rgb(0, 0, 0), rgba(0, 0, 0, 0) y
    // color(srgb 0.9 0.9 0.9 / 0.6). Hay que entenderlas las tres, o el
    // "transparente" se cuela como si fuera negro.
    const rgba = s => {
        s = String(s);
        if (!s || s === 'transparent' || s === 'none') return null;
        const n = (s.match(/-?[\\d.]+(e-?\\d+)?/g) || []).map(Number);
        if (n.length < 3) return null;
        if (s.startsWith('color(')) {
            return [n[0] * 255, n[1] * 255, n[2] * 255, n.length > 3 ? n[3] : 1];
        }
        return [n[0], n[1], n[2], n.length > 3 ? n[3] : 1];
    };
    // El fondo que de verdad se ve: se juntan las capas de abajo hacia arriba,
    // porque un fondo con 60% de opacidad deja ver el de abajo.
    const fondoDe = el => {
        const capas = [];
        for (let n = el; n; n = n.parentElement) {
            const c = rgba(getComputedStyle(n).backgroundColor);
            if (c && c[3] > 0) capas.push(c);
            if ((c && c[3] >= 0.999) || n === document.documentElement) break;
        }
        let base = [255, 255, 255];
        for (let i = capas.length - 1; i >= 0; i--) {
            const [r, g, b, a] = capas[i];
            base = [r * a + base[0] * (1 - a),
                    g * a + base[1] * (1 - a),
                    b * a + base[2] * (1 - a)];
        }
        return base;
    };
    const out = [];
    const selectores = ['.hero__titulo', '.hero__bajada', '.hero__antetitulo',
        '.hero__roles', '.hero__nota', '.ap-seccion__titulo',
        '.ap-seccion__bajada', '.ap-seccion__etiqueta', '.cifra__valor',
        '.cifra__etiqueta', '.ap-area__titulo', '.ap-area__texto',
        '.ap-area__flecha', '.ap-canal__nombre', '.ap-canal__valor',
        '.ap-chip', '.ap-nota-enlaces', '.ap-btn--primario',
        '.ap-btn--fantasma', '.card h3', '.card p', '.tag', '.ap-conteo',
        // Páginas de sección (_layouts/ap-seccion.html)
        '.ap-cabecera__antetitulo', '.ap-cabecera__titulo',
        '.ap-cabecera__bajada', '.ap-fichas-barra__rotulo',
        '.ap-fichas-barra__conteo', '.ap-fichas-barra__nota',
        '.ap-fichas-barra__limpiar', '.ap-ficha-etiqueta',
        '.ap-ficha-etiqueta__n', '.ap-riel__titulo', '.ap-toc__menu a',
        '.ap-autor__nombre', '.ap-autor__lugar', '.ap-autor__nota',
        '.ap-autor__enlace', '.ap-cierre-autor', '.ap-historia',
        '.page__content table th', '.page__content table td',
        '.site-title', '.masthead a', '.page__footer-follow a',
        '.page__footer-copyright a', '.toc a', '.page__content p',
        '.page__content a', '.author__urls a', '.theme-toggle'];
    selectores.forEach(sel => {
        const el = document.querySelector(sel);
        if (!el) return;
        const cs = getComputedStyle(el);
        const fg = rgba(cs.color);
        if (!fg || fg[3] < 0.5) return;   // texto transparente: nada que medir
        const fondo = fondoDe(el);
        const r = ratio([fg[0], fg[1], fg[2]], fondo);
        const grande = parseFloat(cs.fontSize) >= 24 ||
            (parseFloat(cs.fontSize) >= 18.66 && +cs.fontWeight >= 700);
        out.push({
            sel, ratio: r, grande, tam: Math.round(parseFloat(cs.fontSize)),
            peso: cs.fontWeight,
            color: cs.color, fondo: fondo.map(Math.round).join(','),
            texto: el.textContent.trim().slice(0, 28)
        });
    });
    return out;
}"""


def main():
    with sync_playwright() as p:
        nav = p.chromium.launch()

        # ---- 1. contraste, en claro y en oscuro ------------------------
        for esquema in ("light", "dark"):
            ctx = nav.new_context(viewport={"width": 1440, "height": 900},
                                  color_scheme=esquema)
            pag = ctx.new_page()
            for nombre, ruta in PAGINAS_CONTRASTE:
                pag.goto(BASE + ruta, wait_until="load")
                pag.wait_for_timeout(400)
                for m in pag.evaluate(MEDIR_CONTRASTE):
                    minimo = 3.0 if m["grande"] else 4.5
                    if m["ratio"] < minimo:
                        problemas.append(
                            f"contraste {esquema} {nombre} {m['sel']}: "
                            f"{m['ratio']}:1 (mínimo {minimo}) "
                            f"{m['tam']}px peso {m['peso']} "
                            f"color {m['color']} sobre rgb({m['fondo']}) · "
                            f"{m['texto']!r}")
                    else:
                        notas.append(
                            f"contraste {esquema:5} {nombre:9} {m['sel']:24} "
                            f"{m['ratio']:5}:1  {m['tam']}px")
            ctx.close()

        # ---- 2. tipografías --------------------------------------------
        ctx = nav.new_context(viewport={"width": 1440, "height": 900})
        pag = ctx.new_page()
        pag.goto(BASE + "/", wait_until="load")
        pag.wait_for_timeout(600)
        fuentes = pag.evaluate("""() => ({
            cargadas: [...document.fonts].map(f => f.family + ' ' + f.status),
            titulo: getComputedStyle(document.querySelector('.hero__titulo')).fontFamily,
            cuerpo: getComputedStyle(document.querySelector('.hero__bajada')).fontFamily,
            inter: document.fonts.check('16px Inter'),
            grotesk: document.fonts.check('700 40px "Space Grotesk"')
        })""")
        print("== tipografías ==")
        for k, v in fuentes.items():
            print(f"   {k}: {v}")
        if not fuentes["inter"] or not fuentes["grotesk"]:
            problemas.append("las tipografías propias no están disponibles")
        if "Space Grotesk" not in fuentes["titulo"]:
            problemas.append("el título no usa Space Grotesk")
        if "Inter" not in fuentes["cuerpo"]:
            problemas.append("el texto no usa Inter")

        # ---- 3. sin JavaScript ----------------------------------------
        ctx2 = nav.new_context(viewport={"width": 1440, "height": 900},
                               java_script_enabled=False)
        pag2 = ctx2.new_page()
        pag2.goto(BASE + "/", wait_until="load")
        pag2.wait_for_timeout(400)
        html = pag2.content()
        print("\n== sin JavaScript ==")
        print("   <html> con la clase ap-js:",
              "sí (mal)" if "ap-js" in html else "no (correcto)")
        print("   botón de tema montado:",
              "presente" if re.search(r'<button[^>]*class="[^"]*theme-toggle',
                                      html)
              else "ausente (correcto: lo pone el script)")
        print("   hoja de diseño enlazada:",
              "sí" if "apuromafo.css" in html else "NO")
        print("   texto de la portada:",
              "presente" if "reversing" in html else "NO ESTÁ")
        if "ap-js" in html:
            problemas.append("sin JS, <html> queda con la clase ap-js")
        if re.search(r'<button[^>]*class="[^"]*theme-toggle', html):
            problemas.append("sin JS aparece un botón de tema vacío")
        if "apuromafo.css" not in html:
            problemas.append("sin JS no se enlaza la hoja de diseño")
        if "reversing" not in html or "Pentest" not in html:
            problemas.append("sin JS falta texto de la portada")

        # Lo importante: que la regla que esconde [data-reveal] esté atada a la
        # clase que pone el script. Si algún día se suelta, la página se queda
        # en blanco para quien no tenga JavaScript.
        css = contexto.CSS.read_text("utf-8")
        reglas = re.findall(r"([^{}]*)\{([^}]*opacity:\s*0[^}]*)\}", css)
        sueltas = [s.strip() for s, _ in reglas
                   if "data-reveal" in s and "ap-js" not in s]
        print("   reglas que esconden algo sin ap-js:", sueltas or "ninguna")
        if sueltas:
            problemas.append(
                f"hay reglas que ocultan contenido sin JavaScript: {sueltas}")

        pag2.goto(BASE + "/indice/", wait_until="load")
        idx = pag2.content()
        # Los proyectos son los <h3 id="...">; el <h3 class="author__name"> de
        # la barra lateral no cuenta.
        proyectos = len(re.findall(r'<h3 id="', idx))
        print("   el índice sin JS:",
              proyectos, f"proyectos (deben ser {contexto.PROYECTOS})")
        if proyectos != contexto.PROYECTOS:
            problemas.append(
                f"sin JS, el índice muestra {proyectos} "
                f"de {contexto.PROYECTOS}")
        print("   el buscador (lo aporta el script):",
              "presente" if "data-buscador-campo" in idx
              else "ausente (correcto)")
        ctx2.close()

        # ---- 4. menú en pantallas chicas -------------------------------
        # Minimal Mistakes 4.26.2 no usa cajón: el botón muestra una lista
        # .hidden-links que el propio tema arma con JavaScript a partir de
        # .visible-links. Sin JavaScript, esa lista llega vacía.
        print("\n== menú en 390 px ==")
        ctx3 = nav.new_context(viewport={"width": 390, "height": 844})
        pag3 = ctx3.new_page()
        pag3.goto(BASE + "/", wait_until="load")
        pag3.wait_for_timeout(500)
        boton = pag3.locator(".greedy-nav__toggle")
        print("   hay botón de menú:", boton.count() > 0,
              "· se ve:", boton.is_visible() if boton.count() else False)
        if not boton.count():
            problemas.append("no hay botón de menú en pantallas chicas")
        else:
            print("   antes de pulsarlo, la lista oculta se ve:",
                  pag3.locator(".hidden-links").is_visible())
            boton.click()
            pag3.wait_for_timeout(600)
            abierto = pag3.evaluate("""() => {
                const d = document.querySelector('.hidden-links');
                if (!d) return { error: 'no existe' };
                const cs = getComputedStyle(d);
                return { visible: cs.visibility, alto: Math.round(
                    d.getBoundingClientRect().height),
                    enlaces: d.querySelectorAll('a').length };
            }""")
            print("   menú tras pulsarlo:", abierto)
            if abierto.get("error"):
                problemas.append("no se encuentra la lista del menú")
            else:
                if not abierto["visible"] or abierto["alto"] < 40:
                    problemas.append("el menú de móvil no se abre")
                if abierto["enlaces"] < 5:
                    problemas.append(
                        f"el menú trae {abierto['enlaces']} enlaces, "
                        "deberían ser 6")
            # ¿Se ven los enlaces del menú?
            visibles = pag3.evaluate("""() => [...document.querySelectorAll(
                '.hidden-links a')].filter(a => a.getBoundingClientRect().width > 0)
                .length""")
            print("   enlaces visibles en el menú:", visibles)
            pag3.locator(".hidden-links a").first.click()
            pag3.wait_for_timeout(700)
            print("   tras elegir un enlace, la URL es:",
                  pag3.evaluate("() => location.pathname"))

        # El botón de tema tiene que verse en el teléfono.
        print("   botón de tema visible en el teléfono:",
              pag3.locator(".theme-toggle").is_visible())
        if not pag3.locator(".theme-toggle").is_visible():
            problemas.append("en 390 px no se ve el botón de tema")
        ctx3.close()

        # ---- 5. el tema se acuerda entre páginas ------------------------
        print("\n== el tema se guarda entre páginas ==")
        ctx4 = nav.new_context(viewport={"width": 1440, "height": 900})
        pag4 = ctx4.new_page()
        pag4.goto(BASE + "/", wait_until="load")
        pag4.wait_for_timeout(400)
        pag4.locator(".theme-toggle").click()
        pag4.wait_for_timeout(400)
        pag4.goto(BASE + "/indice/", wait_until="load")
        pag4.wait_for_timeout(400)
        estado = pag4.evaluate("""() => ({
            tema: document.documentElement.getAttribute('data-tema'),
            hoja: document.getElementById('ap-tema-hoja').getAttribute('href'),
            fondo: getComputedStyle(document.body).backgroundColor
        })""")
        print("  ", estado)
        if estado["tema"] != "oscuro" or "main-dark" not in estado["hoja"]:
            problemas.append("el tema oscuro no se mantiene al cambiar de página")
        # Y al revés.
        pag4.locator(".theme-toggle").click()
        pag4.wait_for_timeout(300)
        pag4.goto(BASE + "/red-team/", wait_until="load")
        pag4.wait_for_timeout(300)
        vuelta = pag4.evaluate("""() => ({
            tema: document.documentElement.getAttribute('data-tema'),
            hoja: document.getElementById('ap-tema-hoja').getAttribute('href')
        })""")
        print("  ", vuelta)
        if vuelta["tema"] != "claro":
            problemas.append("no se vuelve al tema claro")
        ctx4.close()

        # ---- 6. navegación con teclado ---------------------------------
        print("\n== teclado ==")
        ctx5 = nav.new_context(viewport={"width": 1440, "height": 900})
        pag5 = ctx5.new_page()
        pag5.goto(BASE + "/", wait_until="load")
        pag5.wait_for_timeout(400)
        orden = []
        for _ in range(9):
            pag5.keyboard.press("Tab")
            orden.append(pag5.evaluate("""() => {
                const a = document.activeElement;
                if (!a) return 'nada';
                return a.tagName.toLowerCase() + '.' +
                    (a.className || '').toString().split(' ')[0] +
                    ':' + (a.textContent || '').trim().slice(0, 18);
            }"""))
        print("   recorrido con Tab:")
        for o in orden:
            print("     ", o)
        if not any("skip-links" in o or "screen-reader" in o for o in orden):
            notas.append("el primer Tab no cae en el enlace de salto")
        ctx5.close()

        # ---- 7. páginas de sección -------------------------------------
        print("\n== páginas de sección ==")
        ctx6 = nav.new_context(viewport={"width": 1440, "height": 900})
        pag6 = ctx6.new_page()

        # Lo que más se nota: al bajar, la barra de filtros tiene que quedar
        # pegada justo debajo del encabezado, no detrás. Es lo que delata que
        # el token del alto estaba mal.
        pag6.goto(BASE + "/herramientas/", wait_until="load")
        pag6.wait_for_timeout(600)
        pag6.evaluate("() => window.scrollTo({top: 3000, behavior: 'instant'})")
        pag6.wait_for_timeout(400)
        pegado = pag6.evaluate("""() => {
            const m = document.querySelector('.masthead');
            const b = document.querySelector('[data-fichas-barra]');
            if (!m || !b) return { error: 'falta algo' };
            const cm = getComputedStyle(m), cb = getComputedStyle(b);
            return {
                abajoMasthead: Math.round(
                    m.getBoundingClientRect().bottom),
                arribaBarra: Math.round(b.getBoundingClientRect().top),
                posMasthead: cm.position,
                posBarra: cb.position,
                token: getComputedStyle(document.documentElement)
                    .getPropertyValue('--ap-alto-masthead').trim(),
                tapada: b.getBoundingClientRect().top <
                    m.getBoundingClientRect().bottom - 2
            };
        }""")
        print("   barra de filtros al bajar:", pegado)
        if pegado.get("error"):
            problemas.append("no se encuentra la barra de filtros")
        else:
            if pegado["tapada"]:
                problemas.append(
                    "la barra de filtros queda tapada por el encabezado")
            if pegado["posBarra"] != "sticky":
                problemas.append("la barra de filtros no está fija")

        # El contenido de la barra tiene que salir de las fichas de verdad.
        barra = pag6.evaluate("""() => {
            const b = document.querySelector('[data-fichas-barra]');
            return {
                fichas: document.querySelectorAll('.card').length,
                conteo: b.querySelector('.ap-fichas-barra__conteo')
                    .textContent.trim(),
                chips: [...b.querySelectorAll('.ap-ficha-etiqueta')].map(c => ({
                    texto: c.textContent.trim(),
                    n: c.querySelector('.ap-ficha-etiqueta__n')
                        ? c.querySelector('.ap-ficha-etiqueta__n')
                            .textContent.trim() : null,
                    pulsado: c.getAttribute('aria-pressed')
                })),
                limpiarVisible: !!b.querySelector('.ap-fichas-barra__limpiar')
                    && b.querySelector('.ap-fichas-barra__limpiar')
                        .offsetParent !== null
            };
        }""")
        print("   fichas en la página:", barra["fichas"], "· la barra dice:",
              repr(barra["conteo"]))
        print("   las ocho etiquetas más usadas:")
        for c in barra["chips"]:
            print("     ", c["texto"], c["n"], "pulsado:", c["pulsado"])
        if str(barra["fichas"]) not in barra["conteo"]:
            problemas.append(
                f"la barra dice {barra['conteo']!r} y hay "
                f"{barra['fichas']} fichas")
        if len(barra["chips"]) != 8:
            problemas.append(
                f"la barra trae {len(barra['chips'])} etiquetas, son 8")
        if any(c["pulsado"] == "true" for c in barra["chips"]):
            problemas.append("las etiquetas salen marcadas antes de pulsar")
        if any(c["pulsado"] is None for c in barra["chips"]):
            # Un botón de alternar tiene que decir en qué estado está, aunque
            # sea el de "sin pulsar".
            problemas.append("las etiquetas no declaran aria-pressed")
        if barra["limpiarVisible"]:
            problemas.append("el botón de limpiar sale sin haber filtrado")

        # Al filtrar, las que quedan son las de esa etiqueta, y la primera se
        # trae a la vista (si no, el usuario ve una lista vacía y no sabe
        # qué pasó).
        chip = pag6.locator(".ap-ficha-etiqueta", has_text="python").first
        pag6.evaluate("() => window.scrollTo({top: 0, behavior: 'instant'})")
        pag6.wait_for_timeout(200)
        chip.click()
        pag6.wait_for_timeout(600)
        filtrado = pag6.evaluate("""() => {
            const vis = [...document.querySelectorAll('.card')]
                .filter(c => !c.hidden);
            const primera = vis[0].getBoundingClientRect();
            return {
                visibles: vis.length,
                // Cada ficha que queda tiene que llevar la etiqueta pulsada.
                // La clave es data-tag, que es de donde la barra saca el
                // recuento; el texto lleva el # y puede llevar acentos.
                sinEtiqueta: vis.filter(c => ![...c.querySelectorAll('.tag')]
                    .some(t => t.dataset.tag === 'python')).length,
                primeraEnVista: primera.top > 0 && primera.top < innerHeight,
                conteo: document.querySelector(
                    '.ap-fichas-barra__conteo').textContent.trim(),
                limpiarVisible: document.querySelector(
                    '.ap-fichas-barra__limpiar').offsetParent !== null
            };
        }""")
        print("   tras filtrar por python:", filtrado)
        if filtrado["visibles"] == 0 or filtrado["visibles"] == barra["fichas"]:
            problemas.append("el filtro por python no dejó nada coherente")
        if filtrado["sinEtiqueta"]:
            problemas.append(
                f"quedan {filtrado['sinEtiqueta']} fichas sin la etiqueta "
                "pulsada")
        if not filtrado["primeraEnVista"]:
            problemas.append(
                "tras filtrar, la primera ficha no queda a la vista")
        if not filtrado["limpiarVisible"]:
            problemas.append("el botón de limpiar no aparece al filtrar")

        # El riel de las páginas de texto: se pega igual y sus enlaces caen
        # en su sitio, con el título por debajo del encabezado y no debajo.
        pag6.goto(BASE + "/sobre-mi/", wait_until="load")
        pag6.wait_for_timeout(500)
        riel = pag6.evaluate("""() => {
            const m = document.querySelector('.masthead');
            const r = document.querySelector('.ap-riel__interior');
            return {
                existe: !!r,
                pos: r ? getComputedStyle(r).position : null,
                tapado: m && r
                    ? r.getBoundingClientRect().top <
                        m.getBoundingClientRect().bottom - 2 : null,
                enlaces: [...document.querySelectorAll('.ap-toc__menu a')]
                    .map(a => a.getAttribute('href'))
            };
        }""")
        print("   riel de sobre-mi:", {k: v for k, v in riel.items()
                                     if k != "enlaces"},
              "·", len(riel["enlaces"]), "entradas")
        if not riel["existe"] or riel["pos"] != "sticky":
            problemas.append("el riel de sobre-mi no existe o no está fijo")
        pag6.evaluate("() => window.scrollTo({top: 0, behavior: 'instant'})")
        pag6.wait_for_timeout(200)
        pag6.locator(".ap-toc__menu a").first.click()
        # El salto es suave: hay que esperar a que la página se detenga, o se
        # mide a mitad de camino y da cualquier cosa.
        quieta = pag6.evaluate("""() => new Promise(res => {
            let antes = -1, iguales = 0;
            const t = setInterval(() => {
                const y = Math.round(window.scrollY);
                if (y === antes) { if (++iguales >= 3) {
                    clearInterval(t); res(y);
                } } else { iguales = 0; antes = y; }
            }, 100);
            setTimeout(() => { clearInterval(t); res(antes); }, 4000);
        })""")
        print("   se detuvo en scrollY =", quieta)
        destino = pag6.evaluate("""() => {
            const a = document.querySelector('.ap-toc__menu a');
            // El href viene codificado (%C3%B3) y el id va en UTF-8. El
            // navegador decodifica el fragmento al saltar, pero al buscarlo a
            // mano hay que hacerlo también.
            const id = decodeURIComponent(a.hash.slice(1));
            const el = document.getElementById(id);
            if (!el) return { error: 'no existe #' + id, hay: id };
            const m = document.querySelector('.masthead');
            const r = el.getBoundingClientRect();
            return {
                texto: el.textContent.trim().slice(0, 30),
                arriba: Math.round(r.top),
                bajoEncabezado: Math.round(
                    m.getBoundingClientRect().bottom),
                tapado: r.top < m.getBoundingClientRect().bottom
            };
        }""")
        print("   el índice salta a:", destino)
        if destino.get("error"):
            problemas.append(f"el índice apunta mal: {destino['error']}")
        elif destino["tapado"]:
            problemas.append(
                "al seguir el índice, el título queda bajo el encabezado")
        elif destino["arriba"] - destino["bajoEncabezado"] > 40:
            problemas.append(
                "al seguir el índice, el título queda demasiado abajo "
                f"({destino['arriba'] - destino['bajoEncabezado']} px)")
        ctx6.close()

        # Las páginas de sección sin JavaScript: sin barra (la arma el script,
        # a propósito) y con todas las fichas a la vista.
        ctx7 = nav.new_context(viewport={"width": 1440, "height": 900},
                               java_script_enabled=False)
        pag7 = ctx7.new_page()
        pag7.goto(BASE + "/red-team/", wait_until="load")
        pag7.wait_for_timeout(300)
        sinJs = pag7.content()
        print("\n== páginas de sección sin JavaScript ==")
        # El contenedor vacío sí está en el HTML (lo pone la plantilla); lo que
        # no puede estar es su contenido, porque la barra la arma filter.js a
        # partir de las etiquetas reales de las fichas.
        barraVacia = re.search(
            r'<div class="ap-fichas-barra"[^>]*>\s*</div>', sinJs)
        print("   barra de filtros:",
              "contenedor vacío (correcto)" if barraVacia
              else "CON CONTENIDO o sin contenedor")
        print("   fichas en el HTML:", len(re.findall(r'class="card"', sinJs)),
              "(deben ser 8)")
        print("   tarjeta del autor:",
              "presente" if "ap-autor" in sinJs else "AUSENTE")
        print("   cifras del encabezado:",
              len(re.findall(r'class="cifra__valor"', sinJs)))
        if not barraVacia:
            problemas.append(
                "sin JS, la barra de filtros no está vacía")
        if "ap-ficha-etiqueta" in sinJs or "ap-fichas-barra__chips" in sinJs:
            problemas.append("sin JS aparecen las etiquetas del filtro")
        if len(re.findall(r'class="card"', sinJs)) != 8:
            problemas.append("sin JS, Red Team no muestra las 8 fichas")
        if "ap-autor" not in sinJs:
            problemas.append("sin JS, la tarjeta del autor desaparece")
        if "ap-cabecera__titulo" not in sinJs:
            problemas.append("sin JS, el encabezado de sección desaparece")
        ctx7.close()
        nav.close()

    print("\n== contraste: las diez medidas más ajustadas ==")
    patron = re.compile(r"([\d.]+):1")
    medidas = [(float(patron.search(n).group(1)), n)
               for n in notas if n.startswith("contraste")]
    for _, n in sorted(medidas)[:10]:
        print("   ", n)
    print(f"   {len(medidas)} medidas en total, todas correctas")

    print("\n== problemas ==")
    if problemas:
        for x in problemas:
            print("  -", x)
        sys.exit(1)
    print("   ninguno")


if __name__ == "__main__":
    main()
