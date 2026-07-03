# Clase 5 — Alertas, respuesta automatizada y cierre end-to-end

> **Alertas accionables, auto-remediación y visualización unificada.**
>
> Clase 5 de 5 · Curso *Observabilidad y Monitoreo en AWS* · ⏱ ~2 horas · 🧪 Laboratorio incluido

Esta clase cierra el curso llevando la observabilidad hasta la **acción**: no solo detectar, sino
responder. Diseñamos **alarmas accionables** de Amazon CloudWatch (de métrica, compuestas y por
detección de anomalías), automatizamos la respuesta a incidentes con **Amazon EventBridge** hacia
**runbooks de SSM Automation** o **AWS Lambda**, notificamos por **Amazon SNS** (email, Slack o
PagerDuty) y consolidamos todo en un **dashboard de CloudWatch** unificado, con **Amazon Managed
Grafana** para vistas multi-fuente. Terminamos integrando el stack completo del curso —métricas,
logs, archivado, contenedores, alertas y dashboard— y validándolo al **simular un incidente** y
resolverlo, poniendo el foco en una estrategia de monitoreo apta para producción: umbrales
accionables, reducción de ruido, SLIs/SLOs y runbooks operativos.

## Objetivos

- Diseñar alertas accionables y reducir el ruido y la fatiga de alertas.
- Automatizar la respuesta a incidentes con EventBridge, Lambda y runbooks de SSM Automation.
- Consolidar la visualización con dashboards de CloudWatch y Amazon Managed Grafana.
- Cerrar el stack de observabilidad end-to-end y validarlo simulando y resolviendo un incidente.

## Módulos

1. **Alarmas de Amazon CloudWatch**
   - Alarmas de métrica, compuestas (*composite*) y por detección de anomalías.
   - Estados de alarma (`OK`, `ALARM`, `INSUFFICIENT_DATA`) y tratamiento de datos faltantes.
   - Acciones: SNS, Auto Scaling, acciones de EC2 y Systems Manager.
2. **Eventos y respuesta automatizada**
   - Amazon EventBridge (ex CloudWatch Events): reglas, patrones de eventos y buses.
   - Auto-remediación: EventBridge → AWS Lambda o runbooks de SSM Automation.
   - Notificaciones: SNS hacia email, Slack o PagerDuty; AWS Chatbot.
3. **Dashboards y visualización**
   - CloudWatch Dashboards: widgets, variables y vistas *cross-account/region*.
   - Amazon Managed Grafana para dashboards multi-fuente.
   - CloudWatch Investigations: análisis de causa raíz asistido por IA.
4. **Estrategia de monitoreo para producción**
   - Diseño de umbrales y alertas accionables; reducción de ruido y fatiga de alertas.
   - SLIs, SLOs y runbooks operativos.
   - Detección temprana de incidentes.
5. **Cierre end-to-end**
   - Integración de todo el stack: métricas, logs, archivado, contenedores, alertas y dashboard.

## Arquitectura del laboratorio

Una plantilla de CloudFormation cierra el stack completo y conecta la detección con la respuesta
automatizada. El flujo de auto-remediación queda así:

1. **CloudFormation** despliega el stack: alarmas, regla de EventBridge, runbook de SSM Automation,
   tópico SNS y dashboard.
2. Una **instancia EC2** genera **alto uso de CPU** (el incidente simulado).
3. La **alarma de métrica** de CPU cruza su umbral y pasa a estado `ALARM`. Junto a ella se crean una
   **alarma compuesta** (que agrupa varias señales con lógica `AND`/`OR`) y una **alarma por
   detección de anomalía** (que aprende la banda esperada de la métrica).
4. **EventBridge** captura el evento *CloudWatch Alarm State Change* mediante una **regla** con un
   **patrón** que filtra el paso a `ALARM`.
5. La regla dispara un **runbook de SSM Automation** que **remedia automáticamente** el incidente.
6. En paralelo, la alarma notifica al **tópico SNS**, que envía un **email** al equipo.
7. El **dashboard de CloudWatch** unificado muestra en una sola vista los widgets de **métricas**
   (CPU, estado de las alarmas) y de **logs**.
8. **Investigación:** se simula el incidente y se resuelve indagando con **Logs Insights**, **Athena**
   y el **service map**, y se documenta el **runbook operativo**.

```
EC2 (alto CPU) ──► Alarma (métrica) ──► EventBridge (regla+patrón) ──► SSM Automation (runbook remedia)
                        │
                        └──► SNS (email al equipo)
Alarma compuesta + Alarma de anomalía ─────────────────────────────► Dashboard unificado (métricas + logs)
Investigación: Logs Insights · Athena · service map ──────────────► causa raíz + runbook operativo
```

### Entregables del laboratorio

- Alarma de métrica + alarma compuesta + alarma por detección de anomalía.
- Regla de EventBridge que dispara un runbook de SSM Automation (auto-remediación).
- Tópico SNS con suscripción de email.
- Dashboard de CloudWatch unificado (widgets de métricas y logs).

## Servicios que se usan

| Servicio | Rol en la clase |
| --- | --- |
| **Amazon CloudWatch Alarms** | Convierte métricas en decisiones: crea la alarma de métrica sobre la CPU, la compuesta y la de detección de anomalía, y dispara las acciones (SNS y, vía evento, la remediación). |
| **Amazon EventBridge** | Bus de eventos: una regla con un patrón captura el cambio de la alarma a `ALARM` y enruta el evento hacia el runbook de SSM Automation. |
| **Amazon SNS** | Notificación *fan-out*: el tópico con suscripción de email avisa al equipo cuando la alarma se dispara (extensible a Slack o PagerDuty). |
| **AWS Lambda** | Alternativa de auto-remediación con lógica a medida cuando un runbook declarativo no alcanza. |
| **AWS Systems Manager** | SSM Automation ejecuta el runbook que remedia el incidente automáticamente; también permite documentar y versionar el runbook operativo. |
| **Amazon CloudWatch Dashboards** | Vista unificada: consolida widgets de métricas (CPU, estado de las alarmas) y de logs en una sola pantalla para operar. |
| **Amazon Managed Grafana** | Dashboards multi-fuente (CloudWatch, Prometheus y otras) cuando se necesita visualización avanzada o transversal. |
| **AWS Chatbot** | Lleva las notificaciones de SNS a canales de chat (Slack o Teams) para la respuesta del equipo. |
| **AWS CloudFormation** | Despliega todo el stack de la clase como infraestructura-como-código: alarmas, regla de EventBridge, runbook de SSM, tópico SNS y dashboard. |
| **AWS IAM** | Otorga los permisos mínimos: que EventBridge invoque la automatización, que el runbook actúe sobre la instancia y que SNS publique, sin credenciales estáticas. |

## Cómo usar

- **Presentación (deck):** abrí [`presentacion/index.html`](presentacion/index.html) en el navegador.
  Navegá con `←` / `→`, `O` para la vista general y `F` para pantalla completa. Funciona offline.
- **Laboratorio:**
  - Guía paso a paso: [`laboratorio/guia.html`](laboratorio/guia.html) — desde abrir la consola de
    AWS hasta desplegar, simular el incidente, verificar la remediación y limpiar.
  - Plantilla de CloudFormation: [`laboratorio/template.yaml`](laboratorio/template.yaml).
  - Recordá **eliminar el stack** al terminar para no incurrir en costos (el lab está diseñado para
    costar menos de USD 1).

## Escenario de investigación / troubleshooting

Simulá un incidente de **alto uso de CPU** en la instancia: la **alarma de métrica** pasa a `ALARM`,
**EventBridge** dispara el **runbook de SSM Automation** que remedia automáticamente, el **dashboard**
refleja la evolución y llega la **notificación por SNS**. Luego investigá la causa raíz con **Logs
Insights**, **Athena** y el **service map**, y documentá el **runbook operativo**. Errores frecuentes:
un patrón de EventBridge que no coincide con el evento de la alarma (la regla nunca se dispara), un rol
de IAM sin permiso para que EventBridge invoque la automatización o para que el runbook actúe sobre la
instancia, una suscripción de SNS sin confirmar (no llega el email), y una alarma compuesta o de
anomalía mal configurada que genera ruido o no detecta el incidente.

## 🖥️ Descargar la presentación (PPTX)

Además del deck HTML, la presentación está disponible en **PowerPoint**:

- [`presentacion/Observabilidad-AWS-Clase-5.pptx`](presentacion/Observabilidad-AWS-Clase-5.pptx) — formato 16:9, con notas del orador.

> Podés abrirlo en PowerPoint/Keynote o **importarlo a Google Slides** (Archivo → Importar presentación).
