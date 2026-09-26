---
layout: default
title: Inicio
description: >-
  apuromafo: profesor de Matemática, pentester y docente en ciberseguridad
  desde Chile. Proyectos de Red Team, programación y herramientas de seguridad.
---

{%- comment -%}
  Portada. Va en HTML a propósito: así se controla cada detalle del diseño.
  Los números y los textos salen de lo que ya dice el sitio en las páginas de
  Red Team, Sobre mí e Índice; no hay cifras nuevas aquí.

  El id="main" es el destino del enlace "ir al contenido" que pone el tema en
  todas las páginas; sin él, en la portada apuntaría a la nada. La clase
  "page__content" también la espera el tema: su JavaScript da por hecho que
  existe, y si no la encuentra se cae a mitad de camino.
{%- endcomment -%}

<div id="main" role="main" class="page__content ap-portada">

<header class="hero">
  <div class="hero__fondo" aria-hidden="true"></div>
  <div class="ap-ancho">
    <div class="hero__contenido">
      <p class="hero__antetitulo">apuromafo &middot; Chile</p>

      <h1 class="hero__titulo">Ciberseguridad,<br>de la práctica a la clase</h1>

      <p class="hero__roles">
        <span class="hero__rotador" data-rotator>
          <span data-rotator-item>Pentester</span>
          <span data-rotator-item>Docente en ciberseguridad</span>
          <span data-rotator-item>Profesor de matemática</span>
          <span data-rotator-item>Inversor de binarios</span>
        </span>
        <span class="hero__puntos">
          <button class="hero__punto" type="button" data-rotator-punto aria-label="Pentester"></button>
          <button class="hero__punto" type="button" data-rotator-punto aria-label="Docente en ciberseguridad"></button>
          <button class="hero__punto" type="button" data-rotator-punto aria-label="Profesor de matemática"></button>
          <button class="hero__punto" type="button" data-rotator-punto aria-label="Inversor de binarios"></button>
        </span>
      </p>

      <p class="hero__bajada">
        Llevo casi 20 años entre reversing y assembler, y unos 4 haciendo
        pentest. Todo lo que hago queda escrito: herramientas, writeups,
        catálogos y el código de cada proyecto, con licencia abierta.
      </p>

      <div class="hero__acciones">
        <a class="ap-btn ap-btn--primario" data-magnetic href="{{ '/red-team/' | relative_url }}">
          Ver mis proyectos
          {% include apuromafo/icono.html nombre="arrow-right" %}
        </a>
        <a class="ap-btn ap-btn--fantasma" data-magnetic href="{{ '/indice/' | relative_url }}">
          Índice de 73 proyectos
        </a>
      </div>

      <p class="hero__nota">
        {% include apuromafo/icono.html nombre="github" %}
        <a href="https://github.com/apuromafo">github.com/apuromafo</a>
        <span aria-hidden="true">&middot;</span>
        <a href="https://t.me/Apuromafo">Telegram en horario hábil</a>
      </p>
    </div>
  </div>
</header>

<section class="ap-seccion ap-banda-cifras" aria-label="En números">
  <div class="ap-ancho">
    <ul class="cifras" data-reveal-group>
      <li data-reveal>
        <span class="cifra__valor">casi <em>20</em></span>
        <span class="cifra__etiqueta">años de reversing y análisis de binarios</span>
      </li>
      <li data-reveal>
        <span class="cifra__valor"><em>700+</em></span>
        <span class="cifra__etiqueta">máquinas completadas en TryHackMe</span>
      </li>
      <li data-reveal>
        <span class="cifra__valor"><em>283</em></span>
        <span class="cifra__etiqueta">días seguidos de actividad al 25-09-2026</span>
      </li>
      <li data-reveal>
        <span class="cifra__valor"><em>104</em></span>
        <span class="cifra__etiqueta">referencias de ciberseguridad y regulación</span>
      </li>
      <li data-reveal>
        <span class="cifra__valor"><em>73</em></span>
        <span class="cifra__etiqueta">proyectos en el índice del repositorio</span>
      </li>
    </ul>
  </div>
</section>

<section class="ap-seccion" aria-labelledby="titulo-areas">
  <div class="ap-ancho">
    <div class="ap-seccion__cabeza" data-reveal>
      <p class="ap-seccion__etiqueta">Por dónde empezar</p>
      <h2 class="ap-seccion__titulo" id="titulo-areas">Cuatro listas, un solo sitio</h2>
      <p class="ap-seccion__bajada">
        Cada proyecto aparece una vez, con su descripción y sus etiquetas. Se
        filtra haciendo clic en cualquier <code>#etiqueta</code>.
      </p>
    </div>

    <ul class="ap-rejilla" data-reveal-group>
      <li data-reveal>
        <a class="ap-area" data-spotlight href="{{ '/red-team/' | relative_url }}">
          <span class="ap-area__icono">{% include apuromafo/icono.html nombre="shield" %}</span>
          <span class="ap-area__titulo">
            Red Team
            <span class="ap-area__conteo">8 fichas</span>
          </span>
          <span class="ap-area__texto">
            Catálogo de ciberseguridad, CTF, reversing y TryHackMe.
          </span>
          <span class="ap-area__flecha">
            Abrir
            {% include apuromafo/icono.html nombre="chevron-right" %}
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-area" data-spotlight href="{{ '/programacion/' | relative_url }}">
          <span class="ap-area__icono">{% include apuromafo/icono.html nombre="code" %}</span>
          <span class="ap-area__titulo">
            Programación
            <span class="ap-area__conteo">5 fichas</span>
          </span>
          <span class="ap-area__texto">
            Python, Delphi, Bash y C: lo que escribo para resolver algo.
          </span>
          <span class="ap-area__flecha">
            Abrir
            {% include apuromafo/icono.html nombre="chevron-right" %}
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-area" data-spotlight href="{{ '/herramientas/' | relative_url }}">
          <span class="ap-area__icono">{% include apuromafo/icono.html nombre="terminal" %}</span>
          <span class="ap-area__titulo">
            Herramientas
            <span class="ap-area__conteo">33 fichas</span>
          </span>
          <span class="ap-area__texto">
            Utilidades de seguridad del repositorio Python, con su uso.
          </span>
          <span class="ap-area__flecha">
            Abrir
            {% include apuromafo/icono.html nombre="chevron-right" %}
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-area" data-spotlight href="{{ '/indice/' | relative_url }}">
          <span class="ap-area__icono">{% include apuromafo/icono.html nombre="list" %}</span>
          <span class="ap-area__titulo">
            Índice
            <span class="ap-area__conteo">73 proyectos</span>
          </span>
          <span class="ap-area__texto">
            Todos los proyectos con descripción, para buscar por nombre.
          </span>
          <span class="ap-area__flecha">
            Abrir
            {% include apuromafo/icono.html nombre="chevron-right" %}
          </span>
        </a>
      </li>
    </ul>
  </div>
</section>

<section class="ap-seccion ap-seccion--alt" aria-labelledby="titulo-destacado">
  <div class="ap-ancho">
    <div class="ap-seccion__cabeza" data-reveal>
      <p class="ap-seccion__etiqueta">Destacado</p>
      <h2 class="ap-seccion__titulo" id="titulo-destacado">Dos proyectos que resumen el sitio</h2>
    </div>

    <div class="card" markdown="1" data-spotlight data-reveal>

### [Catálogo de ciberseguridad](https://github.com/apuromafo/Repositorio_Python/tree/main/064_Regulaciones)

Reuní 104 referencias de ciberseguridad, privacidad y regulación financiera (Chile, América Latina y banca), con CLI de consulta en Python y corte al 25-09-2026.

<span class="tags"><a class="tag" data-tag="ciberseguridad">#ciberseguridad</a> <a class="tag" data-tag="python">#python</a> <a class="tag" data-tag="chile">#chile</a></span>

</div>

    <div class="card" markdown="1" data-spotlight data-reveal>

### [TryHackMe — Perfil](https://tryhackme.com/p/apuromafo)

Soy jugador activo de TryHackMe, con más de 700 máquinas completadas y 283 días seguidos de actividad al 25-09-2026.

<span class="tags"><a class="tag" data-tag="tryhackme">#tryhackme</a> <a class="tag" data-tag="pentesting">#pentesting</a> <a class="tag" data-tag="red-team">#red-team</a></span>

</div>
  </div>
</section>

<section class="ap-seccion" aria-labelledby="titulo-formacion">
  <div class="ap-ancho">
    <div class="ap-seccion__cabeza" data-reveal>
      <p class="ap-seccion__etiqueta">Formación</p>
      <h2 class="ap-seccion__titulo" id="titulo-formacion">Formación y docencia</h2>
      <p class="ap-seccion__bajada">
        Diplomados y certificaciones. El detalle de más de 100 cursos está en
        mis billeteras de credenciales, todas públicas.
      </p>
    </div>

    <ul class="ap-chips" data-reveal-group>
      <li data-reveal><span class="ap-chip">Diplomado en Red Team — USACH</span></li>
      <li data-reveal><span class="ap-chip">eJPT — Penetration Testing</span></li>
      <li data-reveal><span class="ap-chip">CEHP — Ec-Council</span></li>
      <li data-reveal><span class="ap-chip">Reversing &amp; Exploiting — USACH</span></li>
      <li data-reveal><span class="ap-chip">Implementador Líder ISO 27035</span></li>
    </ul>

    <p class="ap-nota-enlaces" data-reveal>
      {% include apuromafo/icono.html nombre="cap" %}
      Billeteras:
      <a href="https://www.credential.net/profile/michelfandez/wallet">Credential.net</a>,
      <a href="https://certs.ine.com/profile/michelfandez/wallet">INE</a>,
      <a href="https://www.credly.com/users/michel-alejandro-faundez-ortiz/badges">Credly</a>
      &middot;
      <a href="{{ '/sobre-mi/' | relative_url }}">Ver el perfil completo</a>
    </p>
  </div>
</section>

<section class="ap-seccion ap-seccion--alt" aria-labelledby="titulo-contacto">
  <div class="ap-ancho">
    <div class="ap-seccion__cabeza" data-reveal>
      <p class="ap-seccion__etiqueta">Contacto</p>
      <h2 class="ap-seccion__titulo" id="titulo-contacto">Escríbeme o mira lo que hago</h2>
      <p class="ap-seccion__bajada">
        Todo mi trabajo está publicado en GitHub con licencias abiertas según
        cada repositorio. Telegram es el mejor lugar para escribirme.
      </p>
    </div>

    <ul class="ap-contacto" data-reveal-group>
      <li data-reveal>
        <a class="ap-canal" data-spotlight href="https://t.me/Apuromafo">
          <span class="ap-canal__icono">{% include apuromafo/icono.html nombre="telegram" %}</span>
          <span class="ap-canal__texto">
            <span class="ap-canal__nombre">Telegram</span>
            <span class="ap-canal__valor">t.me/Apuromafo</span>
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-canal" data-spotlight href="https://github.com/apuromafo">
          <span class="ap-canal__icono">{% include apuromafo/icono.html nombre="github" %}</span>
          <span class="ap-canal__texto">
            <span class="ap-canal__nombre">GitHub</span>
            <span class="ap-canal__valor">github.com/apuromafo</span>
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-canal" data-spotlight href="https://tryhackme.com/p/apuromafo">
          <span class="ap-canal__icono">{% include apuromafo/icono.html nombre="flag" %}</span>
          <span class="ap-canal__texto">
            <span class="ap-canal__nombre">TryHackMe</span>
            <span class="ap-canal__valor">tryhackme.com/p/apuromafo</span>
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-canal" data-spotlight href="https://linkedin.com/in/mfaundez">
          <span class="ap-canal__icono">{% include apuromafo/icono.html nombre="linkedin" %}</span>
          <span class="ap-canal__texto">
            <span class="ap-canal__nombre">LinkedIn</span>
            <span class="ap-canal__valor">in/mfaundez</span>
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-canal" data-spotlight href="https://www.instagram.com/apuromafo">
          <span class="ap-canal__icono">{% include apuromafo/icono.html nombre="instagram" %}</span>
          <span class="ap-canal__texto">
            <span class="ap-canal__nombre">Instagram</span>
            <span class="ap-canal__valor">@apuromafo</span>
          </span>
        </a>
      </li>
      <li data-reveal>
        <a class="ap-canal" data-spotlight href="https://twitter.com/apuromafo">
          <span class="ap-canal__icono">{% include apuromafo/icono.html nombre="x-twitter" %}</span>
          <span class="ap-canal__texto">
            <span class="ap-canal__nombre">X</span>
            <span class="ap-canal__valor">@apuromafo</span>
          </span>
        </a>
      </li>
    </ul>

    <p class="ap-nota-enlaces" data-reveal>
      {% include apuromafo/icono.html nombre="rss" %}
      Los cambios del sitio y de los proyectos quedan en
      <a href="{{ '/novedades/' | relative_url }}">Novedades</a>.
    </p>
  </div>
</section>

</div>
