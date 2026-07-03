# Troubleshooting y exploración · Clase 3

Problemas frecuentes del pipeline de archivado y explotación, más escenarios
para experimentar. Muchos de estos errores son **intencionalmente reproducibles**
para practicar diagnóstico.

## Problemas frecuentes

### 1. Firehose entrega objetos vacíos o ilegibles (basura en Athena)
**Síntoma:** los objetos en S3 no se pueden leer o Athena devuelve caracteres
raros. **Causa:** los logs de CloudWatch llegan **gzip-comprimidos** a Firehose.
**Solución:** habilitar la **decompresión** en Firehose (procesador
`Decompression` + `CloudWatchLogProcessing` con `DataMessageExtraction`), como ya
hace esta plantilla, antes de cualquier conversión. Sin eso, las consultas de
Athena devuelven basura.

### 2. La conversión a Parquet falla y los registros van al prefijo de error
**Síntoma:** aparecen objetos bajo `errores/` y faltan datos en `cloudtrail/`.
**Causa:** el esquema de la tabla de Glue no coincide con la estructura real del
JSON (columnas o tipos mal definidos). **Solución:** alinear las columnas/tipos
de la tabla de Glue con el JSON real. En este lab entregamos JSON (no Parquet)
para simplificar; si activás record format conversion, revisá el esquema.

### 3. Athena escanea demasiado: query lenta y cara
**Síntoma:** la query tarda y el costo estimado es alto. **Causa:** no se filtra
por la columna de partición de fecha, o `partition projection` está mal
configurada (rango/formato de fecha incorrecto). **Solución:** incluir SIEMPRE un
`WHERE` sobre las particiones (`anio`, `mes`, `dia`). El workgroup además corta
cada query a 100 MB escaneados.

### 4. Athena devuelve cero filas aunque hay datos
**Causas típicas:**
- El `LOCATION` de la tabla apunta al prefijo equivocado (revisá que sea
  `s3://<bucket>/cloudtrail/`).
- Las particiones no fueron cargadas: sin partition projection habría que correr
  `MSCK REPAIR TABLE` o `ALTER TABLE ADD PARTITION`. Con projection, verificá que
  el rango de años/meses/días cubra la fecha de tus datos.
- Se usó el SerDe incorrecto para el formato del log.

### 5. Access Denied en la cadena IAM
**Síntoma:** errores de permisos en algún salto. **Revisar:**
- El rol del subscription filter puede escribir en Firehose (`firehose:PutRecord*`).
- El rol de Firehose tiene `s3:PutObject` sobre el bucket (y `glue:GetTable*` si
  convertís a Parquet).
- Athena/el usuario pueden leer S3 y escribir en la **result location**.

### 6. Athena falla al consultar objetos ya transicionados a Glacier
**Síntoma:** error al leer objetos que la regla de Lifecycle ya movió a Glacier
Flexible Retrieval o Deep Archive. **Causa:** Athena no lee esas clases sin
restaurar. **Solución:** restaurar los objetos primero, o segmentar el bucket
para archivar solo lo que ya no se consulta (por eso los datos "calientes"
quedan en `cloudtrail/` y solo se archivan tras N días).

### 7. La regla de Lifecycle no ahorra lo esperado
**Causa:** overhead y mínimo de almacenamiento por objeto en Glacier (p. ej. 90
días en Deep Archive). Archivar muchos objetos pequeños sale caro. **Solución:**
ajustar el buffering de Firehose (tamaño/tiempo) para generar **pocos objetos
grandes** — en este lab, 64 MB / 60 s.

### 8. El stack queda en ROLLBACK_COMPLETE
**Causa habitual:** el nombre de bucket ya existe (los nombres de bucket son
globales) o el `NombrePrefijo` colisiona con recursos previos. **Solución:** abrí
**Events**, buscá el primer error (arriba del rollback) y cambiá el
`NombrePrefijo`.

## Escenario de investigación (obligatorio)

**Pregunta:** ¿quién ejecutó `AuthorizeSecurityGroupIngress` abriendo un puerto
sensible (22 o 3389) y cuándo?

La instancia EC2 del lab genera, entre otros, un evento donde el usuario
`pedro.admin` abre el puerto **22** a `0.0.0.0/0`. Ejecutá en Athena (workgroup
`<prefijo>-wg`, base `<prefijo>_archivo_db`), ajustando la partición de fecha:

```sql
SELECT
  eventtime,
  useridentity.arn      AS quien,
  useridentity.username AS usuario,
  sourceipaddress       AS ip_origen,
  awsregion             AS region,
  requestparameters     AS parametros
FROM "<prefijo>_archivo_db"."cloudtrail_eventos"
WHERE eventname = 'AuthorizeSecurityGroupIngress'
  AND (
        requestparameters LIKE '%"fromPort":22%'
     OR requestparameters LIKE '%"fromPort":3389%'
  )
  AND anio = '2026' AND mes = '07'   -- ajustá a la fecha de tus datos
ORDER BY eventtime DESC;
```

**Resultado esperado:** una fila con `pedro.admin`, su IP de origen
(`203.0.113.24`), la región y el timestamp del evento. Eso responde *quién* y
*cuándo*. La consulta ya viene guardada como **named query** en el workgroup.

> Si la query devuelve cero filas: (a) esperá 1–2 min a que Firehose escriba en
> S3; (b) verificá que `anio`/`mes`/`dia` coincidan con la fecha real de los
> objetos (`aws s3 ls s3://<bucket>/cloudtrail/ --recursive`).

## Escenarios de exploración

- **Cambiá el buffering de Firehose** (`SizeInMBs` / `IntervalInSeconds`) y observá
  cómo cambia la cantidad y el tamaño de los objetos en S3. Menos objetos grandes
  = mejor para Glacier.
- **Bajá `DiasHastaGlacier` a 1** en un stack de prueba y mirá cómo la regla de
  Lifecycle transiciona los objetos (y por qué Athena luego no los lee sin
  restaurar).
- **Rompé la query a propósito:** quitá el filtro de partición (`anio`/`mes`) y
  compará los bytes escaneados; el workgroup debería cortar a 100 MB.
- **Sumá una segunda condición de investigación:** buscá `RevokeSecurityGroupIngress`
  para ver quién *cerró* el puerto, y correlacioná con el evento de apertura.
- **Compará Logs Insights vs Athena:** Logs Insights es ideal para lo reciente en
  CloudWatch Logs; Athena es para lo archivado en S3 a bajo costo y gran volumen.
