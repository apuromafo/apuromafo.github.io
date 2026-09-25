document.addEventListener("DOMContentLoaded", function () {
  var normalizar = function (texto) {
    return texto
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "");
  };

  var tarjetas = Array.prototype.slice.call(document.querySelectorAll(".card"));
  var indicador = document.getElementById("filtro-activo");
  var nombreFiltro = document.getElementById("filtro-nombre");
  var botonLimpiar = document.getElementById("limpiar-filtro");

  function etiquetasDe(tarjeta) {
    return Array.prototype.map.call(
      tarjeta.querySelectorAll(".tag"),
      function (el) {
        return normalizar(el.getAttribute("data-tag") || el.textContent);
      }
    );
  }

  function limpiar() {
    tarjetas.forEach(function (t) {
      t.hidden = false;
    });
    Array.prototype.forEach.call(
      document.querySelectorAll(".tag.activo"),
      function (el) {
        el.classList.remove("activo");
      }
    );
    if (indicador) {
      indicador.hidden = true;
    }
  }

  function filtrar(tag, etiqueta) {
    var activo = normalizar(tag);
    tarjetas.forEach(function (t) {
      t.hidden = etiquetasDe(t).indexOf(activo) === -1;
    });
    Array.prototype.forEach.call(
      document.querySelectorAll(".tag"),
      function (el) {
        el.classList.toggle(
          "activo",
          normalizar(el.getAttribute("data-tag") || el.textContent) === activo
        );
      }
    );
    if (indicador && nombreFiltro) {
      nombreFiltro.textContent = etiqueta;
      indicador.hidden = false;
    }
  }

  Array.prototype.forEach.call(
    document.querySelectorAll(".tag"),
    function (el) {
      el.setAttribute("tabindex", "0");
      el.setAttribute("role", "button");
      const activar = function (evento) {
        evento.preventDefault();
        if (el.classList.contains("activo")) {
          limpiar();
        } else {
          filtrar(el.getAttribute("data-tag") || el.textContent, el.textContent);
        }
      };
      el.addEventListener("click", activar);
      el.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" || evento.key === " ") {
          activar(evento);
        }
      });
    }
  );

  if (botonLimpiar) {
    botonLimpiar.addEventListener("click", limpiar);
  }
});
