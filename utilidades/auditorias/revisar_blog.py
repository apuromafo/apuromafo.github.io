"""Medidas de las piezas del blog: la columna de lectura de la entrada y las
tarjetas del índice. No se pueden mirar las capturas, así que se mide lo que el
diseño promete y se falla cuando una medida se sale de lo prometido.

Sale con 0 si todo cuadra, con 1 si encontró algo y con 2 si no pudo ni
arrancar. Antes solo informaba, y una auditoría que no puede fallar no audita
nada.

Lo que se comprueba, en las dos páginas y en los dos temas:
  (a) que la columna de lectura existe, es más estrecha que la ventana y está
      centrada (márgenes izquierdo y derecho iguales);
  (b) que el texto de lectura no baja de 16 px;
  (c) que la página no desborda en horizontal;
  (d) que en el índice hay al menos una ficha, cada una con fecha y con título
      más grande que su metadato;
  (e) que en el teléfono la columna de lectura entra en la pantalla y no se
      queda estrecha de más.

Uso:  python utilidades/auditorias/revisar_blog.py [dirección del servidor]
"""

import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else contexto.BASE

# El índice y la entrada. La dirección de la entrada cambia cada vez que se le
# cambia la fecha o el título, así que sale de la configuración por nombre y no
# escrita aquí, que era una forma de que esta auditoría se quedara callada
# mirando una página que ya no existe.
BLOG, ENTRADA = contexto.GRUPOS["blog"]

# Los dos anchos que se miden: escritorio y teléfono, que es donde las
# medidas se rompen.
ESCRITORIO, TELEFONO = contexto.ANCHOS

fallos = []


def chequear(ok, texto, detalle=""):
    print(("  OK   " if ok else "  FALLA") + "  " + texto
          + ("   " + detalle if detalle else ""))
    if not ok:
        fallos.append(texto + (" | " + detalle if detalle else ""))
    return ok


# Las medidas llegan como texto (las devuelve getComputedStyle), así que para
# comparar hay que convertirlas; un valor que no sea número vale 0 y la
# comprobación que lo use fallará sola, que es justo lo que se quiere ver.
def numero(valor):
    try:
        return float(str(valor).replace("px", "").strip())
    except (TypeError, ValueError):
        return 0.0


MEDIR_ENTRADA = """() => {
  const q = (s) => document.querySelector(s);
  const caja = q('.ap-cuerpo__principal--lectura');
  const chip = q('.ap-entrada__etiquetas .ap-chip');
  const fecha = q('.ap-entrada__fecha');
  const autor = q('.ap-cierre-autor');
  const art = q('.ap-seccion-contenido');
  const titulo = q('.ap-cabecera__titulo');
  const antetitulo = q('.ap-cabecera__antetitulo');
  if (!caja || !art || !titulo) return {faltan: true};
  const cs = (el) => getComputedStyle(el);
  const r = caja.getBoundingClientRect();
  return {
    ancho_principal: Math.round(r.width),
    ancho_ventana: window.innerWidth,
    izquierda_principal: Math.round(r.left),
    derecha_principal: Math.round(window.innerWidth - r.right),
    ancho_texto: Math.round(art.getBoundingClientRect().width),
    fuente_texto: cs(art).fontSize + ' / ' + cs(art).lineHeight,
    fuente_texto_px: parseFloat(cs(art).fontSize),
    fuente_texto_familia: cs(art).fontFamily.split(',')[0],
    fecha_texto: fecha ? fecha.textContent.trim() : null,
    fecha_fuente: fecha ? cs(fecha).fontSize + ' ' +
               cs(fecha).fontFamily.split(',')[0] : null,
    chip_texto: chip ? chip.textContent.trim() : null,
    chip_fuente: chip ? cs(chip).fontSize : null,
    autor_ancho: autor ? Math.round(autor.getBoundingClientRect().width) : null,
    titulo: titulo.textContent.trim(),
    antetitulo_texto: antetitulo ? antetitulo.textContent.trim() : null,
    antetitulo_enlace: !!(antetitulo && antetitulo.querySelector('a')),
    desborde: document.documentElement.scrollWidth - window.innerWidth,
  };
}"""

MEDIR_BLOG = """() => {
  const q = (s) => document.querySelector(s);
  const fila = q('.ap-entrada-fila');
  if (!fila) return {faltan: true};
  const h2 = q('.ap-entrada-fila__titulo');
  const meta = q('.ap-entrada-fila__meta');
  const bajada = q('.ap-entrada-fila__bajada');
  const cs = (el) => getComputedStyle(el);
  const c = fila.getBoundingClientRect();
  return {
    filas: document.querySelectorAll('.ap-entrada-fila').length,
    ancho_tarjeta: Math.round(c.width),
    alto_tarjeta: Math.round(c.height),
    titulo_fuente: cs(h2).fontSize + ' / ' + cs(h2).lineHeight,
    titulo_fuente_px: parseFloat(cs(h2).fontSize),
    titulo_margen: cs(h2).marginTop + ' ' + cs(h2).marginBottom,
    titulo_borde: cs(h2).borderBottomWidth,
    // El pseudoelemento va como segundo argumento de getComputedStyle; sin él
    // esto devolvía el content del propio h2 ("normal") y no miraba nada.
    titulo_antes: getComputedStyle(h2, '::before').content,
    meta_fuente_px: parseFloat(cs(meta).fontSize),
    bajada_ancho: Math.round(bajada.getBoundingClientRect().width),
    fondo_tarjeta: cs(fila).backgroundColor,
    borde_tarjeta: cs(fila).borderTopWidth,
    radio: cs(fila).borderTopLeftRadius,
    reveal: fila.getAttribute('data-reveal'),
    fecha_texto: q('.ap-entrada-fila__meta time').textContent.trim(),
    etiquetas: [...document.querySelectorAll('.ap-entrada-fila__etiquetas .ap-chip')]
      .map((e) => e.textContent.trim()),
    titulos: [...document.querySelectorAll('.ap-entrada-fila__titulo')]
      .map((e) => e.textContent.trim()),
    desborde: document.documentElement.scrollWidth - window.innerWidth,
  };
}"""


def comprobar_entrada(m, esquema):
    print(f"== entrada / {esquema}")
    for k, v in m.items():
        print(f"   {k:22} {v}")
    if m.get("faltan"):
        return chequear(False, "la entrada tiene columna de lectura y título")
    ventana = m["ancho_ventana"]
    chequear(0 < m["ancho_principal"] < ventana,
             "(a) la columna de lectura es más estrecha que la ventana",
             f"{m['ancho_principal']} de {ventana}")
    chequear(abs(m["izquierda_principal"] - m["derecha_principal"]) <= 2,
             "(a) y está centrada",
             f"izq {m['izquierda_principal']} / der {m['derecha_principal']}")
    chequear(numero(m["fuente_texto_px"]) >= 16,
             "(b) el texto de lectura es de 16 px o más",
             m["fuente_texto"])
    chequear(m["desborde"] <= 1, "(c) la entrada no desborda en horizontal",
             f"{m['desborde']}px")
    chequear(bool(m["titulo"]), "el título de la entrada tiene texto",
             m["titulo"])
    chequear(bool(m["fecha_texto"]), "la entrada lleva su fecha",
             str(m["fecha_texto"]))
    chequear(bool(m["chip_texto"]), "la entrada lleva al menos una etiqueta",
             str(m["chip_texto"]))


def comprobar_indice(m, esquema):
    print(f"== indice del blog / {esquema}")
    for k, v in m.items():
        print(f"   {k:22} {v}")
    if m.get("faltan"):
        return chequear(False, "el índice del blog tiene fichas")
    chequear(m["filas"] >= 1, "(d) el índice tiene al menos una ficha",
             f"{m['filas']}")
    chequear(m["ancho_tarjeta"] <= contexto.ANCHOS[0][1],
             "las fichas no son más anchas que la ventana",
             f"{m['ancho_tarjeta']}")
    chequear(numero(m["titulo_fuente_px"]) > numero(m["meta_fuente_px"]),
             "(d) el título de la ficha es más grande que su metadato",
             f"{m['titulo_fuente']} contra {m['meta_fuente_px']}px")
    chequear(bool(m["fecha_texto"]), "(d) la ficha lleva fecha en español",
             m["fecha_texto"])
    chequear(len(m["titulos"]) == m["filas"] and all(m["titulos"]),
             "(d) todas las fichas tienen título", str(m["titulos"]))
    chequear(m["desborde"] <= 1, "(c) el índice no desborda en horizontal",
             f"{m['desborde']}px")


MEDIR_TEL = """() => {
  const f = document.querySelector('.ap-cuerpo__principal--lectura')
    || document.querySelector('.ap-cuerpo__principal');
  if (!f) return {faltan: true};
  const r = f.getBoundingClientRect();
  return {
    ancho_principal: Math.round(r.width),
    ancho_ventana: window.innerWidth,
    desborde: document.documentElement.scrollWidth - window.innerWidth,
  };
}"""


def main():
    with sync_playwright() as p:
        nav = p.chromium.launch()
        for esquema in contexto.TEMAS:
            ctx = nav.new_context(
                viewport={"width": ESCRITORIO[1], "height": ESCRITORIO[2]},
                color_scheme=esquema)
            pag = ctx.new_page()

            pag.goto(BASE + ENTRADA[1], wait_until="load")
            pag.wait_for_timeout(400)
            comprobar_entrada(pag.evaluate(MEDIR_ENTRADA), esquema)

            pag.goto(BASE + BLOG[1], wait_until="load")
            pag.wait_for_timeout(400)
            comprobar_indice(pag.evaluate(MEDIR_BLOG), esquema)

            ctx.close()

        # El teléfono es el otro ancho donde las medidas se rompen.
        ctx = nav.new_context(
            viewport={"width": TELEFONO[1], "height": TELEFONO[2]},
            is_mobile=True, has_touch=True, device_scale_factor=3)
        pag = ctx.new_page()
        for nombre, ruta in ((BLOG[0], BLOG[1]), (ENTRADA[0], ENTRADA[1])):
            pag.goto(BASE + ruta, wait_until="load")
            pag.wait_for_timeout(400)
            m = pag.evaluate(MEDIR_TEL)
            ventana = numero(m.get("ancho_ventana"))
            ancho = numero(m.get("ancho_principal"))
            print(f"== {nombre} en telefono: principal/ventana/doc  "
                  f"{m.get('ancho_principal')} / {m.get('ancho_ventana')} / "
                  f"{ventana + numero(m.get('desborde')):.0f}")
            chequear(not m.get("faltan") and 0 < ancho <= ventana,
                     f"(e) {nombre}: la columna entra en la pantalla",
                     f"{ancho:.0f} de {ventana:.0f}px")
            chequear(ancho >= ventana * 0.6,
                     f"(e) {nombre}: y no queda estrecha de más",
                     f"{ancho:.0f}px = {100 * ancho / ventana:.0f}% de la pantalla")
            chequear(numero(m.get("desborde")) <= 1,
                     f"(c) {nombre} en telefono no desborda",
                     f"{m.get('desborde')}px")
        ctx.close()
        nav.close()

    print()
    if fallos:
        print(f"FALLAS: {len(fallos)}")
        for f in fallos:
            print("  - " + f)
        return 1
    print("TODO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())