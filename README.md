# ToDoApp

> ⚠️ **Los datos de este repositorio son falsos.** El `tareas.json` incluido es un proyecto inventado (lanzar una app ficticia) para que veas cómo se ve la herramienta. No hay información personal real. Sustitúyelo por tus propias tareas.

Visor web de tareas con **estados** (hecha / en curso / pendiente) y **dependencias** entre ellas: una tarea sale *bloqueada* hasta que terminan las que la bloquean. Sin dependencias: solo Python 3 y un navegador.

## Qué ves al abrirlo
- **Kanban** con cuatro columnas: En curso, Libres, Bloqueadas y Hechas.
- **Grafo de dependencias** (arrastrable) para ver qué desbloquea qué.
- Filtro por área, buscador de texto, progreso total y fechas (las vencidas se marcan).

## Instalación y uso

```bash
git clone https://github.com/sevas2001/todoapp.git
cd todoapp
python build.py            # genera index.html (ábrelo con doble clic)
python build.py --serve    # además lo sirve en http://localhost:8770/index.html
```

1. Edita `tareas.json` (a mano, con un editor o pidiéndoselo a un asistente de código).
2. Ejecuta `python build.py` para regenerar `index.html`.
3. Abre `index.html` en el navegador.

## Formato de `tareas.json`

| campo | valor |
|---|---|
| `id` | único, minúsculas con guiones |
| `titulo` | texto |
| `area` | una de las `areas` definidas arriba en el JSON |
| `estado` | `pendiente`, `en-curso` o `hecha` |
| `bloqueada_por` | lista de ids; mientras alguna no esté `hecha`, la tarea sale bloqueada |
| `prioridad` | 1 alta, 2 media, 3 baja |
| `fecha`, `notas` | opcionales (`AAAA-MM-DD`) |

Marcar algo hecho = cambiar `estado` a `"hecha"` y volver a ejecutar `build.py`; lo que dependía de ello se desbloquea solo. El script falla con un error claro si hay una dependencia a un id inexistente o un ciclo.

## Tus propias tareas
Reemplaza el `tareas.json` de ejemplo por el tuyo. **Si haces fork público, no subas información sensible**: descomenta `tareas.json` en `.gitignore` o trabaja en un repo privado.
