document.addEventListener("DOMContentLoaded", function () {
  var CLARO = "claro";
  var OSCURO = "oscuro";
  var hoja = document.querySelector('link[rel="stylesheet"][href*="/assets/css/main"]');

  function hrefPara(modo) {
    if (!hoja) {
      return null;
    }
    var base = hoja.getAttribute("href").split("?")[0];
    if (modo === OSCURO) {
      return base.replace(/main(-dark)?\.css$/, "main-dark.css");
    }
    return base.replace(/main(-dark)?\.css$/, "main.css");
  }

  function aplicar(modo, boton) {
    var destino = hrefPara(modo);
    if (hoja && destino) {
      hoja.setAttribute("href", destino);
    }
    try {
      localStorage.setItem("tema", modo);
    } catch (e) {}
    if (boton) {
      boton.textContent = modo === OSCURO ? "☀ Claro" : "☾ Oscuro";
      boton.setAttribute(
        "aria-label",
        modo === OSCURO ? "Cambiar a tema claro" : "Cambiar a tema oscuro"
      );
    }
  }

  function inicial() {
    var guardado = null;
    try {
      guardado = localStorage.getItem("tema");
    } catch (e) {}
    if (guardado === OSCURO || guardado === CLARO) {
      return guardado;
    }
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      return OSCURO;
    }
    return CLARO;
  }

  var boton = document.createElement("button");
  boton.type = "button";
  boton.className = "theme-toggle";
  boton.addEventListener("click", function () {
    var actual = null;
    try {
      actual = localStorage.getItem("tema");
    } catch (e) {}
    if (!actual && hoja && /main-dark\.css$/.test(hoja.getAttribute("href"))) {
      actual = OSCURO;
    }
    aplicar(actual === OSCURO ? CLARO : OSCURO, boton);
  });

  var nav = document.querySelector(".greedy-nav .visible-links");
  if (nav) {
    var item = document.createElement("li");
    item.className = "masthead__menu-item";
    item.appendChild(boton);
    nav.appendChild(item);
  }

  aplicar(inicial(), boton);
});
