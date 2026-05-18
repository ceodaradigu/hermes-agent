# User Understanding memory save-local smoke test

Esta guia valida el flujo futuro local de `memory-save-local`. A diferencia de los smoke tests anteriores de snapshot en memoria, este flujo si toca disco bajo `.jarvis/user_understanding/`.

## Preparacion

Arranca la API local de JARVIS en el puerto habitual y usa el script local:

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

Opcionalmente lista el estado en memoria:

```bash
scripts/local/voice-runtime-control.sh memory-proposals
```

## Ejecutar save-local explicito

```bash
scripts/local/voice-runtime-control.sh memory-save-local
```

Tambien se puede pasar base dir y backup:

```bash
scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
```

## Verificar archivos locales

```bash
ls -la .jarvis/user_understanding/
ls -la .jarvis/user_understanding/backups/
cat .jarvis/user_understanding/memory_proposals.snapshot.json
cat .jarvis/user_understanding/audit_log.jsonl
```

Debe existir:

- `.jarvis/user_understanding/memory_proposals.snapshot.json`
- `.jarvis/user_understanding/audit_log.jsonl`
- `.jarvis/user_understanding/backups/`

Si ya habia snapshot previo y se uso `create_backup=true`, debe aparecer un backup en `backups/`.

## Confirmar alcance

Este flujo sigue sin implementar `load-local` ni autoload. Guardar el archivo no aplica memoria al router/runtime, no cambia la clasificacion de `transcript`, no ejecuta tareas reales y no crea misiones reales.

Puedes comprobar que `transcript` sigue comportandose igual antes y despues del save-local:

```bash
scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
scripts/local/voice-runtime-control.sh memory-save-local
scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

## Limpieza

Si quieres borrar el estado local creado por este smoke test:

```bash
rm -rf .jarvis
```

Hazlo solo si no necesitas conservar otros archivos locales bajo `.jarvis`.
