# Laboratorio · Clase 1 — Fundamentos, métricas y monitoreo de EC2 con CloudWatch

> Los pilares de la observabilidad y las métricas de tu infraestructura.

Desplegás con **CloudFormation** la base del entorno de observabilidad: una VPC con
subred pública y una instancia **EC2 t3.micro** que instala el **CloudWatch agent**
(config versionada en **SSM Parameter Store**), publica métricas del sistema operativo
y una métrica personalizada con `PutMetricData`. Después verificás los datos en
**CloudWatch** y diagnosticás, por **SSM Session Manager**, por qué dejan de llegar
métricas cuando el agente se detiene.

## Qué despliega

| Recurso | Servicio | Para qué |
|---|---|---|
| VPC + subred pública + Internet Gateway + ruteo | VPC | Red con salida a internet para el agente y SSM |
| IAM Role + Instance Profile | IAM | Permisos sin credenciales estáticas (`CloudWatchAgentServerPolicy` + `AmazonSSMManagedInstanceCore`) |
| Parámetro `/observabilidad/<stack>/cloudwatch-agent-config` | SSM Parameter Store | Configuración JSON versionada del CloudWatch agent |
| Instancia `t3.micro` (gp3 8 GiB, cifrado, single-AZ) | EC2 | Host monitoreado; UserData instala y arranca el agente |
| Security Group sin ingress (egress abierto) | VPC | Acceso solo por Session Manager (sin puerto SSH) |

Rutas de métricas resultantes:

- **Hipervisor** → `AWS/EC2` (`CPUUtilization`, sin agente).
- **Sistema operativo** → `CWAgent` (`mem_used_percent`, `disk_used_percent`, vía agente).
- **Personalizada** → `Curso/Obs` (`TareasCompletadas`, vía `PutMetricData` + cron por minuto).

## Requisitos

- Cuenta de AWS con permisos para VPC, EC2, IAM, SSM y CloudWatch.
- Región sugerida: **us-east-1**.
- Para la vía CLI: `aws-cli` configurado (`aws configure`).
- Al desplegar hay que aceptar la capacidad **`CAPABILITY_IAM`** (el stack crea un rol).

## Deploy rápido

### Consola

1. **CloudFormation › Create stack › With new resources**.
2. **Upload a template file** → subí `template.yaml`.
3. Nombre `obs-clase-1`, dejá los parámetros por defecto (la AMI se resuelve sola desde SSM).
4. Marcá *I acknowledge that AWS CloudFormation might create IAM resources* → **Submit**.
5. Esperá `CREATE_COMPLETE` y revisá la pestaña **Outputs**.

### CLI

```bash
aws cloudformation deploy \
  --stack-name obs-clase-1 \
  --template-file template.yaml \
  --parameter-overrides file://parameters.example.json \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

Verificar las métricas del SO (reemplazá `<INSTANCE_ID>` por el output `InstanceId`):

```bash
aws cloudwatch list-metrics \
  --namespace CWAgent \
  --dimensions Name=InstanceId,Value=<INSTANCE_ID> \
  --region us-east-1
```

## Parámetros

| Parámetro | Default | Descripción |
|---|---|---|
| `VpcCidr` | `10.20.0.0/16` | Rango CIDR de la VPC |
| `PublicSubnetCidr` | `10.20.1.0/24` | Rango CIDR de la subred pública |
| `InstanceType` | `t3.micro` | Tipo de instancia (`t3.micro` o `t3.small`) |
| `VolumeSizeGb` | `8` | Tamaño del disco raíz gp3 (8–30 GiB) |
| `LatestAmiId` | *(SSM)* | AMI de Amazon Linux 2023 resuelta desde `/aws/service/ami-amazon-linux-latest/...` |

`parameters.example.json` trae los defaults listos para `create-stack`/`deploy`.

## Costo estimado

Con limpieza al terminar, el laboratorio queda **por debajo de USD 1**:

- EC2 `t3.micro`: ~USD 0.0104/hora on-demand en us-east-1.
- EBS gp3 8 GiB: fracción de centavo por las horas del lab.
- Métricas personalizadas de CloudWatch: pocas métricas únicas, dentro/cerca de free tier.
- VPC, IGW, subred, IAM, SSM Parameter Store (Standard): sin costo.

## Limpieza

```bash
aws cloudformation delete-stack --stack-name obs-clase-1 --region us-east-1
```

Borra todos los recursos (sin `DeletionPolicy: Retain`, sin buckets S3 que vaciar).
Las métricas ya publicadas expiran solas por retención y no generan costo una vez que
dejan de recibir datos.

## Archivos

- `template.yaml` — CloudFormation del laboratorio (cfn-lint limpio).
- `parameters.example.json` — parámetros de ejemplo.
- `guia.html` — guía paso a paso (consola + CLI).
- `troubleshooting.md` — problemas frecuentes y escenarios de exploración.
