/* ===========================================================================
   Apuromafo — filtro por etiquetas
   ===========================================================================
   Las fichas de Red Team, Programación y Herramientas se filtran haciendo
   clic en cualquiera de sus etiquetas, o con Enter o Espacio si se navega con
   el teclado.

   La barra se construye aquí, no en el markdown, por tres razones:
     · las etiquetas de la barra son las que más se repiten, y eso se cuenta
       sobre las fichas reales en vez de anotarlo a mano y que se envejezca;
     · sin este archivo no queda nada: la barra no existe, todas las fichas se
       ven y las etiquetas son solo texto. Es una mejora progresiva de verdad;
     · las páginas que no piden barra (la portada) no reciben contador ni
       botones: allí las etiquetas son rótulos, no un filtro.

   La barra dice cuántas fichas quedan y trae las etiquetas más usadas, para
   que se vea que se puede filtrar. Se queda pegada al bajar, porque con 33
   fichas hay que poder cambiar de etiqueta sin volver arriba.
   =========================================================================== */

(function () {
  "use strict";

  var sitio = document.querySelector("[data-fichas-barra]");
  if (!sitio) {
    return;
  }

  var tarjetas = Array.prototype.slice.call(document.querySelectorAll(".card"));
  if (!tarjetas.length) {
    return;
  }

  // Los acentos y la eñe no cambian el resultado: "Python" y "python" son la
  // misma etiqueta, y "#Chile" y "#chile" también.
  function normalizar(texto) {
    return String(texto || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function etiquetaDe(el) {
    return normalizar(el.getAttribute("data-tag") || el.textContent);
  }

  function sinMovimiento() {
    return !!(
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  /* --- La barra ---------------------------------------------------------- */

  // Cuántas veces se repite cada etiqueta en las fichas.
  var resumen = {};
  tarjetas.forEach(function (t) {
    Array.prototype.forEach.call(t.querySelectorAll(".tag"), function (el) {
      var clave = etiquetaDe(el);
      if (!clave) {
        return;
      }
      if (!resumen[clave]) {
        resumen[clave] = { texto: "#" + el.getAttribute("data-tag"), n: 0 };
      }
      resumen[clave].n += 1;
    });
  });

  var CUANTAS = 8;
  var claves = Object.keys(resumen)
    .sort(function (a, b) {
      return resumen[b].n - resumen[a].n || a.localeCompare(b);
    })
    .slice(0, CUANTAS);

  var fila = document.createElement("div");
  fila.className = "ap-fichas-barra__fila";

  var conteo = document.createElement("p");
  conteo.className = "ap-fichas-barra__conteo";
  conteo.setAttribute("data-conteo-filtro", "");
  conteo.setAttribute("role", "status");
  conteo.setAttribute("aria-live", "polite");
  fila.appendChild(conteo);

  var botonLimpiar = document.createElement("button");
  botonLimpiar.type = "button";
  botonLimpiar.className = "ap-fichas-barra__limpiar";
  botonLimpiar.setAttribute("data-limpiar-filtro", "");
  botonLimpiar.textContent = "Limpiar";
  botonLimpiar.hidden = true;
  fila.appendChild(botonLimpiar);

  var chips = document.createElement("div");
  chips.className = "ap-fichas-barra__chips";

  var rotulo = document.createElement("span");
  rotulo.className = "ap-fichas-barra__rotulo";
  rotulo.textContent = "Filtrar por";
  chips.appendChild(rotulo);

  claves.forEach(function (clave) {
    var boton = document.createElement("button");
    boton.type = "button";
    boton.className = "tag ap-ficha-etiqueta";
    boton.setAttribute("data-tag", clave);
    boton.setAttribute("aria-pressed", "false");
    boton.appendChild(document.createTextNode(resumen[clave].texto));

    var numero = document.createElement("span");
    numero.className = "ap-ficha-etiqueta__n";
    numero.textContent = resumen[clave].n;
    boton.appendChild(numero);

    chips.appendChild(boton);
  });

  var nota = document.createElement("span");
  nota.className = "ap-fichas-barra__nota";
  var sobrantes = Object.keys(resumen).length - claves.length;
  nota.textContent = sobrantes
    ? "y " +
      sobrantes +
      " etiqueta" +
      (sobrantes === 1 ? "" : "s") +
      " más en las fichas."
    : "También puedes filtrar desde las etiquetas de cada ficha.";
  chips.appendChild(nota);

  sitio.appendChild(fila);
  sitio.appendChild(chips);

  /* --- Filtrar ----------------------------------------------------------- */

  // Las de la barra y las de las fichas se sirven del mismo código: por eso
  // llevan la misma clase .tag y el mismo data-tag.
  var etiquetas = Array.prototype.slice.call(document.querySelectorAll(".tag"));
  var ultimaEtiqueta = null;

  function etiquetasDe(tarjeta) {
    return Array.prototype.map.call(tarjeta.querySelectorAll(".tag"), etiquetaDe);
  }

  function pintarConteo(visibles) {
    var total = tarjetas.length;
    conteo.textContent =
      visibles === total
        ? total + (total === 1 ? " ficha" : " fichas")
        : "Mostrando " + visibles + " de " + total + " fichas";
  }

  // Si la primera ficha que queda está más abajo de la pantalla, se sube hasta
  // ella. Sin esto, filtrar por una etiqueta rara desde arriba deja una
  // pantalla de fichas que ya no corresponden y nadie ve que cambió algo.
  function mirarPrimera(primera) {
    if (!primera) {
      return;
    }
    var caja = primera.getBoundingClientRect();
    if (caja.top < window.innerHeight) {
      return;
    }
    var masthead = document.querySelector(".masthead");
    var altoEncabezado = masthead ? masthead.offsetHeight : 0;
    var y =
      window.scrollY +
      caja.top -
      altoEncabezado -
      sitio.offsetHeight -
      16;
    window.scrollTo({
      top: Math.max(0, y),
      behavior: sinMovimiento() ? "auto" : "smooth"
    });
  }

  function limpiar() {
    tarjetas.forEach(function (t) {
      t.hidden = false;
    });
    etiquetas.forEach(function (el) {
      el.classList.remove("activo");
      el.setAttribute("aria-pressed", "false");
    });
    botonLimpiar.hidden = true;
    pintarConteo(tarjetas.length);
    if (ultimaEtiqueta && ultimaEtiqueta.isConnected) {
      ultimaEtiqueta.focus();
    }
  }

  function filtrar(tag, texto, origen) {
    var activo = normalizar(tag);
    var visibles = 0;
    var primera = null;

    tarjetas.forEach(function (t) {
      var coincide = etiquetasDe(t).indexOf(activo) !== -1;
      t.hidden = !coincide;
      if (coincide) {
        visibles += 1;
        if (!primera) {
          primera = t;
        }
      }
    });

    etiquetas.forEach(function (el) {
      var marcada = etiquetaDe(el) === activo;
      el.classList.toggle("activo", marcada);
      el.setAttribute("aria-pressed", marcada ? "true" : "false");
    });

    botonLimpiar.hidden = visibles === tarjetas.length;
    ultimaEtiqueta = origen;
    pintarConteo(visibles);
    mirarPrimera(primera);
  }

  etiquetas.forEach(function (el) {
    // Las de la barra son <button> de verdad: el navegador ya les da el
    // teclado, el papel y el foco. Las de las fichas son <a> sin href, y ahí
    // sí hay que ponerlo todo a mano para que sirvan con teclado.
    var esBoton = el.tagName === "BUTTON";
    if (!esBoton) {
      el.setAttribute("tabindex", "0");
      el.setAttribute("role", "button");
    }
    el.setAttribute("aria-pressed", "false");

    function activar(evento) {
      evento.preventDefault();
      if (el.classList.contains("activo")) {
        limpiar();
      } else {
        filtrar(
          el.getAttribute("data-tag") || el.textContent,
          el.textContent,
          el
        );
      }
    }

    el.addEventListener("click", activar);
    if (!esBoton) {
      el.addEventListener("keydown", function (evento) {
        if (
          evento.key === "Enter" ||
          evento.key === " " ||
          evento.key === "Spacebar"
        ) {
          activar(evento);
        }
      });
    }
  });

  botonLimpiar.addEventListener("click", limpiar);

  pintarConteo(tarjetas.length);
})();
