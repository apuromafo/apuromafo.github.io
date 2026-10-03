/* ===========================================================================
   Apuromafo — interacciones del sitio
   ===========================================================================
   Script clásico, sin módulos, para que funcione tal cual en GitHub Pages.

   Todo es mejora progresiva: si algo no está en la página, no pasa nada; si el
   visitante pidió menos movimiento, no se mueve nada; y sin JavaScript el
   contenido se lee completo. Nada de esto es necesario para entender el
   sitio, solo para que se sienta mejor.

   Marcas que se leen desde el HTML:

     data-reveal         aparece al entrar en pantalla
     data-reveal-group   sus hijos directos entran en cascada
     data-magnetic       el elemento se acerca suavemente al cursor
     data-spotlight      el resplandor del puntero lo sigue por dentro
     data-progress       barra de progreso de lectura
     data-back-top       botón para volver arriba
     data-rotator        texto que se va turnando solo
     data-rotator-item   una de las partes del texto que rota
     data-rotator-punto  botón para elegir a mano qué parte se ve
     data-buscador       campo de búsqueda de una lista
     data-buscador-lista lista que se filtra
   =========================================================================== */

(function () {
  "use strict";

  var RAIZ = document.documentElement;
  var consultaMovimiento = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : { matches: false };

  function conMovimiento() {
    return !consultaMovimiento.matches;
  }

  function punteroFino() {
    return (
      window.matchMedia &&
      window.matchMedia("(hover: hover) and (pointer: fine)").matches
    );
  }

  /* El href de un ancla y el id de su destino no siempre están escritos de la
     misma manera. Hoy el include toc.html del tema los escribe tal cual (con la
     tilde puesta), pero el mismo fragmento se ve percent-encoded en a.href y
     en la barra de direcciones, y el tema podría cambiarlo en cualquier
     momento. Se prueba primero lo decodificado y, si no aparece nada, lo crudo:
     así el mismo código sirve para las dos formas. Un href raro (un % suelto,
     por ejemplo) no debe romper nada, y si no encuentra destino devuelve null
     para que el llamador siga su camino como hasta ahora. */
  function porId(href) {
    var crudo = String(href || "").replace(/^#/, "");
    if (!crudo) {
      return null;
    }
    var destino = null;
    try {
      destino = document.getElementById(decodeURIComponent(crudo));
    } catch (error) {
      // decodeURIComponent tira con lo que no es una secuencia válida; el
      // intento con el texto tal cual, de abajo, es el plan B.
    }
    return destino || document.getElementById(crudo);
  }

  /* ------------------------------------------------------------------------
   * 1. Revelado al entrar en pantalla
   * ---------------------------------------------------------------------- */
  function revelado() {
    var pendientes = Array.prototype.slice.call(
      document.querySelectorAll("[data-reveal]")
    );
    if (!pendientes.length) {
      return;
    }

    function mostrar(el) {
      el.classList.add("es-visible");
      var i = pendientes.indexOf(el);
      if (i !== -1) {
        pendientes.splice(i, 1);
      }
    }

    function mostrarTodo() {
      pendientes.slice().forEach(mostrar);
    }

    // Sin movimiento (o sin scroll) se enseña todo de una.
    if (!conMovimiento()) {
      mostrarTodo();
      return;
    }

    // Cascada: los hijos de un grupo entran uno detrás de otro.
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-reveal-group]"),
      function (grupo) {
        Array.prototype.forEach.call(grupo.children, function (hijo, i) {
          if (hijo.hasAttribute("data-reveal")) {
            hijo.style.setProperty("--ap-reveal-delay", i * 70 + "ms");
          }
        });
      }
    );

    // Se decide por geometría y no con IntersectionObserver a propósito: es lo
    // mismo de barato para treinta elementos, y no depende de que el navegador
    // avise bien. Lo importante es que ningún elemento se quede invisible para
    // siempre si algo raro pasa con el observador.
    function revisar() {
      var alto = window.innerHeight;
      for (var i = pendientes.length - 1; i >= 0; i--) {
        var caja = pendientes[i].getBoundingClientRect();
        if (caja.bottom <= 0) {
          // Ya quedó arriba: al volver a mirarlo tiene que estar ahí, no
          // aparecer de la nada. También cubre entrar por un ancla o con la
          // página restaurada a media lectura.
          mostrar(pendientes[i]);
        } else if (caja.top < alto * 0.94) {
          mostrar(pendientes[i]);
        }
      }
    }

    var pedido = false;
    function alMover() {
      if (pedido) {
        return;
      }
      pedido = true;
      window.requestAnimationFrame(function () {
        pedido = false;
        revisar();
      });
    }

    window.addEventListener("scroll", alMover, { passive: true });
    window.addEventListener("resize", alMover, { passive: true });

    // Si algo quedó enfocado (por ejemplo, navegación con Tab), se muestra.
    document.addEventListener("focusin", function (evento) {
      var el = evento.target.closest && evento.target.closest("[data-reveal]");
      if (el) {
        mostrar(el);
      }
    });

    // Si en medio de la lectura se pide menos movimiento, se enseña todo.
    if (consultaMovimiento.addEventListener) {
      consultaMovimiento.addEventListener("change", function () {
        if (consultaMovimiento.matches) {
          mostrarTodo();
        }
      });
    }

    revisar();
  }

  /* ------------------------------------------------------------------------
   * 2. Botones magnéticos
   * ---------------------------------------------------------------------- */
  function magneticos() {
    if (!conMovimiento() || !punteroFino()) {
      return;
    }

    Array.prototype.forEach.call(
      document.querySelectorAll("[data-magnetic]"),
      function (el) {
        var limite = parseFloat(el.getAttribute("data-magnetic")) || 6;

        el.addEventListener("pointermove", function (evento) {
          var caja = el.getBoundingClientRect();
          el.style.setProperty(
            "--ap-mx",
            (((evento.clientX - caja.left - caja.width / 2) * limite) / 100
            ).toFixed(2) + "px"
          );
          el.style.setProperty(
            "--ap-my",
            (((evento.clientY - caja.top - caja.height / 2) * limite) / 100
            ).toFixed(2) + "px"
          );
        });

        function soltar() {
          el.style.setProperty("--ap-mx", "0px");
          el.style.setProperty("--ap-my", "0px");
        }

        el.addEventListener("pointerleave", soltar);
        el.addEventListener("blur", soltar);
      }
    );
  }

  /* ------------------------------------------------------------------------
   * 3. Resplandor que sigue al puntero
   * ---------------------------------------------------------------------- */
  function destellos() {
    if (!conMovimiento() || !punteroFino()) {
      return;
    }

    Array.prototype.forEach.call(
      document.querySelectorAll("[data-spotlight]"),
      function (el) {
        el.addEventListener("pointermove", function (evento) {
          var caja = el.getBoundingClientRect();
          el.style.setProperty("--ap-x", evento.clientX - caja.left + "px");
          el.style.setProperty("--ap-y", evento.clientY - caja.top + "px");
        });
      }
    );
  }

  /* ------------------------------------------------------------------------
   * 4. Barra de progreso de lectura
   * ---------------------------------------------------------------------- */
  function progreso() {
    var barra = document.querySelector("[data-progress]");
    if (!barra) {
      return;
    }

    function pintar() {
      var alto = document.documentElement.scrollHeight - window.innerHeight;
      var avance = alto > 0 ? window.scrollY / alto : 0;
      barra.style.setProperty(
        "--ap-avance",
        Math.max(0, Math.min(1, avance)).toFixed(4)
      );
    }

    window.addEventListener("scroll", pintar, { passive: true });
    window.addEventListener("resize", pintar);
    pintar();
  }

  /* ------------------------------------------------------------------------
   * 5. Estado del encabezado al bajar
   * ---------------------------------------------------------------------- */
  function encabezado() {
    var barra = document.querySelector("[data-header]") ||
      document.querySelector(".masthead");
    if (!barra) {
      return;
    }

    // La barra de filtros y el riel de las páginas de sección se pegan con
    // top: var(--ap-alto-masthead). Ese alto no es el que dice el CSS: el
    // encabezado suma el relleno y el borde sobre el nav, y da 103 px, no 68.
    // Por eso se mide de verdad y se escribe en el token. Si no, al bajar, la
    // barra de filtros se esconde debajo del encabezado.
    //
    // No basta con medir al arrancar: en el tema oscuro la hoja se cambia
    // desde un script, y hasta que main-dark.css carga el encabezado sale
    // sin estilos y mide el triple. Por eso se escucha con ResizeObserver,
    // que también cubre el cambio de fuente, el menú del teléfono y el zoom.
    var ultimoAlto = 0;

    function medir() {
      var alto = Math.round(barra.getBoundingClientRect().height);
      if (alto > 0 && alto !== ultimoAlto) {
        ultimoAlto = alto;
        document.documentElement.style.setProperty(
          "--ap-alto-masthead",
          alto + "px"
        );
      }
    }

    if (window.ResizeObserver) {
      new window.ResizeObserver(medir).observe(barra);
    }
    window.addEventListener("load", medir);

    function marcar() {
      barra.classList.toggle("ap-desplazado", window.scrollY > 24);
    }

    window.addEventListener("scroll", marcar, { passive: true });
    window.addEventListener("resize", function () {
      ultimoAlto = 0;
      medir();
      marcar();
    });
    medir();
    marcar();
  }

  /* ------------------------------------------------------------------------
   * 6. Volver arriba
   * ---------------------------------------------------------------------- */
  function volverArriba() {
    var boton = document.querySelector("[data-back-top]");
    if (!boton) {
      return;
    }

    boton.addEventListener("click", function () {
      window.scrollTo({
        top: 0,
        behavior: conMovimiento() ? "smooth" : "auto"
      });
      // El foco vuelve arriba también: si no, el siguiente Tab seguiría
      // escuchando desde el final de la página.
      var foco = document.querySelector(".site-title") ||
        document.querySelector("main");
      if (foco) {
        foco.setAttribute("tabindex", "-1");
        foco.focus({ preventScroll: true });
      }
    });

    function mostrar() {
      boton.classList.toggle(
        "es-visible",
        window.scrollY > window.innerHeight * 0.8
      );
    }

    window.addEventListener("scroll", mostrar, { passive: true });
    mostrar();
  }

  /* ------------------------------------------------------------------------
   * 7. Texto que se va turnando
   * ---------------------------------------------------------------------- */
  function rotador() {
    var contenedor = document.querySelector("[data-rotator]");
    if (!contenedor) {
      return;
    }

    var textos = Array.prototype.slice.call(
      contenedor.querySelectorAll("[data-rotator-item]")
    );
    if (textos.length < 2) {
      return;
    }

    var puntos = contenedor.parentElement
      ? Array.prototype.slice.call(
          contenedor.parentElement.querySelectorAll("[data-rotator-punto]")
        )
      : [];
    var actual = 0;
    var temporizador = null;
    var PAUSA = 4200;

    function mostrar(indice) {
      actual = (indice + textos.length) % textos.length;
      textos.forEach(function (t, i) {
        var activa = i === actual;
        t.classList.toggle("es-activo", activa);
        t.setAttribute("aria-hidden", activa ? "false" : "true");
      });
      puntos.forEach(function (p, i) {
        p.classList.toggle("es-activo", i === actual);
      });
    }

    function parar() {
      if (temporizador) {
        window.clearInterval(temporizador);
        temporizador = null;
      }
    }

    function arrancar() {
      if (temporizador || !conMovimiento()) {
        return;
      }
      temporizador = window.setInterval(function () {
        mostrar(actual + 1);
      }, PAUSA);
    }

    puntos.forEach(function (punto, i) {
      punto.addEventListener("click", function () {
        mostrar(i);
        parar();
        arrancar();
      });
    });

    // Al pasar el puntero o al entrar el foco, se detiene: quien está
    // leyendo ese texto no quiere que se le cambie debajo.
    contenedor.addEventListener("pointerenter", parar);
    contenedor.addEventListener("pointerleave", arrancar);
    contenedor.addEventListener("focusin", parar);
    contenedor.addEventListener("focusout", arrancar);

    mostrar(0);
    arrancar();
  }

  /* ------------------------------------------------------------------------
   * 8. Anclas internas con desplazamiento suave
   * ---------------------------------------------------------------------- */
  function anclas() {
    document.addEventListener("click", function (evento) {
      var enlace = evento.target.closest &&
        evento.target.closest('a[href^="#"]');
      if (!enlace) {
        return;
      }
      // El href se copia tal cual: porId descodifica para buscar, pero la URL
      // que ve la gente se deja escrita como estaba en el atributo.
      var href = enlace.getAttribute("href");
      var destino = porId(href);
      if (!destino) {
        return;
      }

      evento.preventDefault();
      destino.scrollIntoView({
        behavior: conMovimiento() ? "smooth" : "auto",
        block: "start"
      });
      destino.setAttribute("tabindex", "-1");
      destino.focus({ preventScroll: true });
      if (history.replaceState) {
        history.replaceState(null, "", href);
      }
    });
  }

  /* ------------------------------------------------------------------------
   * 9. Buscador de listas (el índice de proyectos)
   * ---------------------------------------------------------------------- */
  function busqueda() {
    var campos = Array.prototype.slice.call(
      document.querySelectorAll("[data-buscador]")
    );
    if (!campos.length) {
      return;
    }

    campos.forEach(function (campo) {
      var lista = document.getElementById(
        campo.getAttribute("data-buscador")
      );
      if (!lista) {
        return;
      }

      var entrada = campo.querySelector("input");
      var vacio = document.getElementById(
        campo.getAttribute("data-buscador") + "-vacio"
      );
      var conteo = document.querySelector("[data-conteo-buscador]");
      if (!entrada) {
        return;
      }

      // El botón de borrar puede estar dentro del campo o fuera (en el aviso
      // de "no hay resultados"), así que se buscan en toda la página.
      var limpiadores = Array.prototype.slice.call(
        document.querySelectorAll("[data-buscador-limpiar]")
      );

      function vaciar() {
        entrada.value = "";
        filtrar();
        entrada.focus();
      }
      limpiadores.forEach(function (b) {
        b.addEventListener("click", vaciar);
      });

      // Cada elemento de la lista son uno o varios hijos consecutivos; se
      // agrupan para que al ocultar uno se oculte su descripción.
      var grupos = [];
      Array.prototype.forEach.call(lista.children, function (hijo) {
        var ultimo = grupos[grupos.length - 1];
        var esTitulo = /^H[1-6]$/.test(hijo.tagName);
        if (esTitulo || !ultimo) {
          grupos.push({ titulo: hijo, cuerpo: [] });
        } else {
          ultimo.cuerpo.push(hijo);
        }
      });

      function normalizar(texto) {
        return String(texto || "")
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "");
      }

      function filtrar() {
        var termino = normalizar(entrada.value).trim();
        var found = 0;
        var propio = campo.querySelector("[data-buscador-limpiar]");

        grupos.forEach(function (grupo) {
          var texto = normalizar(grupo.titulo.textContent);
          grupo.cuerpo.forEach(function (parte) {
            texto += " " + normalizar(parte.textContent);
          });
          var coincide = !termino || texto.indexOf(termino) !== -1;
          grupo.titulo.hidden = !coincide;
          grupo.cuerpo.forEach(function (parte) {
            parte.hidden = !coincide;
          });
          if (coincide) {
            found += 1;
          }
        });

        if (vacio) {
          vacio.hidden = found !== 0;
        }
        if (propio) {
          propio.hidden = termino === "";
        }
        if (conteo) {
          conteo.textContent =
            termino === ""
              ? grupos.length + " proyectos"
              : found === 1
              ? "1 proyecto coincide"
              : found + " proyectos coinciden";
        }
      }

      var esperando;
      entrada.addEventListener("input", function () {
        window.clearTimeout(esperando);
        esperando = window.setTimeout(filtrar, 90);
      });
      entrada.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape" && entrada.value) {
          evento.preventDefault();
          vaciar();
        }
      });

      // "/" lleva al campo, como en la mayoría de herramientas.
      document.addEventListener("keydown", function (evento) {
        if (
          evento.key === "/" &&
          !/^(INPUT|TEXTAREA|SELECT)$/.test(evento.target.tagName) &&
          !evento.metaKey &&
          !evento.ctrlKey &&
          !evento.altKey
        ) {
          evento.preventDefault();
          entrada.focus();
          entrada.select();
        }
      });

      filtrar();
    });
  }

  /* ------------------------------------------------------------------------
   * 10. Índice del riel: marcar la sección que se está leyendo
   * ---------------------------------------------------------------------- */
  function indiceRiel() {
    var menu = document.querySelector(".ap-toc__menu");
    if (!menu) {
      return;
    }

    var secciones = [];
    Array.prototype.forEach.call(
      menu.querySelectorAll('a[href^="#"]'),
      function (enlace) {
        var destino = porId(enlace.getAttribute("href"));
        // Una entrada que no apunta a ningún título se deja como está: la
        // escribió el tema y, sin este módulo, el índice se ve igual.
        if (destino) {
          secciones.push({ enlace: enlace, destino: destino });
        }
      }
    );
    if (!secciones.length) {
      return;
    }

    var activa = null;

    function marcar(indice) {
      if (indice === activa) {
        return;
      }
      activa = indice;
      secciones.forEach(function (seccion, i) {
        var esActiva = i === indice;
        seccion.enlace.classList.toggle("es-activo", esActiva);
        // aria-current le dice a quien navega con lector de pantalla cuál de
        // estas secciones es la que se está leyendo ahora.
        if (esActiva) {
          seccion.enlace.setAttribute("aria-current", "true");
        } else {
          seccion.enlace.removeAttribute("aria-current");
        }
      });
    }

    // La línea de referencia es la misma que usa el salto de ancla: el
    // scroll-padding-top del html, que sale de --ap-alto-masthead y que app.js
    // reescribe con el alto real del encabezado. Si acá se inventara un número,
    // el título que queda marcado y el título al que salta el clic terminarían
    // en dos filas distintas.
    function linea() {
      var relleno = parseFloat(
        window.getComputedStyle(RAIZ).scrollPaddingTop
      );
      return isNaN(relleno) || relleno <= 0 ? 0 : relleno;
    }

    function revisar() {
      var ref = linea();
      var indice = -1;
      for (var i = 0; i < secciones.length; i++) {
        if (secciones[i].destino.getBoundingClientRect().top <= ref + 1) {
          indice = i;
        }
      }

      // Abajo del todo manda la última, aunque su título siga por debajo de la
      // línea: la página no da para más, y quedarse en la anterior daría la
      // sensación de que al índice le falta la última entrada.
      var hasta = RAIZ.scrollHeight - window.innerHeight;
      if (hasta > 0 && hasta - window.scrollY <= 2) {
        indice = secciones.length - 1;
      }

      // Arriba del todo no se marca nada, y no hace falta ninguna regla
      // especial: el encabezado de la página ocupa más que la línea, así que el
      // primer título todavía está por debajo y nadie quedó leído.
      marcar(indice);
    }

    var pedido = false;
    function alMover() {
      if (pedido) {
        return;
      }
      pedido = true;
      window.requestAnimationFrame(function () {
        pedido = false;
        revisar();
      });
    }

    window.addEventListener("scroll", alMover, { passive: true });
    window.addEventListener("resize", alMover, { passive: true });
    // Las fuentes del tema llegan después y mueven todo: se vuelve a medir.
    window.addEventListener("load", alMover, { passive: true });

    // Al hacer clic se marca el destino de entrada, sin esperar a que termine
    // el desplazamiento. Después manda la geometría, que va corrigiendo durante
    // el viaje y deja el marcador donde corresponde. Congelarlo hasta que
    // pare el scroll pediría un temporizador que se desincroniza en cuanto el
    // visitante scrollea con la rueda en el medio, y ahí el marcador queda
    // mintiendo.
    //
    // La marca dura poco y está bien que dure poco: en cuanto la página se
    // mueve, la geometría dice que todavía no se ha leído nada (el título de la
    // sección sigue por debajo de la línea) y la quita. Eso no es un fallo del
    // clic: es el indicador diciendo la verdad sobre dónde está el visitante.
    menu.addEventListener("click", function (evento) {
      var enlace = evento.target.closest &&
        evento.target.closest('a[href^="#"]');
      if (!enlace) {
        return;
      }
      for (var i = 0; i < secciones.length; i++) {
        if (secciones[i].enlace === enlace) {
          marcar(i);
          return;
        }
      }
    });

    revisar();
  }

  /* ------------------------------------------------------------------------
   * Arranque
   * ---------------------------------------------------------------------- */
  function iniciar() {
    RAIZ.classList.add("ap-js");

    // Cada módulo va por su cuenta: si uno falla (porque en esta página falte
    // algo, o porque un navegador se ponga raro), el resto sigue funcionando.
    // Esto solo son adornos; el contenido ya se leyó entero.
    [
      ["revelado", revelado],
      ["botones magnéticos", magneticos],
      ["resplandor", destellos],
      ["progreso de lectura", progreso],
      ["encabezado", encabezado],
      ["volver arriba", volverArriba],
      ["texto rotativo", rotador],
      ["anchas", anclas],
      ["buscador", busqueda],
      ["índice del riel", indiceRiel]
    ].forEach(function (par) {
      try {
        par[1]();
      } catch (error) {
        if (window.console && console.warn) {
          console.warn("Apuromafo: falló " + par[0], error);
        }
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
