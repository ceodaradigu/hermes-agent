# Criterios de Cierre

## Que significa cerrar una PR

Cerrar una PR significa que su promesa explicita esta cumplida y validada en el
nivel correcto:

- `REAL`: ejecucion o comportamiento comprobable.
- `PARCIAL`: alcance parcial declarado y limites escritos.
- `READINESS`: contrato/preparacion declarado como readiness, sin venderlo como
  capacidad final.
- `NO HECHO`: ausencia honesta de capacidad real.

## Tests no bastan

Los tests son necesarios, pero no bastan si la PR promete capacidad de usuario:

- voz real;
- wake real por microfono;
- browser real;
- file mutation real;
- iPhone fuera de casa;
- Home Assistant/casa fisica;
- pagos/publicacion/deploy/mensajeria.

En esos casos hace falta validacion manual real o cerrar la PR solo como
`READINESS` declarado.

## PRs documentales

En PRs documentales, no hace falta validacion manual nueva de usuario si no se
promete una nueva capacidad runtime. Pero los docs no pueden contradecir
validaciones manuales ya documentadas en handoff, master map o documentos de
cierre: si algo esta validado en el PC de David, debe decir `REAL validado en PC
de David` y mantener sus limitaciones.

Si una PR promete una capacidad de usuario nueva, tests no bastan: requiere
validacion manual real en PC/iPhone o cierre explicito como `READINESS`.

## Dispatcher futuro

Para cerrar como `REAL` el dispatcher gobernado JARVIS -> Hermes, exigir:

- una accion browser real ejecutada por Hermes desde JARVIS;
- una accion file real ejecutada por Hermes desde JARVIS;
- risk classification antes de ejecutar;
- approval cuando toque;
- auditoria metadata-only;
- respuesta final honesta;
- prueba de que no existe `/execute`, shell arbitrario ni frontend directo a
  Hermes.

Hasta entonces, browser/file desde JARVIS deben quedar `PARCIAL` o `READINESS`
segun el caso.
