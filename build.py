#!/usr/bin/env python3
"""Genera index.html a partir de tareas.json. Sin dependencias.

Uso:  python build.py            -> escribe index.html
      python build.py --serve    -> genera y abre servidor en http://localhost:8770
"""
import html
import json
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).parent
DATOS = AQUI / "tareas.json"
SALIDA = AQUI / "index.html"

COLORES = {"hecha": "#4ade80", "en-curso": "#fbbf24", "pendiente": "#94a3b8", "bloqueada": "#64748b"}
AREA_COLORES = ["#38bdf8", "#f472b6", "#a3e635", "#fb923c", "#c084fc", "#2dd4bf", "#f87171", "#facc15"]
COLUMNAS = [("en-curso", "En curso"), ("pendiente", "Libres"), ("bloqueada", "Bloqueadas"), ("hecha", "Hechas")]


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


def esc(s):
    return html.escape(str(s))


def color_area(a, areas):
    todas = list(areas)
    return AREA_COLORES[(todas.index(a) if a in todas else len(todas)) % len(AREA_COLORES)]


def fecha_corta(f):
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    try:
        y, m, d = f.split("-")
        return f"{int(d)} {meses[int(m) - 1]}" + ("" if y == "2026" else f" {y}")
    except Exception:
        return f


def tarjeta(tid, tareas, ef, areas, hoy):
    t = tareas[tid]
    e = ef[tid]
    ca = color_area(t["area"], areas)
    pie = []
    if t.get("fecha"):
        vencida = e != "hecha" and t["fecha"] < hoy
        pie.append(f'<span class="chip fecha{" venc" if vencida else ""}">{esc(fecha_corta(t["fecha"]))}</span>')
    pend = [tareas[d]["titulo"] for d in t["bloqueada_por"] if tareas[d]["estado"] != "hecha"] if e == "bloqueada" else []
    nota = f'<p class="nota">{esc(t["notas"])}</p>' if t.get("notas") else ""
    espera = ""
    if e == "bloqueada":
        extra = f' <em>+{len(pend) - 1}</em>' if len(pend) > 1 else ""
        espera = f'<p class="espera" title="Espera a: {esc(", ".join(pend))}"><span>🔒 espera a: {esc(pend[0])}</span>{extra}</p>'
    return (f'<article class="t {e}" data-area="{esc(t["area"])}" data-q="{esc((t["titulo"] + " " + t.get("notas", "")).lower())}" style="--a:{ca}">'
            f'<header><span class="area"><i></i>{esc(t["area"])}</span><span class="pr p{t["prioridad"]}">P{t["prioridad"]}</span></header>'
            f'<h4>{esc(t["titulo"])}</h4>{espera}{nota}'
            f'<footer>{"".join(pie)}</footer></article>')


def kanban_html(areas, tareas, ef, hoy):
    cols = []
    for clave, nombre in COLUMNAS:
        ids = [i for i in tareas if ef[i] == clave]
        ids.sort(key=lambda x: (tareas[x]["prioridad"], tareas[x].get("fecha", "9999"), x))
        cuerpo = "".join(tarjeta(i, tareas, ef, areas, hoy) for i in ids) or '<p class="vacio">Nada por aquí</p>'
        cols.append(f'<section class="col {clave}"><h3><i></i>{nombre}<b>{len(ids)}</b></h3><div class="cards">{cuerpo}</div></section>')
    return f'<div class="kanban">{"".join(cols)}</div>'


def grafo_svg(tareas, ef, areas):
    memo = {}
    for tid in tareas:
        profundidad(tid, tareas, memo)
    capas = {}
    for tid, p in memo.items():
        capas.setdefault(p, []).append(tid)
    conectadas = {tid for tid, t in tareas.items() if t["bloqueada_por"]} | {
        d for t in tareas.values() for d in t["bloqueada_por"]}
    capas = {p: [x for x in ids if x in conectadas] for p, ids in capas.items()}
    capas = {p: ids for p, ids in capas.items() if ids}
    if not capas:
        return "<p class='vacio'>No hay dependencias todavía.</p>"
    W, H, GX, GY = 232, 60, 52, 18
    pos = {}
    for col, p in enumerate(sorted(capas)):
        for fila, tid in enumerate(sorted(capas[p], key=lambda x: (tareas[x]["area"], tareas[x]["prioridad"], x))):
            pos[tid] = (24 + col * (W + GX), 24 + fila * (H + GY))
    ancho = max(x for x, _ in pos.values()) + W + 24
    alto = max(y for _, y in pos.values()) + H + 24
    o = [f'<svg viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}" xmlns="http://www.w3.org/2000/svg">',
         '<defs><marker id="f" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">'
         '<path d="M0,0 L9,4.5 L0,9 z" fill="#475569"/></marker></defs>']
    for tid, t in tareas.items():
        if tid not in pos:
            continue
        for d in t["bloqueada_por"]:
            x1, y1 = pos[d][0] + W, pos[d][1] + H / 2
            x2, y2 = pos[tid][0], pos[tid][1] + H / 2
            mx = (x1 + x2) / 2
            o.append(f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" stroke="#334155" stroke-width="1.6" marker-end="url(#f)"/>')
    for tid, (x, y) in pos.items():
        t = tareas[tid]
        c = COLORES[ef[tid]]
        ca = color_area(t["area"], areas)
        tit = t["titulo"]
        l1, l2 = tit, ""
        if len(tit) > 28:
            corte = tit.rfind(" ", 0, 28)
            corte = corte if corte > 12 else 28
            l1, l2 = tit[:corte], tit[corte:].strip()
            if len(l2) > 28:
                l2 = l2[:27] + "…"
        o.append(f'<g><title>{esc(tit)} [{ef[tid]}]</title>'
                 f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="10" fill="#111827" stroke="{c}" stroke-width="{2 if ef[tid] == "en-curso" else 1.4}"/>'
                 f'<circle cx="{x + 14}" cy="{y + 16}" r="4" fill="{ca}"/>'
                 f'<text x="{x + 26}" y="{y + 20}" fill="#e5e7eb" font-size="13" font-weight="600">{esc(l1)}</text>'
                 + (f'<text x="{x + 26}" y="{y + 36}" fill="#e5e7eb" font-size="13" font-weight="600">{esc(l2)}</text>' if l2 else "")
                 + f'<text x="{x + 26}" y="{y + H - 9}" fill="{c}" font-size="11">{esc(t["area"])} · {ef[tid]}</text></g>')
    o.append("</svg>")
    return "".join(o)


def construir():
    areas, tareas = cargar()
    ef = {tid: estado_efectivo(t, tareas) for tid, t in tareas.items()}
    hoy = date.today().isoformat()
    total = len(tareas)
    cuenta = {k: sum(v == k for v in ef.values()) for k, _ in COLUMNAS}
    hechas = cuenta["hecha"]
    pct = 100 * hechas // max(total, 1)
    por_area = {}
    for tid, t in tareas.items():
        por_area.setdefault(t["area"], []).append(tid)
    orden = [a for a in areas if a in por_area] + [a for a in por_area if a not in areas]
    filtros = '<button class="f on" data-f="">Todas</button>' + "".join(
        f'<button class="f" data-f="{esc(a)}" style="--a:{color_area(a, areas)}"><i></i>{esc(a)}<b>{sum(ef[i] != "hecha" for i in por_area[a])}</b></button>' for a in orden)
    proximas = sorted((t for tid, t in tareas.items() if ef[tid] != "hecha" and t.get("fecha")), key=lambda t: t["fecha"])
    stats = "".join(
        f'<div class="stat {k}"><b>{cuenta[k]}</b><span>{n}</span></div>' for k, n in COLUMNAS)
    leyenda = "".join(f'<span style="--c:{c}"><i></i>{n}</span>' for n, c in COLORES.items())
    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Gestor de tareas</title>
<style>
:root{{--bg:#0b0f17;--panel:#111827;--panel2:#161e2e;--line:#1f2a3c;--ink:#e5e7eb;--mut:#8a97ab;--dim:#5b6b82;
--curso:#fbbf24;--hecha:#4ade80;--pend:#94a3b8;--bloq:#64748b}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 "Segoe UI",system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:1500px;margin:0 auto;padding:28px 28px 60px}}
.cab{{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;flex-wrap:wrap}}
h1{{margin:0;font-size:26px;letter-spacing:-.02em}}
.sub{{color:var(--mut);margin-top:4px}} .sub code{{color:var(--dim)}}
.prog{{min-width:280px;flex:0 1 380px}}
.prog .l{{display:flex;justify-content:space-between;color:var(--mut);font-size:12px;margin-bottom:6px}} .prog .l b{{color:var(--ink);font-size:15px}}
.bar{{height:8px;background:var(--line);border-radius:99px;overflow:hidden}} .bar i{{display:block;height:100%;background:var(--hecha);border-radius:99px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0 18px}}
.stat{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 16px;display:flex;align-items:baseline;gap:10px}}
.stat b{{font-size:26px;letter-spacing:-.02em}} .stat span{{color:var(--mut)}}
.stat.en-curso b{{color:var(--curso)}} .stat.hecha b{{color:var(--hecha)}}
.barra{{display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:18px;position:sticky;top:0;background:linear-gradient(var(--bg) 82%,transparent);padding:10px 0;z-index:5}}
.tabs{{display:flex;gap:4px;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:4px}}
.tab{{background:none;border:0;color:var(--mut);font:inherit;font-weight:600;padding:7px 16px;border-radius:7px;cursor:pointer}}
.tab:hover{{color:var(--ink)}} .tab.on{{background:#1e293b;color:var(--ink)}}
.filtros{{display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.f{{background:var(--panel);border:1px solid var(--line);color:var(--mut);font:inherit;font-size:13px;padding:5px 12px;border-radius:99px;cursor:pointer;display:inline-flex;align-items:center;gap:7px}}
.f i{{width:8px;height:8px;border-radius:50%;background:var(--a)}} .f b{{font-weight:600;color:var(--dim);font-size:12px}}
.f:hover{{color:var(--ink);border-color:#2b3a52}} .f.on{{color:var(--ink);border-color:var(--a,#64748b);background:var(--panel2)}}
#q{{background:var(--panel);border:1px solid var(--line);color:var(--ink);font:inherit;padding:7px 12px;border-radius:9px;width:200px;outline:none}}
#q:focus{{border-color:#475569}}
.kanban{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;align-items:start}}
.col{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:6px 12px 14px;min-width:0}}
.col h3{{margin:0;padding:12px 4px;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);display:flex;align-items:center;gap:8px;position:sticky;top:58px;background:var(--panel);z-index:2;border-radius:12px}}
.col h3 i{{width:9px;height:9px;border-radius:50%}} .col h3 b{{margin-left:auto;background:var(--line);color:var(--ink);border-radius:99px;padding:1px 9px;font-size:12px}}
.col.en-curso h3 i{{background:var(--curso)}} .col.pendiente h3 i{{background:var(--pend)}} .col.bloqueada h3 i{{background:var(--bloq)}} .col.hecha h3 i{{background:var(--hecha)}}
.cards{{display:flex;flex-direction:column;gap:10px}}
.t{{background:var(--panel2);border:1px solid var(--line);border-radius:11px;padding:11px 13px 10px}}
.t:hover{{border-color:#2f3f58;transform:translateY(-1px)}} .t{{transition:transform .12s,border-color .12s}}
.t.en-curso{{border-color:#5b4513;box-shadow:0 0 0 1px #5b451355}}
.t header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
.area{{display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em;font-weight:600}}
.area i{{width:8px;height:8px;border-radius:50%;background:var(--a)}}
.pr{{font-size:11px;font-weight:700;padding:1px 7px;border-radius:6px;background:var(--line);color:var(--mut)}}
.pr.p1{{background:#3b1d22;color:#fca5a5}} .pr.p2{{background:#3a2d12;color:#fcd34d}}
.t h4{{margin:0;font-size:14px;font-weight:600;line-height:1.35}}
.t.hecha h4{{color:var(--dim);text-decoration:line-through;text-decoration-color:#334155}}
.t.bloqueada h4{{color:#b6c0cf}}
.espera{{margin:7px 0 0;font-size:12px;color:var(--dim);display:flex;gap:6px;align-items:center}}
.espera span{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}} .espera em{{color:var(--mut);font-style:normal;flex:none}}
.nota{{margin:6px 0 0;font-size:12px;color:var(--mut);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.t.bloqueada .nota{{-webkit-line-clamp:1}}
.t:hover .nota{{-webkit-line-clamp:unset}}
.t footer{{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}} .t footer:empty{{display:none}}
.chip{{font-size:11px;padding:2px 8px;border-radius:99px;background:var(--line);color:var(--mut)}}
.chip.fecha::before{{content:"▪ ";color:var(--dim)}} .chip.venc{{background:#3b1d22;color:#fca5a5}}
.vacio{{color:var(--dim);text-align:center;padding:18px 0;margin:0}}
.hide{{display:none!important}}
.vista{{display:none}} .vista.on{{display:block}}
.grafo{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;overflow:auto;scrollbar-color:#334155 var(--panel);scrollbar-width:thin;cursor:grab}}
.grafo::-webkit-scrollbar{{height:10px}}.grafo::-webkit-scrollbar-thumb{{background:#334155;border-radius:99px}}.grafo::-webkit-scrollbar-track{{background:var(--panel)}}
.grafo.arr{{cursor:grabbing;user-select:none}}
.grafo svg{{display:block;font-family:"Segoe UI",system-ui,sans-serif}}
.leyenda{{display:flex;gap:18px;flex-wrap:wrap;margin:0 0 14px;color:var(--mut);font-size:13px}}
.leyenda i{{display:inline-block;width:10px;height:10px;border-radius:3px;border:2px solid var(--c);margin-right:7px;vertical-align:-1px}}
.ayuda{{color:var(--dim);font-size:12px;margin:0 0 12px}}
@media(max-width:1100px){{.kanban{{grid-template-columns:repeat(2,minmax(0,1fr))}}.stats{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:640px){{.kanban{{grid-template-columns:1fr}}.wrap{{padding:18px 14px 40px}}#q{{width:100%}}}}
@media(prefers-reduced-motion:reduce){{.t{{transition:none}}.t:hover{{transform:none}}}}
</style></head><body><div class="wrap">
<div class="cab"><div><h1>Gestor de tareas</h1>
<div class="sub">{total} tareas · generado desde <code>tareas.json</code> el {esc(fecha_corta(hoy))}</div></div>
<div class="prog"><div class="l"><span><b>{pct}%</b> completado</span><span>{hechas} de {total}</span></div>
<div class="bar"><i style="width:{pct}%"></i></div></div></div>
<div class="stats">{stats}</div>
<div class="barra"><div class="tabs"><button class="tab on" data-v="kanban">Tablero</button><button class="tab" data-v="grafo">Dependencias</button></div>
<div class="filtros">{filtros}<input id="q" type="search" placeholder="Buscar tarea…"></div></div>
<div class="vista on" id="v-kanban">{kanban_html(areas, tareas, ef, hoy)}</div>
<div class="vista" id="v-grafo"><p class="ayuda">Cada flecha va de lo que hay que hacer antes a lo que desbloquea. Pasa el ratón por un nodo para ver el título completo.</p>
<div class="leyenda">{leyenda}</div><div class="grafo">{grafo_svg(tareas, ef, areas)}</div></div>
</div>
<script>
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
let area="",q="";
function aplicar(){{
  $$('.t').forEach(t=>{{const ok=(!area||t.dataset.area===area)&&(!q||t.dataset.q.includes(q));t.classList.toggle('hide',!ok)}});
  $$('.col').forEach(c=>{{const n=c.querySelectorAll('.t:not(.hide)').length;c.querySelector('h3 b').textContent=n}});
}}
$$('.f').forEach(b=>b.onclick=()=>{{area=b.dataset.f;$$('.f').forEach(x=>x.classList.toggle('on',x===b));aplicar()}});
const g=$('.grafo');let dx=null;g.onmousedown=e=>{{dx=[e.clientX,g.scrollLeft];g.classList.add('arr')}};
addEventListener('mouseup',()=>{{dx=null;g.classList.remove('arr')}});addEventListener('mousemove',e=>{{if(dx)g.scrollLeft=dx[1]-(e.clientX-dx[0])}});
$('#q').oninput=e=>{{q=e.target.value.trim().toLowerCase();aplicar()}};
$$('.tab').forEach(b=>b.onclick=()=>{{$$('.tab').forEach(x=>x.classList.toggle('on',x===b));$$('.vista').forEach(v=>v.classList.toggle('on',v.id==='v-'+b.dataset.v));
  $('.filtros').style.visibility=b.dataset.v==='kanban'?'visible':'hidden'}});
</script></body></html>"""
    SALIDA.write_text(pagina, encoding="utf-8")
    print(f"OK: {SALIDA} ({total} tareas, {hechas} hechas)")


if __name__ == "__main__":
    construir()
    if "--serve" in sys.argv:
        import functools
        import http.server
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(AQUI))
        print("http://localhost:8770/index.html")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8770), h).serve_forever()
