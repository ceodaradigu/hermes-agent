# User Understanding memory load-local smoke test

Esta guia valida `memory-load-local` como lectura local explicita. El flujo lee y escribe `.jarvis/user_understanding/` solo por comandos explicitos; no hay autoload ni aplicacion al router/runtime.

## Preparacion

Arranca la API local de JARVIS y limpia proposals en memoria:

```bash
scripts/local/voice-runtime-control.sh memory-clear
```

## Crear una proposal

```bash
scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
  "monta algo para probar este nicho" \
  "create_mission" \
  "probar este nicho" \
  "David reviso que probar un nicho debe empezar como mision de validacion."
```

## Guardar snapshot local

```bash
scripts/local/voice-runtime-control.sh memory-save-local
```

Esto crea `.jarvis/user_understanding/memory_proposals.snapshot.json` y audita el guardado.

## Vaciar memoria en proceso

```bash
scripts/local/voice-runtime-control.sh memory-clear
scripts/local/voice-runtime-control.sh memory-proposals
```

La lista debe quedar vacia.

## Cargar snapshot local explicitamente

```bash
scripts/local/voice-runtime-control.sh memory-load-local
```

Tambien se puede pasar `base_dir` y `replace`:

```bash
scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
```

`memory-load-local` lee solo `.jarvis/user_understanding/memory_proposals.snapshot.json`, resuelto por el backend. No acepta ruta directa a archivo.

## Verificar proposal recuperada

```bash
scripts/local/voice-runtime-control.sh memory-proposals
```

Debe aparecer la proposal creada antes del `memory-save-local`.

## Verificar transcript sin cambio

```bash
scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

El resultado debe seguir siendo el comportamiento normal del router, por ejemplo `create_asset` si esa era la clasificacion previa. `memory-load-local` no aplica aprendizaje al router/runtime; solo recupera proposals al store para revision/listado.

## Limpieza opcional

```bash
scripts/local/voice-runtime-control.sh memory-clear
rm -rf .jarvis
```

El borrado de `.jarvis` es opcional y solo debe hacerse si no necesitas conservar otros archivos locales.
