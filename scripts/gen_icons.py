#!/usr/bin/env python3
"""Genera un set consistente de iconos SVG de servicios AWS para el workshop.

Cada icono es un badge cuadrado con esquinas redondeadas, gradiente por
categoria y un glifo blanco de linea. El objetivo es coherencia visual entre
las 5 clases, no replicar el branding oficial de AWS (se evitan marcas
registradas y se garantiza un look uniforme).
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "services")
os.makedirs(OUT, exist_ok=True)


def darken(hex_color, factor=0.72):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, int(c * factor)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


# Paleta por categoria (coherente e internamente consistente)
CAT = {
    "compute":    "#E8730C",
    "containers": "#EC8B2B",
    "storage":    "#3F8624",
    "analytics":  "#7A3FF2",
    "mgmt":       "#C7157B",   # familia observabilidad (color heroe del curso)
    "appint":     "#2E73B8",
    "security":   "#C7303C",
    "devtools":   "#1CA79E",
    "networking": "#5B34C4",
    "generic":    "#48566B",
}

# glifo dibujado en un lienzo 0..40 (se traslada a translate(20,20))
SERVICES = {
    # slug: (label, categoria, glifo)
    "cloudwatch": ("Amazon CloudWatch", "mgmt",
        '<path d="M5 29 A16 16 0 0 1 35 29"/><line x1="20" y1="29" x2="30" y2="15"/><circle cx="20" cy="29" r="2.6" fill="#fff"/>'),
    "cloudwatch-logs": ("CloudWatch Logs", "mgmt",
        '<rect x="9" y="4" width="22" height="32" rx="2"/><line x1="14" y1="13" x2="26" y2="13"/><line x1="14" y1="20" x2="26" y2="20"/><line x1="14" y1="27" x2="22" y2="27"/>'),
    "cloudwatch-alarms": ("CloudWatch Alarms", "mgmt",
        '<path d="M11 27 a9 11 0 0 1 18 0 z"/><line x1="8" y1="27" x2="32" y2="27"/><line x1="20" y1="6" x2="20" y2="10"/><circle cx="20" cy="32" r="2.4" fill="#fff"/>'),
    "cloudwatch-dashboards": ("CloudWatch Dashboards", "mgmt",
        '<rect x="6" y="6" width="12" height="10" rx="1"/><rect x="22" y="6" width="12" height="10" rx="1"/><rect x="6" y="20" width="12" height="14" rx="1"/><rect x="22" y="20" width="12" height="14" rx="1"/>'),
    "application-signals": ("CloudWatch Application Signals", "mgmt",
        '<line x1="8" y1="34" x2="8" y2="27"/><line x1="16" y1="34" x2="16" y2="20"/><line x1="24" y1="34" x2="24" y2="13"/><line x1="32" y1="34" x2="32" y2="6"/>'),
    "container-insights": ("Container Insights", "mgmt",
        '<rect x="5" y="14" width="30" height="16" rx="1"/><line x1="13" y1="14" x2="13" y2="30"/><line x1="21" y1="14" x2="21" y2="30"/><line x1="29" y1="14" x2="29" y2="30"/><polyline points="6,10 14,4 22,8 34,2"/>'),
    "cloudformation": ("AWS CloudFormation", "mgmt",
        '<rect x="5" y="5" width="13" height="13" rx="1"/><rect x="22" y="5" width="13" height="13" rx="1"/><rect x="13" y="22" width="14" height="13" rx="1"/>'),
    "systems-manager": ("AWS Systems Manager", "mgmt",
        '<circle cx="20" cy="20" r="9"/><circle cx="20" cy="20" r="3" fill="#fff"/><line x1="20" y1="4" x2="20" y2="9"/><line x1="20" y1="31" x2="20" y2="36"/><line x1="4" y1="20" x2="9" y2="20"/><line x1="31" y1="20" x2="36" y2="20"/><line x1="9" y1="9" x2="12" y2="12"/><line x1="28" y1="28" x2="31" y2="31"/><line x1="31" y1="9" x2="28" y2="12"/><line x1="12" y1="28" x2="9" y2="31"/>'),
    "grafana": ("Amazon Managed Grafana", "mgmt",
        '<circle cx="20" cy="20" r="15"/><polyline points="9,25 16,17 22,21 31,10" stroke="#fff"/>'),
    "ec2": ("Amazon EC2", "compute",
        '<rect x="9" y="9" width="22" height="22" rx="1"/><rect x="16" y="16" width="8" height="8" fill="#fff"/><line x1="15" y1="9" x2="15" y2="4"/><line x1="25" y1="9" x2="25" y2="4"/><line x1="15" y1="36" x2="15" y2="31"/><line x1="25" y1="36" x2="25" y2="31"/><line x1="4" y1="15" x2="9" y2="15"/><line x1="4" y1="25" x2="9" y2="25"/><line x1="31" y1="15" x2="36" y2="15"/><line x1="31" y1="25" x2="36" y2="25"/>'),
    "lambda": ("AWS Lambda", "compute",
        '<path d="M11 34 L21 8 L29 8 M20 20 L29 34"/>'),
    "autoscaling": ("EC2 Auto Scaling", "compute",
        '<path d="M6 20 A14 14 0 0 1 30 11"/><polyline points="24,8 31,10 29,17"/><path d="M34 20 A14 14 0 0 1 10 29"/><polyline points="16,32 9,30 11,23"/>'),
    "ecs": ("Amazon ECS", "containers",
        '<rect x="5" y="12" width="30" height="18" rx="1"/><line x1="13" y1="12" x2="13" y2="30"/><line x1="20" y1="12" x2="20" y2="30"/><line x1="27" y1="12" x2="27" y2="30"/>'),
    "fargate": ("AWS Fargate", "containers",
        '<rect x="4" y="6" width="32" height="28" rx="3" stroke-dasharray="4 3"/><rect x="12" y="16" width="16" height="12" rx="1"/><line x1="18" y1="16" x2="18" y2="28"/><line x1="24" y1="16" x2="24" y2="28"/>'),
    "firelens": ("FireLens / Fluent Bit", "containers",
        '<path d="M20 4 C25 12 30 15 30 23 a10 10 0 0 1 -20 0 c0 -5 3 -8 5 -12 c1 4 3 5 4 8 c1 -4 1 -8 1 -15 z"/>'),
    "s3": ("Amazon S3", "storage",
        '<path d="M9 11 L31 11 L28 34 L12 34 Z"/><ellipse cx="20" cy="11" rx="11" ry="3.2"/>'),
    "glacier": ("S3 Glacier", "storage",
        '<line x1="20" y1="4" x2="20" y2="36"/><line x1="6" y1="12" x2="34" y2="28"/><line x1="34" y1="12" x2="6" y2="28"/><path d="M20 4 l-3 4 M20 4 l3 4 M20 36 l-3 -4 M20 36 l3 -4"/>'),
    "athena": ("Amazon Athena", "analytics",
        '<rect x="9" y="6" width="22" height="4" rx="1"/><rect x="9" y="31" width="22" height="4" rx="1"/><line x1="14" y1="10" x2="14" y2="31"/><line x1="20" y1="10" x2="20" y2="31"/><line x1="26" y1="10" x2="26" y2="31"/>'),
    "glue": ("AWS Glue", "analytics",
        '<path d="M7 9 h9 a4 4 0 0 1 8 0 h9 v9 a4 4 0 0 0 0 8 v9 h-9 a4 4 0 0 0 -8 0 h-9 v-9 a4 4 0 0 1 0 -8 z"/>'),
    "firehose": ("Amazon Data Firehose", "analytics",
        '<path d="M5 7 L35 7 L24 21 L24 35 L16 30 L16 21 Z"/>'),
    "kinesis": ("Amazon Kinesis", "analytics",
        '<path d="M4 14 C12 6 16 22 24 14 S34 6 36 14"/><path d="M4 26 C12 18 16 34 24 26 S34 18 36 26"/>'),
    "eventbridge": ("Amazon EventBridge", "appint",
        '<path d="M22 4 L9 23 L18 23 L16 36 L31 15 L21 15 Z" fill="#fff" stroke="none"/>'),
    "sns": ("Amazon SNS", "appint",
        '<circle cx="10" cy="20" r="3.5" fill="#fff"/><circle cx="31" cy="9" r="3" fill="#fff"/><circle cx="33" cy="20" r="3" fill="#fff"/><circle cx="31" cy="31" r="3" fill="#fff"/><line x1="12" y1="18" x2="29" y2="10"/><line x1="14" y1="20" x2="30" y2="20"/><line x1="12" y1="22" x2="29" y2="30"/>'),
    "chatbot": ("AWS Chatbot", "appint",
        '<path d="M6 8 h28 a2 2 0 0 1 2 2 v14 a2 2 0 0 1 -2 2 h-14 l-8 6 v-6 h-6 a2 2 0 0 1 -2 -2 v-14 a2 2 0 0 1 2 -2 z"/><circle cx="14" cy="17" r="1.6" fill="#fff"/><circle cx="20" cy="17" r="1.6" fill="#fff"/><circle cx="26" cy="17" r="1.6" fill="#fff"/>'),
    "kms": ("AWS KMS", "security",
        '<circle cx="14" cy="14" r="7"/><line x1="18.5" y1="18.5" x2="33" y2="33"/><line x1="27" y1="27" x2="31" y2="23"/><line x1="31" y1="31" x2="35" y2="27"/>'),
    "iam": ("AWS IAM", "security",
        '<path d="M20 4 L34 10 V21 C34 29 28 34 20 36 C12 34 6 29 6 21 V10 Z"/><circle cx="20" cy="17" r="4" fill="#fff"/><path d="M13 29 a7 7 0 0 1 14 0" fill="#fff" stroke="none"/>'),
    "xray": ("AWS X-Ray", "devtools",
        '<circle cx="16" cy="16" r="9"/><line x1="22.5" y1="22.5" x2="34" y2="34"/><circle cx="16" cy="16" r="2.4" fill="#fff"/><circle cx="30" cy="8" r="2" fill="#fff"/><circle cx="34" cy="18" r="2" fill="#fff"/>'),
    "adot": ("AWS Distro for OpenTelemetry", "devtools",
        '<polygon points="20,4 33,12 33,28 20,36 7,28 7,12"/><circle cx="20" cy="20" r="5" fill="#fff"/><line x1="20" y1="4" x2="20" y2="10"/><line x1="33" y1="12" x2="27" y2="16"/>'),
    "vpc": ("Amazon VPC", "networking",
        '<rect x="4" y="8" width="32" height="24" rx="4" stroke-dasharray="4 3"/><rect x="9" y="15" width="9" height="9" rx="1"/><rect x="22" y="15" width="9" height="9" rx="1"/><line x1="18" y1="19" x2="22" y2="19"/>'),
    "aws-cloud": ("AWS Cloud", "generic",
        '<path d="M13 30 h16 a7 7 0 0 0 1 -14 a10 10 0 0 0 -19 2 a6.5 6.5 0 0 0 2 12 z"/>'),
}

BADGE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="80" height="80" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="grad_{slug}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="1" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="76" height="76" rx="16" fill="url(#grad_{slug})"/>
  <g fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" transform="translate(20,20)">
    {glyph}
  </g>
</svg>
'''

count = 0
for slug, (label, cat, glyph) in SERVICES.items():
    c1 = CAT[cat]
    c2 = darken(c1)
    svg = BADGE.format(label=label, slug=slug.replace("-", "_"), c1=c1, c2=c2, glyph=glyph)
    with open(os.path.join(OUT, f"{slug}.svg"), "w") as f:
        f.write(svg)
    count += 1

print(f"Generados {count} iconos en {os.path.relpath(OUT)}")
print(",".join(sorted(SERVICES.keys())))
