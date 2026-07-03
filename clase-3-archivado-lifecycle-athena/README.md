# Clase 3 · Archivado, ciclo de vida y explotación con Athena

> **Archivar económicamente y explotar logs con SQL.**
> De CloudWatch Logs a un data lake en Amazon S3, y de ahí a una investigación de
> seguridad en Amazon Athena.

Tercera de las cinco clases del programa **Observabilidad y Monitoreo en AWS**.
Cubre la fase de **archivado económico** y **explotación forense** de logs:
cuándo retener en CloudWatch Logs frente a archivar en S3 y en las clases de
almacenamiento en frío (Glacier), cómo mover logs a S3 en near real-time con un
subscription filter hacia Amazon Data Firehose (con conversión a Parquet,
compresión y particionado por fecha), cómo diseñar el ciclo de vida (Lifecycle)
para transicionar a Glacier y Deep Archive, y cómo explotar esos logs con SQL en
Amazon Athena (con AWS Glue Data Catalog y partition projection). Todo definido
como código en CloudFormation.

---

## Objetivos

- Archivar logs a largo plazo de forma **económica** y conforme a normativa.
- Decidir cuándo retener en **CloudWatch Logs**, cuándo archivar en **S3** y cuándo en **Glacier**.
- Diseñar el **ciclo de vida** y la "rotación" de los datos con S3 Lifecycle.
- Explotar los logs con **SQL en Amazon Athena** para troubleshooting e investigación de seguridad.
- Definir el pipeline completo **como código** en una única plantilla de CloudFormation.

---

## Módulos

1. **Estrategia de archivado y costo** — cuándo retener en CloudWatch Logs, cuándo archivar en S3 y cuándo en Glacier; consideraciones de cumplimiento y retención regulatoria.
2. **Streaming de logs a Amazon S3** — subscription filter → Amazon Data Firehose → S3 en near real-time; export tasks (batch) para cargas puntuales; transformación a Parquet, compresión y particionado por fecha.
3. **Ciclo de vida y rotación en S3** — S3 Lifecycle hacia Glacier y Glacier Deep Archive; la "rotación" en AWS como retención, particionado y tiering (no es logrotate tradicional).
4. **Explotación de datos con Amazon Athena** — Athena sobre CloudTrail, VPC Flow Logs y logs de balanceadores/aplicación; tablas y SerDe (JSON, Grok, Parquet) con Glue Data Catalog; particionado y partition projection; cuándo usar Logs Insights y cuándo Athena.
5. **Todo como código** — el delivery stream de Firehose, el bucket S3 con lifecycle y los recursos de Glue/Athena definidos en CloudFormation.

---

## Servicios de la clase

| Servicio | Rol en la clase |
| --- | --- |
| **Amazon CloudWatch Logs** | Origen del pipeline: un subscription filter empuja los eventos (por ejemplo de CloudTrail) hacia Firehose en near real-time. |
| **Amazon Data Firehose** | Corazón del archivado: hace buffering, convierte a Parquet con el esquema de Glue, comprime y escribe en S3 particionado por fecha. |
| **Amazon S3** | Data lake de logs archivados: destino de Firehose, base del particionado por fecha y fuente que consulta Athena. |
| **Amazon S3 Glacier** | Archivado frío de bajo costo: destino de la regla de Lifecycle para retención regulatoria a largo plazo. |
| **AWS Glue Data Catalog** | Metastore de Athena: base de datos y tabla que describen los logs en S3 con su SerDe y particiones. |
| **Amazon Athena** | Explotación con SQL serverless: un workgroup con ubicación de resultados ejecuta la consulta de investigación de seguridad. |
| **AWS CloudFormation** | Infraestructura como código: una única plantilla despliega todo el pipeline de forma reproducible. |
| **AWS IAM** | Cadena de confianza: roles que habilitan cada salto (Logs → Firehose, Firehose → S3/Glue, Athena → S3/Glue) con least privilege. |

---

## Arquitectura del laboratorio

```
CloudWatch Logs ──[subscription filter, near real-time]──> Amazon Data Firehose
                                                                   │
                              buffering + Parquet + compresión + particionado por fecha
                                                                   ▼
                                                            Amazon S3 (data lake)
                                                          prefijos year=/month=/day=
                                                                   │
                                            [regla de S3 Lifecycle, ej. tras 30 días]
                                                                   ▼
                                                    S3 Glacier / Deep Archive (frío)

AWS Glue Data Catalog (Database + Table + SerDe + particiones) describe los datos en S3
                                                                   │
Amazon Athena (Workgroup + Query Result Location) ──[lee esquema de Glue, escanea S3
   filtrando por partición de fecha]──> consulta de investigación:
   eventName = 'AuthorizeSecurityGroupIngress' abriendo el puerto 22/3389
                                                                   │
                                                       resultados → S3 (query location)

IAM roles enlazan cada salto · Todo el conjunto se despliega desde una plantilla de CloudFormation.
```

**Flujo resumido:** CloudTrail (o la app) genera eventos que llegan a un log group
de CloudWatch Logs. Un subscription filter los empuja a un delivery stream de
Firehose, que hace buffering, los convierte a Parquet usando el esquema de Glue,
los comprime y los escribe en el bucket S3 particionados por fecha. Una regla de
S3 Lifecycle transiciona esos objetos a Glacier para el archivado frío. En
paralelo, el Glue Data Catalog describe los datos y Amazon Athena los explota con
SQL desde un workgroup, escribiendo los resultados en su ubicación de resultados
en S3. Los roles de IAM enlazan cada salto y todo se despliega desde una única
plantilla de CloudFormation.

---

## Escenario de investigación

La consulta de cierre resuelve una investigación real sobre eventos de CloudTrail
archivados: **detectar quién ejecutó `AuthorizeSecurityGroupIngress` abriendo un
puerto sensible** (por ejemplo 22 o 3389) **y cuándo**, filtrando por
`eventName` y por la columna de partición de fecha para escanear lo mínimo.

---

## Cómo usar

- **Presentación:** abrí [`presentacion/index.html`](presentacion/index.html) en el navegador
  (funciona offline con `file://`). Navegá con las flechas `←` `→`, `O` para la
  vista general y `F` para pantalla completa.
- **Laboratorio:** seguí la guía paso a paso en [`laboratorio/guia.html`](laboratorio/guia.html)
  y desplegá la plantilla [`laboratorio/template.yaml`](laboratorio/template.yaml).

### Entregables del laboratorio

- **Delivery stream** de Amazon Data Firehose.
- **Bucket S3** con particionado por fecha y regla de lifecycle a Glacier.
- **Base de datos y tabla** en AWS Glue Data Catalog.
- **Workgroup de Athena** con ubicación de resultados.
- **Consulta SQL** de investigación de seguridad.

> **Nota de costo:** el laboratorio usa recursos serverless de bajo costo y clases
> de almacenamiento económicas. Acordate de **vaciar el bucket S3** antes de borrar
> el stack y de eliminar el stack al terminar para no dejar recursos facturando.

---

## Novedades relevantes

- **Amazon Data Firehose** es el nombre actual del servicio antes conocido como Amazon Kinesis Data Firehose (rebranding de 2024).
- Firehose soporta **decompresión** de CloudWatch Logs (llegan gzip por defecto) y luego **record format conversion** a Parquet/ORC para destino S3.
- **Dynamic partitioning** permite particionar por claves dentro de los datos; para logs de CloudWatch requiere habilitar *Multi record deaggregation*.
- **Athena engine v3** (basado en Trino) es la versión actual del motor, con mejor performance y más funciones SQL.
- **Partition projection** elimina la gestión manual de particiones y es la práctica recomendada para tablas de CloudTrail de alto volumen.
- **S3 Glacier Instant Retrieval** ofrece acceso en milisegundos, un punto intermedio entre S3 Standard-IA y las clases Glacier con recuperación diferida.

---

## Navegación del curso

| | Clase | Foco |
| --- | --- | --- |
| ← | [Clase 2 · Logs, recolección y retención](../clase-2-logs-recoleccion-retencion/) | Recolectar y retener logs |
| **▸** | **Clase 3 · Archivado, ciclo de vida y explotación con Athena** | **Archivar y explotar con SQL** |
| → | [Clase 4 · Observabilidad de contenedores (ECS/Fargate)](../clase-4-observabilidad-contenedores-ecs-fargate/) | Contenedores |

## 🖥️ Descargar la presentación (PPTX)

Además del deck HTML, la presentación está disponible en **PowerPoint**:

- [`presentacion/Observabilidad-AWS-Clase-3.pptx`](presentacion/Observabilidad-AWS-Clase-3.pptx) — formato 16:9, con notas del orador.

> Podés abrirlo en PowerPoint/Keynote o **importarlo a Google Slides** (Archivo → Importar presentación).
