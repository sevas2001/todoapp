#!/usr/bin/env python3
"""Genera index.html a partir de tareas.json. Sin dependencias.

Uso:  python build.py            -> escribe index.html
      python build.py --serve    -> genera y abre servidor en http://localhost:8765
"""
import html
import json
import sys
from pathlib import Path

AQUI = Path(__file__).parent
DATOS = AQUI / "tareas.json"
SALIDA = AQUI / "index.html"

COLORES = {"hecha": "#3fb950", "en-curso": "#d29922", "pendiente": "#8b949e", "bloqueada": "#484f58"}


def cargar():
    d = json.loads(DATOS.read_text(encoding="utf-8"))
    tareas = {t["id"]: t for t in d["tareas"]}
    for t in tareas.values():
        t.setdefault("bloqueada_por", [])
        t.setdefault("prioridad", 2)
        for dep in t["bloqueada_por"]:
            if dep not in tareas:
                raise SystemExit(f"Tarea '{t['id']}' depende de '{dep}' que no existe")
    return d.get("areas", []), tareas


def estado_efectivo(t, tareas):
    if t["estado"] == "hecha":
        return "hecha"
    if any(tareas[d]["estado"] != "hecha" for d in t["bloqueada_por"]):
        return "bloqueada"
    return t["estado"]


def profundidad(tid, tareas, memo, pila=()):
    if tid in memo:
        return memo[tid]
    if tid in pila:
        raise SystemExit(f"Ciclo de dependencias: {' -> '.join(pila + (tid,))}")
    deps = tareas[tid]["bloqueada_por"]
    memo[tid] = 0 if not deps else 1 + max(profundidad(d, tareas, memo, pila + (tid,)) for d in deps)
    return memo[tid]


def grafo_svg(tareas, ef):
    memo = {}
    for tid in tareas:
        profundidad(tid, tareas, memo)
    capas = {}
    for tid, p in memo.items():
        capas.setdefault(p, []).append(tid)
    # solo tareas con alguna relacion, para que el grafo no se llene de islas
    conectadas = {tid for tid, t in tareas.items() if t["bloqueada_por"]} | {
        d for t in tareas.values() for d in t["bloqueada_por"]}
    capas = {p: [x for x in ids if x in conectadas] for p, ids in capas.items()}
    capas = {p: ids for p, ids in capas.items() if ids}
    W, H, GX, GY = 170, 44, 36, 18
    pos = {}
    for col, p in enumerate(sorted(capas)):
        for fila, tid in enumerate(sorted(capas[p], key=lambda x: (tareas[x]["area"], x))):
            pos[tid] = (20 + col * (W + GX), 20 + fila * (H + GY))
    if not pos:
        return "<p>No hay dependencias todavía.</p>"
    ancho = max(x for x, _ in pos.values()) + W + 20
    alto = max(y for _, y in pos.values()) + H + 20
    o = [f'<svg viewBox="0 0 {ancho} {alto}" style="width:100%;height:auto;max-width:{ancho}px" xmlns="http://www.w3.org/2000/svg">',
         '<defs><marker id="f" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
         '<path d="M0,0 L8,4 L0,8 z" fill="#6e7681"/></marker></defs>']
    for tid, t in tareas.items():
        if tid not in pos:
            continue
        for d in t["bloqueada_por"]:
            x1, y1 = pos[d][0] + W, pos[d][1] + H / 2
            x2, y2 = pos[tid][0], pos[tid][1] + H / 2
            mx = (x1 + x2) / 2
            o.append(f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" '
                     f'stroke="#6e7681" stroke-width="1.5" marker-end="url(#f)"/>')
    for tid, (x, y) in pos.items():
        t = tareas[tid]
        c = COLORES[ef[tid]]
        txt = t["titulo"] if len(t["titulo"]) <= 24 else t["titulo"][:23] + "…"
        o.append(f'<g><title>{html.escape(t["titulo"])} [{ef[tid]}]</title>'
                 f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="8" fill="#161b22" stroke="{c}" stroke-width="2"/>'
                 f'<text x="{x + 10}" y="{y + 19}" fill="#e6edf3" font-size="12">{html.escape(txt)}</text>'
                 f'<text x="{x + 10}" y="{y + 35}" fill="{c}" font-size="10">{html.escape(t["area"])} · {ef[tid]}</text></g>')
    o.append("</svg>")
    return "".join(o)


def lista_html(areas, tareas, ef):
    por_area = {}
    for tid, t in tareas.items():
        por_area.setdefault(t["area"], []).append(tid)
    orden = [a for a in areas if a in por_area] + [a for a in por_area if a not in areas]
    o = []
    for a in orden:
        ids = sorted(por_area[a], key=lambda x: (ef[x] == "hecha", tareas[x]["prioridad"], x))
        hechas = sum(ef[i] == "hecha" for i in ids)
        o.append(f'<section><h3>{html.escape(a)} <small>{hechas}/{len(ids)}</small></h3><ul>')
        for i in ids:
            t = tareas[i]
            e = ef[i]
            extra = ""
            if e == "bloqueada":
                pend = [tareas[d]["titulo"] for d in t["bloqueada_por"] if tareas[d]["estado"] != "hecha"]
                extra += f'<div class="n">⛔ espera a: {html.escape(", ".join(pend))}</div>'
            if t.get("fecha"):
                extra += f'<div class="n">📅 {t["fecha"]}</div>'
            if t.get("notas"):
                extra += f'<div class="n">{html.escape(t["notas"])}</div>'
            marca = "✔" if e == "hecha" else ("▶" if e == "en-curso" else ("🔒" if e == "bloqueada" else "○"))
            o.append(f'<li class="{e}"><span class="m">{marca}</span> '
                     f'<span class="p p{t["prioridad"]}">P{t["prioridad"]}</span> {html.escape(t["titulo"])}{extra}</li>')
        o.append("</ul></section>")
    return "".join(o)


def construir():
    areas, tareas = cargar()
    ef = {tid: estado_efectivo(t, tareas) for tid, t in tareas.items()}
    total = len(tareas)
    hechas = sum(v == "hecha" for v in ef.values())
    curso = [tareas[i]["titulo"] for i, v in ef.items() if v == "en-curso"]
    libres = sorted((i for i, v in ef.items() if v == "pendiente"), key=lambda x: tareas[x]["prioridad"])
    sig = "".join(f"<li>{html.escape(tareas[i]['titulo'])}</li>" for i in libres[:3]) or "<li>—</li>"
    en = "".join(f"<li>{html.escape(x)}</li>" for x in curso) or "<li>—</li>"
    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>ToDoApp</title>
<style>
body{{background:#0d1117;color:#e6edf3;font:14px system-ui,sans-serif;margin:0;padding:24px;max-width:1200px;margin:auto}}
h1{{margin:0 0 4px}} h2{{margin-top:32px;border-bottom:1px solid #30363d;padding-bottom:6px}}
h3 small{{color:#8b949e;font-weight:normal}}
.top{{display:flex;gap:16px;flex-wrap:wrap;margin-top:16px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:12px 16px;flex:1;min-width:220px}}
.card h4{{margin:0 0 6px;color:#8b949e;font-weight:600;font-size:12px;text-transform:uppercase}}
.card ul{{margin:0;padding-left:18px}}
.bar{{height:8px;background:#30363d;border-radius:4px;overflow:hidden}} .bar i{{display:block;height:100%;background:#3fb950}}
section{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:4px 16px 8px;margin:12px 0}}
ul{{list-style:none;padding:0}} li{{padding:5px 0;border-bottom:1px solid #21262d}} li:last-child{{border:0}}
li.hecha{{color:#8b949e;text-decoration:line-through}} li.bloqueada{{color:#8b949e}} li.en-curso{{color:#e3b341}}
.m{{display:inline-block;width:20px}} .n{{margin-left:20px;color:#8b949e;font-size:12px;text-decoration:none}}
.p{{font-size:10px;border-radius:4px;padding:1px 4px;background:#30363d;margin-right:4px}} .p1{{background:#da3633}} .p2{{background:#9e6a03}}
.g{{overflow:auto;background:#161b22;border:1px solid #30363d;border-radius:10px;padding:8px}}
.leyenda span{{margin-right:14px;font-size:12px}}
</style></head><body>
<h1>ToDoApp</h1>
<div style="color:#8b949e">{hechas}/{total} hechas · generado desde <code>tareas.json</code></div>
<div class="bar" style="margin-top:8px"><i style="width:{100 * hechas // max(total, 1)}%"></i></div>
<div class="top">
<div class="card"><h4>En curso</h4><ul>{en}</ul></div>
<div class="card"><h4>Siguiente libre (por prioridad)</h4><ul>{sig}</ul></div>
</div>
<h2>Dependencias</h2>
<div class="leyenda">{"".join(f'<span style="color:{c}">■ {n}</span>' for n, c in COLORES.items())}</div>
<div class="g">{grafo_svg(tareas, ef)}</div>
<h2>Por áreas</h2>
{lista_html(areas, tareas, ef)}
</body></html>"""
    SALIDA.write_text(pagina, encoding="utf-8")
    print(f"OK: {SALIDA} ({total} tareas, {hechas} hechas)")


if __name__ == "__main__":
    construir()
    if "--serve" in sys.argv:
        import functools
        import http.server
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(AQUI))
        print("http://localhost:8765/index.html")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8765), h).serve_forever()
