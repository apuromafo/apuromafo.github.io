---
layout: ap-seccion
title: Red Team
permalink: /red-team/
antetitulo: Ciberseguridad ofensiva
icono: crosshairs
bajada: >-
  Proyectos de ciberseguridad ofensiva, reversing y práctica, con el contexto
  con el que los uso en el trabajo. Las etiquetas de cada ficha sirven para
  filtrar la lista.
cifras:
  - valor: "8"
    etiqueta: fichas documentadas
  - valor: "104"
    etiqueta: referencias de normativa
  - valor: "700+"
    etiqueta: máquinas en TryHackMe
autor: true
filtro: true
---

<div class="card" markdown="1" data-spotlight data-reveal>

### [Catálogo de ciberseguridad](https://github.com/apuromafo/Repositorio_Python/tree/main/064_Regulaciones)

104 referencias de ciberseguridad, privacidad y regulación financiera (Chile, América Latina y banca), con CLI de consulta en Python y corte al 25-09-2026.

Incluye Ley 21.719, Ley 21.663, normativa CMF, LGPD, GDPR, NIS2, DORA, PCI DSS v4.0.1, NIST CSF 2.0, MITRE ATT&CK y OWASP ASVS 5.0.0, entre otras. Ejemplos de uso:

**Historia:** partió de un script de 49 entradas y llegó a la v3.0.0 de septiembre de 2026, con 104 referencias, CLI de consulta y suite de 14 pruebas.

```bash
python catalogo_ciberseguridad.py banca --rol blue-team
python catalogo_ciberseguridad.py ver CL-PRV-001
python catalogo_ciberseguridad.py mapa
```

<span class="tags"><a class="tag" data-tag="ciberseguridad">#ciberseguridad</a> <a class="tag" data-tag="privacidad">#privacidad</a> <a class="tag" data-tag="banca">#banca</a> <a class="tag" data-tag="chile">#chile</a> <a class="tag" data-tag="latam">#latam</a> <a class="tag" data-tag="python">#python</a> <a class="tag" data-tag="red-team">#red-team</a> <a class="tag" data-tag="blue-team">#blue-team</a></span>

</div>

<div class="card" markdown="1" data-spotlight data-reveal>

### [CTF — Writeups](https://github.com/apuromafo/ctf)

Apuntes y resoluciones de CTF guardados aquí con fines documentales y de aprendizaje.

**Historia:** creado en 2023 como cuaderno de resoluciones. No todo el material es de autoría propia: el fin es documentativo.

Plataformas que documento: [TryHackMe](https://github.com/apuromafo/ctf/tree/main/Tryhackme) · [HackTheBox](https://github.com/apuromafo/ctf/tree/main/Hackthebox) · [OverTheWire](https://github.com/apuromafo/ctf/tree/main/OverThewire) · [PicoCTF](https://github.com/apuromafo/ctf/tree/main/PicoCTF) · [Proving Grounds](https://github.com/apuromafo/ctf/tree/main/Proving%20Ground%20Play) · [Atenea CCN-CERT](https://github.com/apuromafo/ctf/tree/main/atenea.ccn-cert.cni.es) (histórico)

**Hito:** top 100 del ranking de Atenea (CCN-CERT), plataforma española de retos. Las soluciones se retiraron voluntariamente por respeto a las normas de la plataforma (no publicar soluciones, solo pequeñas pistas).

<span class="tags"><a class="tag" data-tag="ctf">#ctf</a> <a class="tag" data-tag="writeups">#writeups</a> <a class="tag" data-tag="pentesting">#pentesting</a> <a class="tag" data-tag="red-team">#red-team</a></span>

</div>

<div class="card" markdown="1" data-spotlight data-reveal>

### [RCE Lab](https://github.com/apuromafo/RCE_Lab)

Laboratorio de crackmes, keygenmes, seriales y ejercicios de ingeniería inversa.

**Historia:** activo desde 2018.

<span class="tags"><a class="tag" data-tag="reverse-engineering">#reverse-engineering</a> <a class="tag" data-tag="crackme">#crackme</a> <a class="tag" data-tag="keygenme">#keygenme</a> <a class="tag" data-tag="assembly">#assembly</a></span>

</div>

<div class="card" markdown="1" data-spotlight data-reveal>

### [Crackslatinos — Respaldo](https://github.com/apuromafo/Crackslatinos_/)

Respaldo personal de la lista de reversing Crackslatinos, liderada por Ricardo Narvaja (Argentina), consultor senior de ciberseguridad ofensiva y desarrollador de exploits, incluyendo sus [teorías numeradas](https://github.com/apuromafo/Crackslatinos_/tree/master/Teorias_Numeradas).

**Historia:** es una comunidad con 26 años de trayectoria. Ricardo comparte libremente sus conocimientos de reversing, uso de IDA y más. Lo oficial es siempre lo dicho por su autor; el punto de encuentro es [t.me/crackslatinos](https://t.me/crackslatinos), donde participo como un miembro más, sin jerarquías ni membresías. El sitio original desapareció y el respaldo se conserva como referencia de ese trabajo, que es de Ricardo.

<span class="tags"><a class="tag" data-tag="reversing">#reversing</a> <a class="tag" data-tag="assembly">#assembly</a> <a class="tag" data-tag="crackslatinos">#crackslatinos</a> <a class="tag" data-tag="historia">#historia</a></span>

</div>

<div class="card" markdown="1" data-spotlight data-reveal>

### [OllydbgScript](https://github.com/apuromafo/OllydbgScript)

Recolección de scripts para OllyDbg 1.0 orientados a análisis y depuración.

**Historia:** recolección iniciada en 2016, en la época clásica del reversing en Windows.

<span class="tags"><a class="tag" data-tag="ollydbg">#ollydbg</a> <a class="tag" data-tag="debugging">#debugging</a> <a class="tag" data-tag="reverse-engineering">#reverse-engineering</a></span>

</div>

<div class="card" markdown="1" data-spotlight data-reveal>

### [TryHackMe — Perfil](https://tryhackme.com/p/apuromafo)

Perfil activo en TryHackMe: más de 700 máquinas completadas entre laboratorios guiados y retos. Al 25-09-2026, 283 días seguidos de actividad (streak).

**Historia:** años de práctica continua en la plataforma, complementando el reversing con pentesting aplicado.

<span class="tags"><a class="tag" data-tag="tryhackme">#tryhackme</a> <a class="tag" data-tag="pentesting">#pentesting</a> <a class="tag" data-tag="practica">#práctica</a> <a class="tag" data-tag="red-team">#red-team</a></span>

</div>

<div class="card" markdown="1" data-spotlight data-reveal>

### [Juego 404 — Laberinto](https://github.com/apuromafo/ctf/tree/main/Tryhackme/Personal%20Profile/404_juego)

Juego de creación propia con estética TryHackMe: laberinto jugable en el navegador con 10 niveles en JSON, ranking con protección CSRF y servidor propio en Python. Se juega con el personaje de Echo, de TryHackMe.

**Historia:** diseñado y programado para este sitio, mezclando juego, web y seguridad.

<span class="tags"><a class="tag" data-tag="juego">#juego</a> <a class="tag" data-tag="python">#python</a> <a class="tag" data-tag="tryhackme">#tryhackme</a> <a class="tag" data-tag="web">#web</a></span>

</div>

<div class="card" markdown="1" data-spotlight data-reveal>

### [DockerLabs — Respaldo de máquinas](https://github.com/apuromafo/dockerlabs_backup)

Respaldo de máquinas de práctica de laboratorio de intrusión.

**Historia:** creado en 2024 para conservar esas máquinas de práctica.

<span class="tags"><a class="tag" data-tag="pentesting">#pentesting</a> <a class="tag" data-tag="laboratorio">#laboratorio</a> <a class="tag" data-tag="practica">#practica</a></span>

</div>
