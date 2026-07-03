# Clase 4 · Observabilidad de contenedores (ECS + Fargate)

> **Métricas, logs y trazas de cargas en contenedores.**
> De Container Insights y FireLens a la correlación entre infraestructura,
> servicio y traza para acelerar el diagnóstico y el análisis de causa raíz.

Cuarta de las cinco clases del programa **Observabilidad y Monitoreo en AWS**.
Cubre la observabilidad de cargas que corren en contenedores sobre **Amazon ECS**
y **AWS Fargate**: cómo recolectar métricas a nivel de clúster, servicio, tarea y
contenedor con **CloudWatch Container Insights** (estándar frente a enhanced
observability), qué cambia en **Fargate** al no tener acceso al host, cómo rutear
los logs de los contenedores a CloudWatch con el driver **`awslogs`** o con
**FireLens (Fluent Bit)**, y una introducción a APM con **ADOT**, **CloudWatch
Application Signals** y **AWS X-Ray** para correlacionar infraestructura ↔
servicio ↔ traza. Todo definido como código en CloudFormation.

---

## Objetivos

- Monitorear cargas en contenedores sobre **Amazon ECS** y **AWS Fargate**.
- Recolectar **métricas y logs** de contenedores a nivel de clúster, servicio, tarea y contenedor.
- Rutear los logs de contenedores a CloudWatch con el driver **`awslogs`** o **FireLens**.
- Introducir **APM** con ADOT, CloudWatch Application Signals y AWS X-Ray.
- **Correlacionar** infraestructura, servicios y trazas para acelerar el diagnóstico.
- Definir el clúster, el servicio Fargate y FireLens **como código** en CloudFormation.

---

## Módulos

1. **Container Insights** — Container Insights estándar vs. enhanced observability para Amazon ECS; métricas a nivel de clúster, servicio, tarea y contenedor; dashboards curados y seguimiento de despliegues (deployment tracking).
2. **Particularidades de AWS Fargate** — qué cambia al no tener acceso al host; qué métricas quedan disponibles para las tareas en Fargate.
3. **Logs de contenedores** — el driver `awslogs` para enviar la salida estándar a CloudWatch Logs; FireLens (Fluent Bit) para rutear logs a CloudWatch, S3, OpenSearch o terceros.
4. **APM y correlación (introducción)** — AWS Distro for OpenTelemetry (ADOT) como sidecar o collector; CloudWatch Application Signals con auto-instrumentación e integración con AWS X-Ray; correlación infraestructura ↔ servicio ↔ traza para el análisis de causa raíz.
5. **Todo como código** — el clúster ECS, el servicio Fargate con Container Insights y la configuración de FireLens definidos en CloudFormation.

---

## Servicios de la clase

| Servicio | Rol en la clase |
| --- | --- |
| **Amazon ECS** | Orquestador de contenedores: define el clúster, la task definition y el servicio que mantiene la tarea en ejecución. |
| **AWS Fargate** | Motor de cómputo serverless: ejecuta la tarea sin que administres ni accedas a las instancias EC2 subyacentes. |
| **CloudWatch Container Insights** | Métricas y dashboards: recolecta CPU, memoria y más a nivel de clúster, servicio, tarea y contenedor; se habilita en modo enhanced. |
| **Amazon CloudWatch Logs** | Destino de los logs de los contenedores, para consultarlos y correlacionarlos con las métricas. |
| **AWS FireLens (Fluent Bit)** | Router de logs: sidecar que rutea la salida de los contenedores a CloudWatch, S3, OpenSearch o terceros. |
| **AWS Distro for OpenTelemetry (ADOT)** | Recolección de métricas y trazas: corre como sidecar o collector y exporta a CloudWatch y X-Ray. |
| **CloudWatch Application Signals** | APM administrado: auto-instrumenta la aplicación, publica métricas de request y define SLOs. |
| **AWS X-Ray** | Trazas distribuidas: reconstruye el request punta a punta y alimenta el mapa de servicios. |
| **AWS CloudFormation** | Infraestructura como código: una única plantilla despliega el clúster, el servicio y la configuración de logs de forma reproducible. |
| **AWS IAM** | Roles de la tarea: el execution role descarga la imagen y escribe logs; el task role otorga los permisos de la app y de los sidecars. |

---

## Arquitectura del laboratorio

```
Amazon ECS + AWS Fargate (task + contenedor de aplicación)
        │
        ├──[Container Insights (enhanced)]──> CloudWatch
        │        métricas por clúster / servicio / tarea / contenedor + dashboards curados
        │
        ├──[FireLens · Fluent Bit sidecar]──> CloudWatch Logs
        │        logs del contenedor, listos para correlacionar con las métricas
        │
        └──[ADOT sidecar/collector]──> AWS X-Ray + CloudWatch Application Signals
                 trazas y métricas de request para el análisis de causa raíz

Correlación infraestructura ↔ servicio ↔ traza:
   pico de CPU/memoria (Container Insights) + logs del contenedor (CloudWatch Logs)
   + traza del mismo intervalo (X-Ray) ──> causa raíz

Todo el conjunto se despliega desde una única plantilla de CloudFormation.
```

**Flujo resumido:** un servicio de ECS corre una tarea sobre Fargate con un
contenedor de aplicación de ejemplo. Container Insights, habilitado en modo
enhanced a nivel de clúster, publica en CloudWatch las métricas por clúster,
servicio, tarea y contenedor, con dashboards curados. Los logs del contenedor se
rutean a CloudWatch Logs con FireLens/Fluent Bit (o con el driver `awslogs`). Como
introducción a APM, ADOT recolecta métricas y trazas y las envía a X-Ray y a
CloudWatch Application Signals. En el diagnóstico, se correlaciona el pico de
CPU/memoria de una tarea con los logs de su contenedor y con la traza del mismo
intervalo para hallar la causa raíz. Todo se despliega desde una única plantilla
de CloudFormation.

---

## Escenario de investigación

El escenario de troubleshooting explora Container Insights **a nivel de tarea y
contenedor** (CPU y memoria): se **fuerzan reinicios del contenedor** y se
**correlaciona el pico de métricas con los logs del contenedor** para hallar la
causa del reinicio.

---

## Cómo usar

- **Presentación:** abrí [`presentacion/index.html`](presentacion/index.html) en el navegador
  (funciona offline con `file://`). Navegá con las flechas `←` `→`, `O` para la
  vista general y `F` para pantalla completa.
- **Laboratorio:** seguí la guía paso a paso en [`laboratorio/guia.html`](laboratorio/guia.html)
  y desplegá la plantilla [`laboratorio/template.yaml`](laboratorio/template.yaml).

### Entregables del laboratorio

- **Clúster ECS** con Container Insights (enhanced) habilitado.
- **Task definition Fargate** con un contenedor de aplicación de ejemplo.
- **Logs enviados a CloudWatch** con el driver `awslogs` o un sidecar FireLens/Fluent Bit.
- **Servicio ECS** con la tarea desplegada.
- **Visualización de métricas** por tarea y contenedor en Container Insights.

> **Nota de costo:** el laboratorio usa recursos de bajo costo (Fargate con CPU y
> memoria mínimas, una sola tarea). Acordate de **eliminar el stack** al terminar
> para no dejar tareas ni log groups facturando.

---

## Novedades relevantes

- **Container Insights con enhanced observability para Amazon ECS** suma métricas
  detalladas por tarea y contenedor y dashboards curados, por encima del modo
  estándar (agregado a clúster y servicio).
- El **deployment tracking** de Container Insights correlaciona cada despliegue
  con las métricas para detectar regresiones apenas ocurre un rollout.
- En **Fargate** no hay acceso al host: las métricas se observan a nivel de tarea
  y contenedor, no del sistema operativo del host.
- **FireLens** usa Fluent Bit como router de logs y permite multiplexar destinos
  (CloudWatch, S3, OpenSearch, terceros) y transformar los eventos.
- **CloudWatch Application Signals** auto-instrumenta la aplicación con
  OpenTelemetry (vía **ADOT**) y se integra con **AWS X-Ray** para las trazas.

---

## Navegación del curso

| | Clase | Foco |
| --- | --- | --- |
| ← | [Clase 3 · Archivado, ciclo de vida y explotación con Athena](../clase-3-archivado-lifecycle-athena/) | Archivar y explotar con SQL |
| **▸** | **Clase 4 · Observabilidad de contenedores (ECS/Fargate)** | **Contenedores** |
| → | [Clase 5 · Alertas y respuesta automatizada](../clase-5-alertas-respuesta-automatizada/) | Alertas y automatización |
