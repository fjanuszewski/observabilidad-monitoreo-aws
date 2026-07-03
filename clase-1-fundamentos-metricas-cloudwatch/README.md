# Clase 1 — Fundamentos, métricas y monitoreo de EC2 con CloudWatch

> **Los pilares de la observabilidad y las métricas de tu infraestructura.**
>
> Clase 1 de 5 · Curso *Observabilidad y Monitoreo en AWS* · ⏱ ~2 horas · 🧪 Laboratorio incluido

Esta clase establece los fundamentos de la observabilidad en AWS: distingue monitoreo de
observabilidad, presenta los tres pilares (métricas, logs y trazas), las *golden signals* y los
métodos RED/USE, e introduce SLIs, SLOs y *error budgets*. El foco técnico central es **Amazon
CloudWatch** como plataforma de métricas y la instrumentación de **EC2** con el agente unificado
para recolectar métricas del sistema operativo. Todo el entorno del laboratorio se despliega como
infraestructura-como-código con **CloudFormation**, con la configuración del agente versionada en
**SSM Parameter Store**.

## Objetivos

- Comprender los pilares de la observabilidad y cómo se aplican en AWS.
- Recolectar, publicar y consultar métricas con Amazon CloudWatch.
- Instrumentar una instancia EC2 con el agente de CloudWatch.
- Desplegar la base del entorno con CloudFormation.

## Módulos

1. **Fundamentos de observabilidad y monitoreo**
   - Monitoreo vs observabilidad; los tres pilares (métricas, logs y trazas) y los eventos.
   - *Golden signals* (latencia, tráfico, errores, saturación) y métodos RED/USE.
   - Introducción a SLIs, SLOs y *error budgets*.
   - Panorama de los servicios de observabilidad de AWS y cómo se relacionan.
2. **Métricas con Amazon CloudWatch**
   - Métricas de servicios de AWS, *namespaces* y dimensiones.
   - Resolución estándar vs alta resolución y retención de métricas.
   - Métricas personalizadas con `PutMetricData`.
   - Embedded Metric Format (EMF): métricas embebidas en logs.
   - *Metric math*, detección de anomalías y Metrics Insights (consultas tipo SQL sobre métricas).
3. **Monitoreo de EC2 con el agente unificado de CloudWatch**
   - Métricas del hipervisor vs métricas del sistema operativo (memoria, disco, procesos).
   - Instalación del agente y estructura de su archivo de configuración.
   - Configuración versionada en SSM Parameter Store.
   - Recolección simultánea de métricas del SO y logs con el mismo agente.
   - Despliegue del agente a escala con AWS Systems Manager.
4. **Infraestructura como código con CloudFormation**
   - Anatomía de una plantilla: `Parameters`, `Resources` y `Outputs`.
   - Por qué definir toda la observabilidad como código.

## Arquitectura del laboratorio

Una única plantilla de CloudFormation despliega toda la base del entorno y el flujo de métricas
queda así:

1. **CloudFormation** despliega el *stack* base.
2. El stack crea: **VPC** → subred pública → **Internet Gateway** (ruta `0.0.0.0/0`), un **IAM Role
   + Instance Profile** (`CloudWatchAgentServerPolicy` + `AmazonSSMManagedInstanceCore`), un
   parámetro en **SSM Parameter Store** con la config JSON del agente y la instancia **EC2
   `t3.micro`**.
3. La **EC2** ejecuta su `UserData` en el arranque, instala el CloudWatch agent, que lee su
   configuración desde SSM Parameter Store y arranca.
4. Dos rutas de métricas hacia **CloudWatch**:
   - **Ruta hipervisor:** EC2 → CloudWatch (namespace `AWS/EC2`, p. ej. `CPUUtilization`), sin agente.
   - **Ruta SO:** EC2 + agente → CloudWatch (namespace `CWAgent`, p. ej. `mem_used_percent`,
     `disk_used_percent`) y logs.
5. **Métrica personalizada:** un script en la instancia usa `PutMetricData` para publicar en un
   namespace propio.
6. **Verificación:** en la consola de CloudWatch se comparan las métricas del SO (`CWAgent`) con las
   del hipervisor (`AWS/EC2`) y se confirma la métrica personalizada.
7. **Troubleshooting:** con **SSM Session Manager** te conectás a la instancia sin SSH, detenés el
   agente y observás que dejan de llegar las métricas del SO (las del hipervisor siguen),
   diagnosticando con los logs del agente (`amazon-cloudwatch-agent.log`).

```
CloudFormation → [ VPC + subred pública + IGW | IAM Role | SSM Parameter Store | EC2 ]
EC2 (hipervisor) ───────────────► CloudWatch (AWS/EC2: CPUUtilization)
EC2 + CloudWatch agent ─────────► CloudWatch (CWAgent: mem/disk + logs)
Script + PutMetricData ─────────► CloudWatch (namespace personalizado)
SSM Session Manager ────────────► EC2 (diagnóstico del agente)
```

### Entregables del laboratorio

- VPC + subred pública con Internet Gateway.
- Instancia EC2 `t3.micro` con CloudWatch agent instalado por UserData.
- Config del agente almacenada en SSM Parameter Store.
- Métrica personalizada publicada con `PutMetricData`.
- Verificación de métricas del SO en CloudWatch.

## Servicios que se usan

| Servicio | Rol en la clase |
| --- | --- |
| **Amazon CloudWatch** | Plataforma central de observabilidad: destino de todas las métricas (hipervisor `AWS/EC2`, SO `CWAgent` y personalizada). Se usa la consola para verificar y comparar métricas. |
| **Amazon EC2** | Host monitoreado. Publica métricas del hipervisor sin agente y, con el CloudWatch agent, expone métricas del SO (memoria, disco). |
| **AWS CloudFormation** | Mecanismo de despliegue: una plantilla crea la VPC, la EC2, el rol/instance profile de IAM y el parámetro en SSM. Demuestra la observabilidad como código. |
| **AWS Systems Manager** | Parameter Store versiona la config JSON del agente; Session Manager da acceso a la instancia sin SSH para el diagnóstico. |
| **Amazon VPC** | Provee la red: VPC con subred pública, tabla de rutas e Internet Gateway para que la instancia tenga salida a CloudWatch y SSM. |
| **AWS IAM** | Otorga a la EC2 los permisos (`CloudWatchAgentServerPolicy`, `AmazonSSMManagedInstanceCore`) vía un instance profile, sin credenciales estáticas. |

## Cómo usar

- **Presentación (deck):** abrí [`presentacion/index.html`](presentacion/index.html) en el navegador.
  Navegá con `←` / `→`, `O` para la vista general y `F` para pantalla completa. Funciona offline.
- **Laboratorio:**
  - Guía paso a paso: [`laboratorio/guia.html`](laboratorio/guia.html) — desde abrir la consola de
    AWS hasta desplegar, verificar, explorar y limpiar.
  - Plantilla de CloudFormation: [`laboratorio/template.yaml`](laboratorio/template.yaml).
  - Recordá **eliminar el stack** al terminar para no incurrir en costos (el lab está diseñado para
    costar menos de USD 1).

## Escenario de investigación / troubleshooting

Compará las métricas del SO (`mem_used_percent`, `disk_used_percent`) con las del hipervisor
(`CPUUtilization`); luego detené el agente y diagnosticá por qué dejan de llegar las métricas del SO
usando SSM Session Manager y los logs del agente. Errores frecuentes: buscar métricas de memoria o
disco en el namespace `AWS/EC2` (viven en `CWAgent`), un instance profile sin
`CloudWatchAgentServerPolicy`, o el agente detenido o mal configurado.

## 🖥️ Descargar la presentación (PPTX)

Además del deck HTML, la presentación está disponible en **PowerPoint**:

- [`presentacion/Observabilidad-AWS-Clase-1.pptx`](presentacion/Observabilidad-AWS-Clase-1.pptx) — formato 16:9, con notas del orador.

> Podés abrirlo en PowerPoint/Keynote o **importarlo a Google Slides** (Archivo → Importar presentación).
