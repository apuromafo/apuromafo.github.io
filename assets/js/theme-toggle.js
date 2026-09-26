/* ===========================================================================
   Apuromafo — botón de tema claro/oscuro
   ===========================================================================
   El tema ya quedó decidido en _includes/head.html antes de pintar, así que
   aquí no hay nada que adivinar: el atributo data-tema en <html> es la
   fuente de la verdad.

   El botón se arma en el momento y toma sus iconos de la plantilla que dejó
   la página, así que no hay datos duplicados en JavaScript. Qué icono y qué
   texto se ven los decide el CSS según data-tema; a este script solo le toca
   conectarlo al clic y al cambio de hoja del tema.

   El atributo data-tema manda para la hoja de diseño; el href de main.css ↔
   main-dark.css se cambia para que los colores base del tema acompañen. Las
   dos cosas siempre dicen lo mismo.
   =========================================================================== */

(function () {
  "use strict";

  var RAIZ = document.documentElement;
  var CLARO = "claro";
  var OSCURO = "oscuro";
  var COLOR_NAVEGADOR = { claro: "#f6f8fa", oscuro: "#0a0e14" };
  var PLANTILLA = "[data-plantilla-tema]";

  function hoja() {
    return document.querySelector('link[rel="stylesheet"][href*="/assets/css/main"]');
  }

  function modoActual() {
    return RAIZ.getAttribute("data-tema") === OSCURO ? OSCURO : CLARO;
  }

  function aplicar(modo) {
    RAIZ.setAttribute("data-tema", modo);

    var base = hoja();
    if (base) {
      var actual = base.getAttribute("href").split("?")[0];
      var destino = actual.replace(
        /main(-dark)?\.css$/,
        modo === OSCURO ? "main-dark.css" : "main.css"
      );
      if (destino !== actual) {
        base.setAttribute("href", destino);
      }
    }

    try {
      localStorage.setItem("tema", modo);
    } catch (e) {}

    var color = document.getElementById("ap-color-navegador");
    if (color && COLOR_NAVEGADOR[modo]) {
      color.setAttribute("content", COLOR_NAVEGADOR[modo]);
    }

    // Quien quiera (el rótulo del botón) se entera del cambio.
    document.dispatchEvent(
      new CustomEvent("ap:tema", { detail: modo })
    );
  }

  var boton = null;

  function montar() {
    if (boton) return;

    var plantilla = document.querySelector(PLANTILLA);
    if (!plantilla) return;

    boton = document.createElement("button");
    boton.type = "button";
    boton.className = "theme-toggle";
    boton.setAttribute("aria-label", "Cambiar entre tema claro y oscuro");

    var contenido = plantilla.cloneNode(true);
    contenido.removeAttribute("hidden");
    boton.appendChild(contenido);

    boton.addEventListener("click", function () {
      aplicar(modoActual() === OSCURO ? CLARO : OSCURO);
    });

    // El texto dice a qué se cambia ("Oscuro"), como el glifo que lo acompaña.
    // Lo escribe el script porque solo él sabe en qué modo se está.
    function rotular(modo) {
      var texto = boton.querySelector(".theme-toggle__texto");
      if (texto) {
        texto.textContent = modo === OSCURO ? "Claro" : "Oscuro";
      }
    }
    rotular(modoActual());
    document.addEventListener("ap:tema", function (evento) {
      rotular(evento.detail);
    });

    // Se cuelga junto al botón de menú, para que siga visible cuando la
    // barra se achica en pantallas chicas.
    var nav = document.querySelector(".greedy-nav");
    var menu = document.querySelector(".greedy-nav__toggle");
    if (nav && menu && menu.parentNode === nav) {
      var item = document.createElement("li");
      item.className = "masthead__menu-item ap-tema-item";
      item.appendChild(boton);
      nav.insertBefore(item, menu.nextSibling);
    } else if (nav) {
      var solto = document.createElement("div");
      solto.className = "ap-tema-suelto";
      solto.appendChild(boton);
      nav.appendChild(solto);
    }

    var color = document.getElementById("ap-color-navegador");
    if (color) {
      color.setAttribute("content", COLOR_NAVEGADOR[modoActual()]);
    }

    // Si el visitante nunca ha tocado el botón, se acompaña al cambio de
    // preferencia del sistema.
    if (window.matchMedia) {
      var consulta = window.matchMedia("(prefers-color-scheme: dark)");
      var alCambiar = function (evento) {
        var guardado = null;
        try {
          guardado = localStorage.getItem("tema");
        } catch (e) {}
        if (!guardado) {
          aplicar(evento.matches ? OSCURO : CLARO);
        }
      };
      if (consulta.addEventListener) {
        consulta.addEventListener("change", alCambiar);
      } else if (consulta.addListener) {
        consulta.addListener(alCambiar);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", montar);
  } else {
    montar();
  }
})();
