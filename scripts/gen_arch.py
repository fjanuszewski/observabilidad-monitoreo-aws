#!/usr/bin/env python3
"""Genera un diagrama de arquitectura SVG por laboratorio que contempla TODOS
los componentes del CloudFormation de cada clase. On-brand (mismos íconos y
paleta), con límites de VPC/subred/cluster y flechas etiquetadas.

Salida por clase:
  clase-N/.../laboratorio/arquitectura.svg   (standalone, para render a PNG y como fuente)
Y además inyecta el mismo SVG (responsive) dentro de la sección Arquitectura de guia.html.
"""
import os, re, html

ROOT = os.path.join(os.path.dirname(__file__), "..")
ICON = "../../assets/img/services"   # ruta relativa desde clase-N/laboratorio/

# ---- Geometría de la grilla ------------------------------------------------
NW, NH = 178, 108          # tamaño de nodo
CGAP, RGAP = 238, 178      # separación centro a centro
MX, MTOP, MBOT = 44, 88, 52

# ---- Paleta ----------------------------------------------------------------
NAVY, NAVY2, INK, MUTED, LINE = "#16294a", "#1e3a63", "#22304a", "#5f6f86", "#e4eaf3"
ACCENT = "#b3590f"
PAPER, PAPER2 = "#ffffff", "#f6f9fc"
GROUP_COLORS = {
    "vpc": "#5B34C4", "subnet": "#2E73B8", "cluster": "#E8730C",
    "task": "#EC8B2B", "pipeline": "#7A3FF2", "alerts": "#C7157B",
}


def esc(s): return html.escape(str(s), quote=True)


def wrap(text, maxch):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= maxch:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def clip(cx, cy, tx, ty, hw=NW / 2, hh=NH / 2):
    """Punto en el borde del rect (cx,cy,hw,hh) en dirección a (tx,ty)."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = hw / abs(dx) if dx else 1e9
    sy = hh / abs(dy) if dy else 1e9
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


class Diagram:
    def __init__(self, title):
        self.title = title
        self.nodes = {}   # id -> (col,row,icon,title,sub)
        self.groups = []  # (label, members, kind)
        self.edges = []   # (a,b,label,dashed)

    def node(self, nid, col, row, icon, title, sub=""):
        self.nodes[nid] = (col, row, icon, title, sub)

    def group(self, label, members, kind):
        self.groups.append((label, members, kind))

    def edge(self, a, b, label="", dashed=False, route="straight"):
        self.edges.append((a, b, label, dashed, route))

    def center(self, nid):
        col, row = self.nodes[nid][0], self.nodes[nid][1]
        return MX + NW / 2 + col * CGAP, MTOP + NH / 2 + row * RGAP

    def canvas(self):
        maxc = max(n[0] for n in self.nodes.values())
        maxr = max(n[1] for n in self.nodes.values())
        extra = 78 if any(e[4] == "below" for e in self.edges) else 0
        return MX * 2 + maxc * CGAP + NW, MTOP + maxr * RGAP + NH + MBOT + extra

    def body(self):
        W, H = self.canvas()
        out = []
        out.append(f'<rect x="0" y="0" width="{W}" height="{H}" rx="18" fill="{PAPER2}"/>')
        out.append(f'<text x="{MX}" y="46" font-family="Segoe UI,Helvetica,Arial,sans-serif" '
                   f'font-size="20" font-weight="800" fill="{NAVY}">{esc(self.title)}</text>')

        # --- grupos (detrás) ---
        for label, members, kind in self.groups:
            xs = [self.center(m)[0] for m in members]
            ys = [self.center(m)[1] for m in members]
            pad = 26
            x0 = min(xs) - NW / 2 - pad
            y0 = min(ys) - NH / 2 - pad
            x1 = max(xs) + NW / 2 + pad
            y1 = max(ys) + NH / 2 + pad
            col = GROUP_COLORS.get(kind, MUTED)
            out.append(f'<rect x="{x0:.0f}" y="{y0:.0f}" width="{x1-x0:.0f}" height="{y1-y0:.0f}" '
                       f'rx="16" fill="{col}" fill-opacity="0.05" stroke="{col}" stroke-opacity="0.55" '
                       f'stroke-width="1.6" stroke-dasharray="7 5"/>')
            tw = 12 + len(label) * 7.4
            out.append(f'<rect x="{x0:.0f}" y="{y0-13:.0f}" width="{tw:.0f}" height="24" rx="7" fill="{col}"/>')
            out.append(f'<text x="{x0+tw/2:.0f}" y="{y0+3:.0f}" text-anchor="middle" '
                       f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="12.5" '
                       f'font-weight="700" fill="#fff">{esc(label)}</text>')

        # --- aristas (sobre grupos, debajo de nodos) ---
        for a, b, label, dashed, route in self.edges:
            ax, ay = self.center(a)
            bx, by = self.center(b)
            da = ' stroke-dasharray="6 5"' if dashed else ''
            if route == "below":
                # lazo en U por debajo del diagrama (p.ej. auto-remediación)
                ya, yb = ay + NH / 2, by + NH / 2
                ymid = H - 34
                out.append(f'<path d="M {ax:.0f} {ya:.0f} L {ax:.0f} {ymid:.0f} L {bx:.0f} {ymid:.0f} '
                           f'L {bx:.0f} {yb:.0f}" fill="none" stroke="{ACCENT}" stroke-width="2.4"{da} '
                           f'marker-end="url(#arw)"/>')
                lx, ly = (ax + bx) / 2, ymid
            else:
                p1 = clip(ax, ay, bx, by)
                p2 = clip(bx, by, ax, ay)
                out.append(f'<line x1="{p1[0]:.0f}" y1="{p1[1]:.0f}" x2="{p2[0]:.0f}" y2="{p2[1]:.0f}" '
                           f'stroke="{ACCENT}" stroke-width="2.4"{da} marker-end="url(#arw)"/>')
                lx, ly = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            if label:
                tw = 10 + len(label) * 6.0
                out.append(f'<rect x="{lx-tw/2:.0f}" y="{ly-11:.0f}" width="{tw:.0f}" height="20" rx="6" '
                           f'fill="#fff" stroke="{LINE}"/>')
                out.append(f'<text x="{lx:.0f}" y="{ly+3:.0f}" text-anchor="middle" '
                           f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="11" '
                           f'font-weight="600" fill="{NAVY2}">{esc(label)}</text>')

        # --- nodos ---
        for nid, (col, row, icon, title, sub) in self.nodes.items():
            cx, cy = self.center(nid)
            x, y = cx - NW / 2, cy - NH / 2
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{NW}" height="{NH}" rx="14" '
                       f'fill="{PAPER}" stroke="{LINE}" stroke-width="1.4" filter="url(#sh)"/>')
            out.append(f'<image href="{ICON}/{icon}.svg" x="{cx-19:.0f}" y="{y+12:.0f}" width="38" height="38"/>')
            tlines = wrap(title, 24)[:2]
            ty = y + 66
            for ln in tlines:
                out.append(f'<text x="{cx:.0f}" y="{ty:.0f}" text-anchor="middle" '
                           f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="14.5" '
                           f'font-weight="700" fill="{NAVY}">{esc(ln)}</text>')
                ty += 17
            if sub:
                sy = ty + (0 if len(tlines) == 2 else 2)
                for ln in wrap(sub, 30)[:1]:
                    out.append(f'<text x="{cx:.0f}" y="{sy:.0f}" text-anchor="middle" '
                               f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="11.5" '
                               f'fill="{MUTED}">{esc(ln)}</text>')
        return W, H, "\n".join(out)

    def svg_standalone(self):
        W, H, body = self.body()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
                f'font-family="Segoe UI,Helvetica,Arial,sans-serif">\n{self._defs()}\n{body}\n</svg>\n')

    def svg_inline(self):
        W, H, body = self.body()
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
                f'role="img" aria-label="Diagrama de arquitectura" '
                f'style="width:100%;height:auto;display:block">\n{self._defs()}\n{body}\n</svg>')

    def _defs(self):
        return (f'<defs>'
                f'<marker id="arw" markerWidth="9" markerHeight="9" refX="7.5" refY="4.5" orient="auto">'
                f'<path d="M1,1 L8,4.5 L1,8 Z" fill="{ACCENT}"/></marker>'
                f'<filter id="sh" x="-20%" y="-20%" width="140%" height="150%">'
                f'<feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#16294a" flood-opacity="0.10"/>'
                f'</filter></defs>')


# ============================================================ DEFINICIONES ====
def clase1():
    d = Diagram("Arquitectura del laboratorio · Clase 1")
    d.node("ssm", 0, 0, "systems-manager", "SSM Parameter Store", "config del agente")
    d.node("iam", 0, 1, "iam", "IAM Role + Profile", "sin credenciales fijas")
    d.node("ec2", 2, 0.5, "ec2", "EC2 + CloudWatch agent", "t3.micro · UserData")
    d.node("cw", 3, 0.5, "cloudwatch", "CloudWatch", "SO · hipervisor · custom")
    d.group("VPC · subred pública · IGW", ["ec2"], "vpc")
    d.edge("ssm", "ec2", "ssm:config")
    d.edge("iam", "ec2", "rol")
    d.edge("ec2", "cw", "métricas")
    return d


def clase2():
    d = Diagram("Arquitectura del laboratorio · Clase 2")
    d.node("ec2", 0, 1, "ec2", "EC2 (app)", "genera logs")
    d.node("kms", 1, 0, "kms", "KMS", "cifra el log group")
    d.node("lg", 1, 1, "cloudwatch-logs", "Log group", "retención definida")
    d.node("li", 1, 2, "cloudwatch-logs", "Logs Insights", "consulta guardada")
    d.node("mf", 2, 1, "cloudwatch", "Metric filter", "cuenta ERROR")
    d.node("al", 3, 1, "cloudwatch-alarms", "Alarma", "umbral de errores")
    d.node("sns", 4, 1, "sns", "SNS", "email")
    d.edge("ec2", "lg", "logs")
    d.edge("kms", "lg", "cifra")
    d.edge("lg", "li", "consulta")
    d.edge("lg", "mf", "patrón")
    d.edge("mf", "al", "métrica")
    d.edge("al", "sns", "notifica")
    return d


def clase3():
    d = Diagram("Arquitectura del laboratorio · Clase 3")
    d.node("lg", 0, 1, "cloudwatch-logs", "CloudWatch Logs", "origen de logs")
    d.node("fh", 1, 1, "firehose", "Data Firehose", "subscription filter")
    d.node("s3", 2, 1, "s3", "Amazon S3", "partición por fecha")
    d.node("gl", 2, 0, "glacier", "S3 Glacier", "lifecycle")
    d.node("glue", 3, 1, "glue", "Glue Data Catalog", "base + tabla + SerDe")
    d.node("ath", 4, 1, "athena", "Amazon Athena", "SQL de investigación")
    d.node("iam", 0, 2, "iam", "IAM Roles", "CWL → Firehose · S3")
    d.group("Pipeline de archivado", ["fh", "s3", "gl"], "pipeline")
    d.edge("lg", "fh", "stream")
    d.edge("fh", "s3", "entrega")
    d.edge("s3", "gl", "transición")
    d.edge("s3", "glue", "cataloga")
    d.edge("glue", "ath", "esquema")
    return d


def clase4():
    d = Diagram("Arquitectura del laboratorio · Clase 4")
    d.node("iam", 0, 0, "iam", "IAM Roles", "task + execution")
    d.node("svc", 0, 1, "ecs", "ECS Service", "mantiene la tarea")
    d.node("task", 1, 1, "fargate", "Tarea Fargate", "app + log router")
    d.node("fl", 1, 2, "firelens", "FireLens / awslogs", "driver de logs")
    d.node("ci", 2, 1, "container-insights", "Container Insights", "métricas tarea/contenedor")
    d.node("logs", 2, 2, "cloudwatch-logs", "Log groups", "app + firelens")
    d.group("Clúster ECS · VPC", ["svc", "task", "fl"], "cluster")
    d.edge("iam", "task", "roles")
    d.edge("svc", "task", "corre")
    d.edge("task", "fl", "stdout")
    d.edge("fl", "logs", "rutea")
    d.edge("task", "ci", "métricas")
    return d


def clase5():
    d = Diagram("Arquitectura del laboratorio · Clase 5")
    d.node("dash", 1, 0, "cloudwatch-dashboards", "Dashboard", "métricas + logs")
    d.node("iam", 2, 0, "iam", "IAM Roles", "EventBridge · SSM")
    d.node("sns", 3, 0, "sns", "SNS", "email")
    d.node("ec2", 0, 1, "ec2", "EC2", "carga monitoreada")
    d.node("al", 1, 1, "cloudwatch-alarms", "Alarmas", "métrica·compuesta·anomalía")
    d.node("eb", 2, 1, "eventbridge", "EventBridge", "regla + patrón")
    d.node("ssm", 3, 1, "systems-manager", "SSM Automation", "runbook remedia")
    d.edge("ec2", "al", "métrica")
    d.edge("al", "eb", "estado")
    d.edge("eb", "ssm", "dispara")
    d.edge("eb", "sns", "notifica")
    d.edge("al", "dash", "visualiza")
    d.edge("iam", "eb", "permisos")
    d.edge("ssm", "ec2", "remedia", dashed=True, route="below")
    return d


CLASSES = {
    "clase-1-fundamentos-metricas-cloudwatch": clase1,
    "clase-2-logs-recoleccion-retencion": clase2,
    "clase-3-archivado-lifecycle-athena": clase3,
    "clase-4-observabilidad-contenedores-ecs-fargate": clase4,
    "clase-5-alertas-respuesta-automatizada": clase5,
}


def inject_into_guia(cls_dir, inline_svg):
    path = os.path.join(ROOT, cls_dir, "laboratorio", "guia.html")
    src = open(path).read()
    figure = ('<figure class="arch-figure">\n' + inline_svg +
              '\n<figcaption>Todos los componentes que despliega <code>template.yaml</code>.</figcaption>\n</figure>')
    # elimina figura previa si existe (idempotente)
    src = re.sub(r'<figure class="arch-figure">.*?</figure>\s*', '', src, flags=re.S)
    # inserta tras el <h2>Arquitectura</h2>
    m = re.search(r'(<section id="arquitectura">\s*<h2>[^<]*</h2>)', src)
    if not m:
        raise SystemExit(f"No encuentro la sección Arquitectura en {path}")
    src = src[:m.end()] + "\n      " + figure + "\n" + src[m.end():]
    open(path, "w").write(src)


def main():
    for cls_dir, fn in CLASSES.items():
        d = fn()
        svg_dir = os.path.join(ROOT, cls_dir, "laboratorio")
        with open(os.path.join(svg_dir, "arquitectura.svg"), "w") as f:
            f.write(d.svg_standalone())
        inject_into_guia(cls_dir, d.svg_inline())
        W, H = d.canvas()
        print(f"  {cls_dir}: arquitectura.svg ({W:.0f}x{H:.0f}) + inyectado en guia.html")
    print("OK")


if __name__ == "__main__":
    main()
