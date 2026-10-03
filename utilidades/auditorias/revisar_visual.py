"""Revisión visual y funcional del sitio con un navegador de verdad.

    python revisar_visual.py [carpeta]

Para cada página: la abre en claro y en oscuro, mide lo que se sale de la
pantalla, recoge los errores de JavaScript, comprueba que las fuentes
cargaron, y guarda una captura de la página entera y otra de cómo se ve por
encima del pliegue. Además pulsa de verdad el filtro por etiquetas, el
interruptor de tema y el buscador, porque lo que no se ha pulsado no se sabe
si funciona.
"""

import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

# De dónde salen la dirección del servidor, la carpeta de capturas, las páginas,
# los anchos y los temas es de la configuración, no de aquí: si el sitio crece
# o se cambia el puerto, se toca ap.config.json una vez y no estos siete
# archivos. El primer argumento sigue mandando sobre la carpeta de capturas.
BASE = contexto.BASE
DESTINO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else contexto.CAPTURAS

PAGINAS = contexto.PAGINAS
ANCHOS = contexto.ANCHOS
TEMAS = contexto.TEMAS


def desbordes(pagina):
    """Elementos que se salen de la ventana.

    Se ignoran los que están dentro de una caja con desplazamiento propio
    (un bloque de código largo dentro de un <pre> con overflow auto se sale a
    propósito y no empuja la página), y los que el tema deja a la vista por
    un selector suyo.
    """
    return pagina.evaluate(
        """() => {
            const limite = document.documentElement.clientWidth;
            const rueda = el => {
                for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
                    const ox = getComputedStyle(n).overflowX;
                    if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') return true;
                }
                return false;
            };
            const malos = [];
            document.querySelectorAll('body *').forEach(el => {
                const c = el.getBoundingClientRect();
                if (c.width === 0 && c.height === 0) return;
                if (c.right > limite + 1 || c.left < -1) {
                    if (rueda(el)) return;
                    malos.push({
                        etiqueta: el.tagName.toLowerCase(),
                        clase: (el.className || '').toString().slice(0, 60),
                        izquierda: Math.round(c.left),
                        derecha: Math.round(c.right)
                    });
                }
            });
            return malos.slice(0, 8);
        }"""
    )


def revisar(pagina, nombre, etiqueta, problemas):
    report = pagina.evaluate(
        """() => {
            const h = document.documentElement;
            const fuentesCargadas = [...document.fonts].map(f => f.family);

            // Los iconos que escribe el tema (clases fa-*) se redibujan con una
            // máscara. Si a alguno no se le puso, es un hueco que no se ve.
            const iconosTema = [...document.querySelectorAll("[class*='fa-']")]
                .map(el => {
                    const cs = getComputedStyle(el, '::before');
                    return {
                        clase: el.className,
                        mascara: cs.maskImage || cs.webkitMaskImage || 'none'
                    };
                })
                .filter(i => i.mascara === 'none' || i.mascara === '');

            // El texto que rota en el héroe se apila en la misma celda: solo
            // puede haber uno visible. Si hay dos, se leen superpuestos.
            const rotador = [...document.querySelectorAll(
                '[data-rotator-item]')].map(el => ({
                    texto: el.textContent.trim(),
                    opacidad: Math.round(
                        parseFloat(getComputedStyle(el).opacity) * 100) / 100
                }));
            const rotadorVisibles = rotador.filter(r => r.opacidad > 0.05);

            // Páginas de sección (_layouts/ap-seccion.html): encabezado, ancho
            // del contenido, riel, números de ficha y enlaces del autor.
            const cab = document.querySelector('.ap-cabecera__titulo');
            const cuerpo = document.querySelector('.ap-cuerpo__principal');
            const masthead = document.querySelector('.masthead');
            const primerH3 = document.querySelector(
                '.ap-seccion-contenido .card h3');
            const riel = document.querySelector('.ap-riel__interior');
            const barra = document.querySelector('[data-fichas-barra]');
            const token = getComputedStyle(document.documentElement)
                .getPropertyValue('--ap-alto-masthead').trim();

            const tocRoto = [...document.querySelectorAll('.ap-toc__menu a')]
                .map(a => a.getAttribute('href'))
                .filter(href => href && href.startsWith('#') &&
                    !document.getElementById(href.slice(1)));

            const seccion = {
                cabecera: !!cab,
                cifras: document.querySelectorAll('.ap-cabecera__cifras li').length,
                anchoContenido: cuerpo
                    ? Math.round(cuerpo.getBoundingClientRect().width) : null,
                altoMasthead: masthead ? Math.round(masthead.offsetHeight) : null,
                tokenMasthead: token,
                numero: primerH3
                    ? getComputedStyle(primerH3, '::before').content : null,
                riel: !!riel,
                rielPegado: riel ? getComputedStyle(riel).position : null,
                tocRoto,
                barra: !!barra,
                pegada: barra ? getComputedStyle(barra).position : null,
                autorEnlaces: document.querySelectorAll('.ap-autor__enlace').length,
                autorIconosVacios: [...document.querySelectorAll(
                    '.ap-autor__enlace svg')].filter(s => !s.getAttribute('viewBox'))
                    .length
            };

            return {
                scrollH: h.scrollHeight,
                ancho: h.clientWidth,
                anchoVentana: window.innerWidth,
                scrollAncho: h.scrollWidth,
                tema: h.getAttribute('data-tema'),
                apJs: h.classList.contains('ap-js'),
                fuentes: fuentesCargadas,
                iconosSvg: document.querySelectorAll('svg').length,
                iconosSinDibujar: iconosTema,
                rotador,
                rotadorVisibles,
                seccion,
                h1: document.querySelectorAll('h1').length,
                botonTema: !!document.querySelector('.theme-toggle'),
                volver: !!document.querySelector('.ap-volver'),
                progreso: !!document.querySelector('.ap-progreso'),
                visibles: document.querySelectorAll('[data-reveal].es-visible').length,
                conRevelar: document.querySelectorAll('[data-reveal]').length
            };
        }"""
    )
    if report["scrollAncho"] > report["ancho"] + 1:
        problemas.append(
            f"{nombre}/{etiqueta}: scroll horizontal "
            f"({report['scrollAncho']} > {report['ancho']})")
    if report["h1"] != 1:
        problemas.append(f"{nombre}/{etiqueta}: {report['h1']} <h1> (debe haber 1)")
    if not report["apJs"]:
        problemas.append(f"{nombre}/{etiqueta}: app.js no arrancó")
    if not report["iconosSvg"]:
        problemas.append(f"{nombre}/{etiqueta}: no hay iconos dibujados")
    if report["iconosSinDibujar"]:
        problemas.append(
            f"{nombre}/{etiqueta}: iconos del tema sin dibujo "
            f"{[i['clase'] for i in report['iconosSinDibujar']][:4]}")
    if report["conRevelar"] and report["visibles"] != report["conRevelar"]:
        problemas.append(
            f"{nombre}/{etiqueta}: quedaron {report['conRevelar'] - report['visibles']}"
            f" de {report['conRevelar']} sin revelar")
    if len(report["rotadorVisibles"]) > 1:
        problemas.append(
            f"{nombre}/{etiqueta}: el texto que rota muestra "
            f"{len(report['rotadorVisibles'])} a la vez "
            f"{[r['texto'] for r in report['rotadorVisibles']]}")

    s = report["seccion"]
    if s["cabecera"]:
        # En el teléfono el contenido sí va angosto (es lo que tiene que pasar)
        # y el riel va al final, sin pegarse. Solo se revisa lo de pantalla
        # grande: a partir de 1152 px es donde el riel existe.
        ancho = report["anchoVentana"]
        # La barra y el riel se pegan con top: var(--ap-alto-masthead). Si el
        # alto real del encabezado no es el del token, se montan uno sobre otro
        # o queda un hueco al bajar.
        if s["altoMasthead"] and s["tokenMasthead"]:
            esperado = float(s["tokenMasthead"].replace("px", "").strip())
            if abs(s["altoMasthead"] - esperado) > 2:
                problemas.append(
                    f"{nombre}/{etiqueta}: el encabezado mide {s['altoMasthead']} px"
                    f" y el token dice {s['tokenMasthead']}")
        if s["pegada"] not in (None, "sticky"):
            problemas.append(
                f"{nombre}/{etiqueta}: la barra de filtros no se queda pegada"
                f" (position: {s['pegada']})")
        if s["tocRoto"]:
            problemas.append(
                f"{nombre}/{etiqueta}: enlaces del índice sin destino "
                f"{s['tocRoto'][:3]}")
        if s["numero"] is not None and s["numero"] in ("none", "normal", ""):
            problemas.append(
                f"{nombre}/{etiqueta}: las fichas no llevan número"
                f" (::before = {s['numero']})")
        if s["autorEnlaces"] and s["autorIconosVacios"]:
            problemas.append(
                f"{nombre}/{etiqueta}: {s['autorIconosVacios']} iconos del autor"
                f" salieron vacíos")
        if ancho >= 1152:
            if s["rielPegado"] not in (None, "sticky"):
                problemas.append(
                    f"{nombre}/{etiqueta}: el riel no se queda pegado"
                    f" (position: {s['rielPegado']})")
            # 646 px era justo lo que se vino a cambiar; por debajo de 620 el
            # texto ya se lee en líneas demasiado cortas en pantalla grande.
            if s["anchoContenido"] and s["anchoContenido"] < 620:
                problemas.append(
                    f"{nombre}/{etiqueta}: el contenido quedó en "
                    f"{s['anchoContenido']} px de ancho")
    return report


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    problemas = []
    resumen = []

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        for nombre, ruta in PAGINAS:
            for etiqueta, ancho, alto in ANCHOS:
                for esquema in TEMAS:
                    ctx = navegador.new_context(
                        viewport={"width": ancho, "height": alto},
                        color_scheme=esquema,
                        device_scale_factor=1,
                    )
                    pagina = ctx.new_page()
                    errores = []
                    pagina.on("console", lambda m: errores.append(m.text)
                              if m.type == "error" else None)
                    pagina.on("pageerror", lambda e: errores.append(str(e)))
                    fallos = []
                    pagina.on("requestfailed",
                              lambda r: fallos.append(f"{r.url} {r.failure}"))

                    pagina.goto(BASE + ruta, wait_until="load")
                    pagina.wait_for_timeout(700)
                    # Recorre la página para que se revele todo lo que hay.
                    # Sin "instant" el scroll del sitio lo vuelve animado y la
                    # comprobación mide cualquier cosa.
                    pagina.evaluate(
                        "async () => {"
                        " const h = document.documentElement.scrollHeight;"
                        " for (let y = 0; y < h; y += 300) {"
                        " window.scrollTo({top: y, behavior: 'instant'});"
                        " await new Promise(r => setTimeout(r, 60)); }"
                        " await new Promise(r => setTimeout(r, 200));"
                        " window.scrollTo({top: 0, behavior: 'instant'}); }"
                    )
                    pagina.wait_for_timeout(500)

                    marca = f"{nombre}-{etiqueta}-{esquema}"
                    report = revisar(pagina, nombre, f"{etiqueta}/{esquema}", problemas)
                    if errores:
                        problemas.append(f"{marca}: errores JS {errores[:3]}")
                    if fallos:
                        problemas.append(f"{marca}: peticiones fallidas {fallos[:3]}")

                    fuera = desbordes(pagina)
                    if fuera:
                        problemas.append(f"{marca}: se sale {fuera}")

                    pagina.screenshot(path=str(DESTINO / f"{marca}.png"),
                                      full_page=False)
                    resumen.append(
                        f"{marca:42} tema={report['tema']:6} "
                        f"alto={report['scrollH']:6} svg={report['iconosSvg']:3} "
                        f"revelados={report['visibles']}/{report['conRevelar']}")
                    ctx.close()

            # ---- pruebas de interacción, una vez por página -------------
            ctx = navegador.new_context(viewport={"width": 1440, "height": 900})
            pagina = ctx.new_page()
            errores = []
            pagina.on("pageerror", lambda e: errores.append(str(e)))
            pagina.goto(BASE + ruta, wait_until="load")
            pagina.wait_for_timeout(400)

            # El filtro por etiquetas solo existe en las páginas que declaran
            # barra (front matter filtro: true). En la portada las etiquetas
            # son rótulos, así que no se pulsa nada ahí.
            if pagina.locator("[data-fichas-barra]").count():
                # La barra tiene que haber salido: si el script falla, el
                # contenedor queda vacío y el filtro sigue escondido.
                if not pagina.locator(".ap-fichas-barra__chip, .tag.ap-ficha-etiqueta").count():
                    problemas.append(f"{nombre}: la barra de filtros salió vacía")

                etiqueta = pagina.locator(".ap-ficha-etiqueta").first
                etiqueta.click()
                pagina.wait_for_timeout(250)
                ocultas = pagina.evaluate(
                    "() => [...document.querySelectorAll('.card')].filter(c => c.hidden).length")
                visibles = pagina.evaluate(
                    "() => [...document.querySelectorAll('.card')].filter(c => !c.hidden).length")
                if visibles == 0 or ocultas == 0:
                    problemas.append(
                        f"{nombre}: el filtro no ocultó nada ({visibles} visibles, {ocultas} ocultas)")
                else:
                    resumen.append(
                        f"{nombre}: filtro -> {visibles} visibles, {ocultas} ocultas")

                if etiqueta.get_attribute("aria-pressed") != "true":
                    problemas.append(f"{nombre}: la etiqueta activa no se marcó")

                if pagina.locator(".ap-fichas-barra__limpiar").is_visible():
                    pagina.locator(".ap-fichas-barra__limpiar").click()
                    pagina.wait_for_timeout(200)
                    todas = pagina.evaluate(
                        "() => [...document.querySelectorAll('.card')].filter(c => !c.hidden).length")
                    if todas != visibles + ocultas:
                        problemas.append(f"{nombre}: limpiar no restauró las fichas")
                else:
                    problemas.append(f"{nombre}: el botón de limpiar no apareció")

            if pagina.locator("[data-buscador] input").count():
                campo = pagina.locator("[data-buscador] input").first
                campo.click()
                campo.type("python", delay=40)
                pagina.wait_for_timeout(350)
                visibles = pagina.evaluate(
                    "() => [...document.querySelectorAll('.ap-indice-lista > *')]"
                    ".filter(e => !e.hidden).length")
                texto = pagina.locator("[data-conteo-buscador]").inner_text()
                resumen.append(f"{nombre}: buscar 'python' -> {visibles} nodos visibles · {texto}")
                if visibles == 0:
                    problemas.append(f"{nombre}: la búsqueda no encontró nada")
                campo.fill("zzzz-no-existe")
                pagina.wait_for_timeout(300)
                if not pagina.locator("#lista-proyectos-vacio").is_visible():
                    problemas.append(f"{nombre}: no aparece el aviso de 'sin resultados'")
                else:
                    resumen.append(f"{nombre}: aviso de sin resultados OK")
                campo.fill("")
                pagina.wait_for_timeout(250)

            # El interruptor de tema tiene que funcionar de verdad.
            if pagina.locator(".theme-toggle").count():
                antes = pagina.evaluate("() => document.documentElement.getAttribute('data-tema')")
                href_antes = pagina.evaluate(
                    "() => document.querySelector('#ap-tema-hoja').getAttribute('href')")
                pagina.locator(".theme-toggle").click()
                pagina.wait_for_timeout(400)
                despues = pagina.evaluate("() => document.documentElement.getAttribute('data-tema')")
                href_despues = pagina.evaluate(
                    "() => document.querySelector('#ap-tema-hoja').getAttribute('href')")
                if antes == despues:
                    problemas.append(f"{nombre}: el botón de tema no cambió el modo")
                else:
                    resumen.append(
                        f"{nombre}: tema {antes} -> {despues} · hoja {href_antes} -> {href_despues}")
                guardado = pagina.evaluate("() => localStorage.getItem('tema')")
                if guardado != despues:
                    problemas.append(f"{nombre}: el tema no se guardó")
                pagina.locator(".theme-toggle").click()
                pagina.wait_for_timeout(250)

            if errores:
                problemas.append(f"{nombre} (interacción): errores JS {errores[:3]}")
            ctx.close()

        navegador.close()

    print("== resumen ==")
    print("\n".join(resumen))
    print("\n== problemas ==")
    if problemas:
        print("\n".join("  - " + x for x in problemas))
        sys.exit(1)
    print("  ninguno")


if __name__ == "__main__":
    main()
