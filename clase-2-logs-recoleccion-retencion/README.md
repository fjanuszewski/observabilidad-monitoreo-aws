<div align="center">
  <img src="../assets/img/logo-curso.svg" width="88" alt="Observabilidad y Monitoreo en AWS">
  <h1>Clase 2 · Logs: recolección, lectura y retención</h1>
  <p><strong>Centralizar, consultar y proteger los logs para troubleshooting.</strong></p>
  <p>
    <img alt="Clase" src="https://img.shields.io/badge/clase-2%20de%205-e8792b">
    <img alt="Servicios" src="https://img.shields.io/badge/servicios-CloudWatch%20Logs%20·%20KMS-16294a">
    <img alt="Laboratorio" src="https://img.shields.io/badge/laboratorio-CloudFormation-2f9e44">
  </p>
</div>

---

Esta clase se centra en el **pilar de logs** de la observabilidad: cómo
centralizar logs de aplicaciones y servicios en **Amazon CloudWatch Logs**,
consultarlos y analizarlos para *troubleshooting* con **Logs Insights** y
**Live Tail**, y convertirlos en señales accionables mediante **metric filters**,
**alarmas** y **subscription filters**. Además cubrimos el ciclo de vida del
dato: definir la **retención** por log group (la rotación lógica en la nube),
**enmascarar** datos sensibles con data protection y **cifrar** con **KMS**.
Todo se declara como código en **CloudFormation** para que log groups, filtros y
alarmas sean reproducibles.

## 🎯 Objetivos

- Centralizar los logs en Amazon CloudWatch Logs.
- Consultar y analizar logs para tareas de *troubleshooting*.
- Generar métricas y alarmas a partir de los logs.
- Gestionar la retención (rotación) y proteger datos sensibles.

## 📦 Módulos

1. **Amazon CloudWatch Logs: conceptos y recolección** — log groups, log streams y
   log events; fuentes de logs (agente de CloudWatch, SDK y servicios nativos como
   Lambda, API Gateway, VPC Flow Logs, ELB y Route 53); clases de log Standard vs
   Infrequent Access para optimizar costos.
2. **Lectura y análisis de logs** — CloudWatch Logs Insights (lenguaje de consulta),
   Live Tail (streaming en vivo) y detección de anomalías y análisis de patrones.
3. **De logs a métricas y alarmas** — *metric filters* para generar métricas desde
   patrones en los logs, alarmas derivadas de logs (contar errores y alertar) y
   *subscription filters* para rutear logs hacia otros destinos.
4. **Retención, rotación y protección** — política de retención por log group
   (de 1 día a 10 años o indefinida), enmascaramiento de datos sensibles
   (data protection) y cifrado de logs con AWS KMS.
5. **Todo como código** — definir log groups con retención, metric filters y
   alarmas en CloudFormation.

## 🗺️ Arquitectura del laboratorio

La aplicación corre en una instancia **EC2** con el **agente unificado de
CloudWatch**, que publica los logs (`PutLogEvents`, vía rol IAM) en un
**log group** con retención definida (y cifrado KMS / data protection
opcionales). Sobre ese log group se arma el pipeline:

```
EC2 + Agent ──▶ Log group ──▶ Métrica (metric filter) ──▶ Alarma ──▶ SNS
 PutLogEvents   retención +      FilterPattern "ERROR"      OK/ALARM   notifica
   (rol IAM)    KMS opcional     MetricValue=1, Default=0
                    │
                    ├──▶ Logs Insights (consulta guardada)  → contar errores por período
                    └──▶ Live Tail                          → ver ERROR en streaming
```

- El **metric filter** cuenta las líneas `ERROR` y publica una métrica personalizada.
- La **alarma** vigila esa métrica (estadística `Sum`) y pasa a `ALARM` al superar
  el umbral; opcionalmente publica en un **topic SNS**.
- En paralelo, **Logs Insights** (con una `QueryDefinition` guardada) y **Live Tail**
  sirven para localizar y contar los errores durante el *troubleshooting*.

Todo el conjunto (log group + metric filter + alarma + query guardada + SNS) se
define en una única plantilla de **CloudFormation**. **IAM** es transversal (el
rol de EC2 autoriza la ingestión y el permiso `logs:Unmask` gobierna el acceso a
datos enmascarados) y **KMS** cifra el log group en reposo.

## 🧪 Escenario de troubleshooting

Generá líneas `ERROR` en la app de EC2, mirá la alarma pasar a `ALARM` y usá
Logs Insights para localizar y contar los errores por período.

## 🧰 Servicios protagonistas

| Servicio | Rol en la clase |
|---|---|
| **Amazon CloudWatch Logs** | Centraliza los logs de la app en un log group con retención; base del metric filter, la alarma y la consulta de Logs Insights. |
| **Amazon CloudWatch Alarms** | Vigila la métrica del metric filter de `ERROR` y pasa a `ALARM`, disparando (opcional) la notificación por SNS. |
| **Amazon EC2** | Genera los logs de la aplicación; el agente de CloudWatch los envía al log group usando el rol IAM de la instancia. |
| **AWS KMS** | Cifra el log group en reposo con una customer managed key controlada por el cliente (pilar de protección). |
| **AWS CloudFormation** | Declara todo el pipeline (log group, metric filter, alarma, `QueryDefinition` y SNS) en un único stack reproducible. |
| **AWS IAM** | Autoriza la ingestión desde EC2 y controla el acceso a datos sensibles con el permiso `logs:Unmask`. |

## 🚀 Cómo usar

1. **Presentación** — abrí [`presentacion/index.html`](presentacion/index.html)
   en el navegador (doble clic o `file://`). Navegá con `←` / `→`, `O` para la
   vista general y `F` para pantalla completa.
2. **Laboratorio** — desplegá la plantilla de CloudFormation:
   [`laboratorio/template.yaml`](laboratorio/template.yaml). Es autocontenida,
   de bajo costo (< USD 1) y borrable.
3. **Guía paso a paso** — seguí [`laboratorio/guia.html`](laboratorio/guia.html):
   recorrido desde abrir la consola de AWS hasta desplegar, verificar, explorar
   y limpiar, con *checkpoints* y *troubleshooting*.

> 💡 Todo funciona **offline**: abrí los HTML directamente con `file://` o serví
> el repo con un servidor local si tu navegador restringe recursos locales.

---

<div align="center">
  <sub>Parte del curso <a href="../README.md">Observabilidad y Monitoreo en AWS</a> · Clase 2 de 5</sub>
</div>

## 🖥️ Descargar la presentación (PPTX)

Además del deck HTML, la presentación está disponible en **PowerPoint**:

- [`presentacion/Observabilidad-AWS-Clase-2.pptx`](presentacion/Observabilidad-AWS-Clase-2.pptx) — formato 16:9, con notas del orador.

> Podés abrirlo en PowerPoint/Keynote o **importarlo a Google Slides** (Archivo → Importar presentación).
