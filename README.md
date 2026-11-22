# ToDoApp

Visor web de tareas con **estados** (hecha / en curso / pendiente) y **dependencias** entre ellas (una tarea sale bloqueada hasta que terminen las que la bloquean). Sin dependencias: solo Python 3 y un navegador.

## Instalación

```bash
git clone https://github.com/sevas2001/todoapp.git
cd todoapp
python build.py            # genera index.html (ábrelo con doble clic)
python build.py --serve    # además lo sirve en http://localhost:8765/index.html
```

## Uso

1. Edita `tareas.json` (a mano, con un editor o pidiéndoselo a Claude Code).
2. Ejecuta `python build.py` para regenerar `index.html`.
3. Abre `index.html` en el navegador.

Verás: progreso total, tarea(s) en curso, siguientes tareas libres por prioridad, grafo de dependencias y lista por áreas.

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

El `tareas.json` incluido es solo un ejemplo. Sustitúyelo por el tuyo. **Si el repo es público, no subas información sensible**: descomenta `tareas.json` en `.gitignore` o trabaja en un fork/repo privado.
