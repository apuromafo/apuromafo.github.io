---
layout: ap-seccion
title: Licencias y créditos
permalink: /licencias/
antetitulo: De dónde sale lo que hay aquí
icono: book
bajada: >-
  Las tipografías, los iconos y el tema que usa este sitio, con su licencia y
  de dónde viene cada cosa. Nada se pide a un servidor de terceros.
cifras:
  - valor: "2"
    etiqueta: tipografías, alojadas aquí
  - valor: "27"
    etiqueta: iconos dibujados en el sitio
  - valor: "1"
    etiqueta: tema, Minimal Mistakes 4.26.2
autor: true
toc: true
---

## Tipografías

Las dos están alojadas en este sitio, dentro de `assets/fonts/`. Son los
archivos que publica cada proyecto, recortados al latín y sin modificar: en la
tabla de nombres de cada `.woff2` está el origen.

| Tipografía | Versión | Peso | Autoría |
|---|---|---|---|
| Inter | 4.001 | variable, 100 a 900 | The Inter Project Authors |
| Space Grotesk | 2.000 | variable, 300 a 700 | The Space Grotesk Project Authors |

Las dos van bajo la **SIL Open Font License 1.1**. Inter también se publica
con Apache 2.0 como alternativa, pero aquí va la versión OFL, que es la que
declara el archivo. El texto completo de la licencia está en
[assets/fonts/LICENCIAS.md](https://github.com/apuromafo/apuromafo.github.io/blob/main/assets/fonts/LICENCIAS.md).

## Iconos

Los trazados salen de **Font Awesome Free 6**, con licencia
[CC BY 4.0](https://fontawesome.com/license/free) y copyright de Fonticons, Inc.

El sitio dibuja 27 iconos y no carga la CDN de Font Awesome ni ninguna otra
fuente de iconos:

- 22 van en línea como SVG en el contenido, desde `_data/apuromafo_iconos.yml`.
- 5 los escribe el tema con nombres de Font Awesome 5 y están redibujados como
  máscaras CSS en `assets/css/iconos-tema.css`, para que hereden el color del
  texto y funcionen en claro y en oscuro.

Los dos archivos los genera `utilidades/generar_iconos.py`, que anota de dónde
saca cada trazado y los puede rehacer si se actualiza el tema.

## Tema

[Minimal Mistakes](https://github.com/mmistakes/minimal-mistakes) 4.26.2, de
Michael Rose, con licencia
[MIT](https://github.com/mmistakes/minimal-mistakes/blob/master/LICENSE). Se usa
como tema remoto de Jekyll.

Del tema solo está cambiado `_includes/head.html`, que es una copia con tres
cambios: decidir el tema claro u oscuro antes de pintar, quitar la fuente de
iconos de jsDelivr y cargar primero las tipografías locales. El resto es el
tema tal cual.

El diseño del sitio (colores, tipografía, portada, fichas, barra de filtros)
vive aparte, en `assets/css/apuromafo.css` y `assets/js/`, y se encha desde
`_includes/head/custom.html`. Si algún día se quisiera deshacer, se borran dos
enlaces de ese archivo y el sitio vuelve a lo que traía el tema.

## Cómo se construye

- [Jekyll](https://jekyllrb.com), licencia MIT, con `jekyll-remote-theme`,
  `jekyll-feed`, `jekyll-sitemap` y `jekyll-include-cache`. Lo publica
  GitHub Pages.
- Python 3 para `utilidades/generar_iconos.py`, solo con la biblioteca estándar.
- [fontTools](https://github.com/fonttools/fonttools), licencia MIT, para leer la
  tabla de nombres de los `.woff2` y dejar la licencia de las tipografías
  anotada con datos y no de memoria.
- La capa de diseño es CSS y JavaScript escritos a mano, sin compilar: los
  archivos del repositorio son los que llegan al navegador.

## Contenido

Los textos, las fichas y las descripciones de los proyectos de este sitio son
de [apuromafo](https://github.com/apuromafo). El sitio **no declara licencia de
contenido**, así que no se puede reutilizar sin pedir permiso.

El código de los proyectos está en los repositorios de GitHub, donde cada uno
declara lo suyo. Para cualquier consulta, el
[Telegram](https://t.me/Apuromafo) o el
[LinkedIn](https://linkedin.com/in/mfaundez).
