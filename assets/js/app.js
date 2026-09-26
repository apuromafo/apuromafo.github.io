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
      var id = enlace.getAttribute("href").slice(1);
      if (!id) {
        return;
      }
      var destino = document.getElementById(id);
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
        history.replaceState(null, "", "#" + id);
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
      ["buscador", busqueda]
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
