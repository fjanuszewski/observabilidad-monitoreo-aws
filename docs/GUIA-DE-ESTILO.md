# Guía de estilo y estándares del curso

> Documento de referencia para mantener **coherencia total** entre las 5 clases.
> Toda clase debe respetar esta guía. Ante la duda, copiar las plantillas de
> [`docs/_plantilla/`](./_plantilla/).

## Estructura de cada clase

```
clase-N-<slug>/
├── README.md                     # Portada de la clase: objetivos, módulos, arquitectura, cómo usar
├── presentacion/
│   └── index.html                # Deck (usa ../../assets/css/slides.css + ../../assets/js/slides.js)
└── laboratorio/
    ├── README.md                 # Resumen del lab: qué despliega, requisitos, deploy rápido
    ├── template.yaml             # CloudFormation (cfn-lint limpio)
    ├── parameters.example.json   # Parámetros de ejemplo
    ├── troubleshooting.md        # Problemas frecuentes + escenarios de exploración
    └── guia.html                 # Guía paso a paso (usa ../../assets/css/guide.css + guide.js)
```

Todos los HTML están **2 niveles** por debajo de la raíz, por lo que las rutas a
assets son siempre `../../assets/...`.

## Identidad visual (no negociable)

- **Paleta:** navy `#16294a` / `#1e3a63`, acento naranja `#e8792b`. Definida en el CSS; **no** usar estilos inline de color.
- **Tipografía:** stack de sistema (definido en el CSS). No cargar fuentes externas (las guías/decks se abren offline con `file://`).
- **Íconos de servicios:** SIEMPRE desde `assets/img/services/<slug>.svg`. Ver el catálogo abajo. No inventar rutas ni usar PNG externos.
- **Logo del curso:** `assets/img/logo-curso.svg`.
- Todo debe funcionar **offline** (sin CDNs, sin `fetch`, sin fuentes remotas).

## Presentaciones (`presentacion/index.html`)

- Copiar la estructura de [`_plantilla/presentacion.plantilla.html`](./_plantilla/presentacion.plantilla.html).
- **10 a 14 slides.** Secuencia recomendada: portada → objetivos → (por cada módulo del PDF: 1 divisor de sección + 1–3 slides de contenido/servicio) → diagrama de arquitectura del lab → slide de laboratorio → cierre.
- Cada `.slide` empieza con la barra `.slide-top` (marca + `Clase N`). El contador lo inyecta el JS.
- Tipos disponibles: `.slide--title`, `.slide--section`, `.slide--service`, y contenido normal. Componentes: `.svc-grid`, `.cards`, `.arch`+`.flow`+`.node`, `.callout`, `.code`, `.checklist`, tablas, `.pill`.
- **Densidad:** máximo ~6 bullets o ~3 cards por slide. Preferir varias slides livianas a una recargada (evita overflow).
- Cada servicio mencionado en el PDF de esa clase debe tener su ícono y al menos una explicación de "qué es / para qué / cómo encaja en el lab".
- Incluir SIEMPRE un diagrama de arquitectura del laboratorio con `.arch` + `.flow` + `.node` (íconos reales + flechas `→`).

## Guías de laboratorio (`laboratorio/guia.html`)

- Copiar la estructura de [`_plantilla/guia.plantilla.html`](./_plantilla/guia.plantilla.html).
- Recorrido **desde abrir la consola de AWS hasta terminar y limpiar**. Secciones: Introducción → Arquitectura → Requisitos → Desplegar → Verificar → Explorar/experimentar → Troubleshooting → Limpieza.
- Cada acción es un `.step` (numeración automática). Usar `.console-path` para la navegación en la consola y `.checkpoint` tras cada hito.
- Mostrar SIEMPRE la doble vía: **consola** (paso a paso) y **CLI** (bloque `.code` con botón copiar).
- Cerrar SIEMPRE con **Limpieza** (borrar el stack) y una nota de **costo**.

## CloudFormation (`laboratorio/template.yaml`)

Requisitos obligatorios:

1. **`cfn-lint` limpio** (0 errores). Validar con:
   ```bash
   export PATH="$HOME/Library/Python/3.9/bin:$PATH"
   cfn-lint laboratorio/template.yaml
   ```
2. **Formato YAML** con `AWSTemplateFormatVersion`, `Description`, `Parameters`, `Resources`, `Outputs` y `Metadata` (`AWS::CloudFormation::Interface`) cuando aporte.
3. **Auto-contenido y de bajo costo:** cada lab se despliega solo (crea lo mínimo que necesita). Nada de tipos caros: EC2 `t3.micro`, disco `gp3` chico, single-AZ. Costo objetivo del lab: < USD 1.
4. **AMI:** nunca hardcodear IDs. Usar parámetro
   `AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>` con default
   `/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64`.
5. **IAM:** rol de instancia con las managed policies mínimas
   (`CloudWatchAgentServerPolicy`, `AmazonSSMManagedInstanceCore`). Declarar
   `CAPABILITY_NAMED_IAM` en la guía si se nombran roles.
6. **Región por defecto:** `us-east-1` (documentado, pero sin recursos atados a una región fija por ID).
7. **Tags** en los recursos: `Project = observabilidad-monitoreo-aws`, `Clase = N`.
8. **Borrable:** sin `DeletionPolicy: Retain`. Si un bucket S3 puede quedar con objetos, documentar en la limpieza que hay que vaciarlo antes de borrar el stack.
9. **Outputs** útiles (nombres de recursos, comandos de verificación o enlaces de consola).
10. Comentarios en español explicando cada bloque relevante.

## Tono y lenguaje

- Español rioplatense neutro, claro y práctico. Segunda persona ("vas a desplegar…").
- Términos técnicos e identificadores de código quedan en su forma original (CloudWatch, `PutMetricData`, log group, etc.).
- Correctitud ortográfica completa (tildes, ñ).

## Catálogo de íconos disponibles (`assets/img/services/`)

`adot`, `application-signals`, `athena`, `autoscaling`, `aws-cloud`, `chatbot`,
`cloudformation`, `cloudwatch`, `cloudwatch-alarms`, `cloudwatch-dashboards`,
`cloudwatch-logs`, `container-insights`, `ec2`, `ecs`, `eventbridge`, `fargate`,
`firehose`, `firelens`, `glacier`, `glue`, `grafana`, `iam`, `kinesis`, `kms`,
`lambda`, `s3`, `sns`, `systems-manager`, `vpc`, `xray`.

Si falta un ícono, reutilizar el más cercano de la misma familia (no romper el estilo con imágenes externas).
