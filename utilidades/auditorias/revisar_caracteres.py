"""Busca caracteres que no deberían estar en el repositorio.

El sitio está en español y los archivos en UTF-8, así que acentos, eñes y
rayas están bien. Lo que sale es otra cosa: cirílico o chino colado de un
copiado y pegado, o un carácter de reemplazo (U+FFFD) que aparece cuando algo
se leyó con la codificación equivocada. Eso no se ve en una revisión visual
porque el navegador lo画出 o lo esconde, pero rompe las búsquedas y deja
basura en el sitio publicado.

Solo mira lo que git rastrea, más planificacion.md, que está en .gitignore y es
justo donde más fácil se cuela una cosa rara. Los binarios se saltan.

Sale con 1 si encontró algo, para que el CLI lo cuente como falla.
"""

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import contexto  # noqa: E402

# ASCII, el suplemento y medio, y los signos que se usan en el texto. Cada
# excepción de la lista va con su porqué, que es la parte que hay que leer cuando
# algo nuevo aparezca en ella.
permitidos = set(range(0x20, 0x7F)) | set(range(0xA0, 0x180)) | {
    0x2013,  # raya corta (–)
    0x2014,  # raya larga (—)
    0x2018,  # comilla simple de apertura (‘)
    0x2019,  # comilla simple de cierre (’)
    0x201C,  # comilla doble de apertura (“)
    0x201D,  # comilla doble de cierre (”)
    0x00B7,  # punto medio (·)
    0x2192,  # flecha a la derecha (→), la que se usa en los comentarios
    0x00D7,  # signo de multiplicación (×), para medidas
    0x00A1,  # signo de exclamación inicial (¡)
    0x00BF,  # signo de interrogación inicial (¿)
    0x2026,  # puntos suspensivos (…)
    0x258C,  # bloque izquierdo ▌: el cursor del texto rotativo de la portada,
             # dibujado a propósito con content en apuromafo.css
    0x1F40D,  # serpiente 🐍: el emoji con el que el autor describe su proyecto
              # "Dcode.py" en indice.md; es contenido suyo, no un descuido
}
saltados = {".woff2", ".woff", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}
raiz = contexto.REPO
problemas = 0

archivos = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                          cwd=raiz).stdout.split()
archivos += ["planificacion.md", "ESTADO_LOCAL.md"]
for rel in archivos:
    f = raiz / rel
    if not f.is_file() or f.suffix.lower() in saltados:
        continue
    try:
        t = f.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001 - un archivo ilegible también avisa
        print(f"{rel}: no se pudo leer ({e})")
        problemas += 1
        continue
    malos = {}
    for i, linea in enumerate(t.splitlines(), 1):
        for ch in linea:
            if ord(ch) > 127 and ord(ch) not in permitidos:
                malos.setdefault(ch, []).append(i)
    for ch, ls in malos.items():
        problemas += 1
        print(f"{rel}: U+{ord(ch):04X} {ch!r} lineas {sorted(set(ls))[:6]}")

if problemas:
    print(f"{problemas} archivo(s) con caracteres raros")
    sys.exit(1)
print("ningún carácter raro")
