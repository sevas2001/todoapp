# ToDoApp — instrucciones para Claude Code

Proyecto mínimo: `tareas.json` (fuente de verdad) → `python build.py` → `index.html`. Sin dependencias, solo Python 3.

## Qué hacer cuando el usuario pida algo
- **Añadir / editar / completar tareas**: edita `tareas.json` (formato en `README.md`) y ejecuta `python build.py`. Para completar, `estado: "hecha"`. Nunca borres tareas, márcalas hechas.
- **Ids**: únicos, minúsculas-con-guiones. `bloqueada_por` solo con ids existentes y sin ciclos (el script lo valida).
- **Ver la app**: `python build.py --serve` y abrir http://localhost:8765/index.html, o abrir `index.html`.
- Tras cualquier cambio, ejecuta `python build.py` y confirma que termina con `OK:`.

## Primera vez en una máquina nueva
1. Comprueba `python --version` (3.8+).
2. Sustituye las tareas de ejemplo de `tareas.json` por las reales del usuario (pregúntale cuáles; si te las pasa en texto, estructúralas con áreas, prioridades y dependencias).
3. `python build.py` y abre `index.html`.

## Privacidad
El repo es público. Antes de hacer `git push` con tareas reales, avisa al usuario: puede contener información del trabajo. Opción: poner `tareas.json` en `.gitignore`.
