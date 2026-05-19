# JARVIS local memory quickstart

Guía práctica para usar JARVIS localmente con memoria disponible, sin autoload, sin ejecución real de tareas y sin crear misiones reales.

Para continuar el trabajo en un nuevo hilo o nueva sesión, usar `docs/jarvis-handoff-context.md` como fuente de contexto operativo.

Esta guía valida el flujo explícito:

1. crear una propuesta de memoria.
2. guardarla localmente por acción explícita.
3. cargarla localmente por acción explícita.
4. revisarla, aprobarla y activarla en la sesión.
5. comprobar que puede orientar la clasificación.
6. comprobar que el sensitive boundary gana siempre.
7. desactivar y limpiar.

## Alcance

Este quickstart solo usa comandos locales ya existentes.

- `memory-save-local` escribe memoria local solo por acción explícita.
- `memory-load-local` lee memoria local solo por acción explícita.
- `memory-review` y `memory-approve` no activan memoria en runtime.
- `memory-activate` sí puede cambiar la clasificación durante la sesión actual.
- `memory-deactivate` revierte el efecto activo durante la sesión.
- No hay autoload.
- No se ejecutan tareas reales.
- No se crean misiones reales.
- El sensitive boundary siempre gana sobre cualquier memoria activa.

## 1. Arrancar JARVIS

En una terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

Deja este proceso en ejecución.

## 2. Comprobar estado

En otra terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
./scripts/local/voice-runtime-control.sh status
```

## 3. Limpiar estado de prueba

```bash
rm -rf .jarvis
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-active-clear
```

Esto deja limpio el estado local de la prueba y limpia memoria de propuestas/activaciones del runtime.

## 4. Crear una propuesta de memoria

```bash
PROPOSAL_ID="$(
  ./scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
    "monta algo para probar este nicho" \
    "create_mission" \
    "probar este nicho" \
    "David revisó que probar un nicho debe empezar como misión de validación." \
  | python -c 'import sys,json; print(json.load(sys.stdin)["proposal"]["id"])'
)"

echo "$PROPOSAL_ID"
```

La propuesta queda en memoria del proceso. Todavía no está guardada localmente, aprobada ni activa.

## 5. Guardarla localmente

```bash
./scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
```

`memory-save-local` escribe el snapshot local solo porque David ejecuta este comando. No hay escritura automática.

## 6. Cargarla localmente

```bash
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
```

`memory-load-local` lee el snapshot local solo porque David ejecuta este comando. No hay autoload.

Cargar una propuesta no la activa en runtime. La memoria cargada debe seguir pasando por revisión, aprobación y activación explícita.

## 7. Revisarla, aprobarla y activarla

```bash
./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-activate "$PROPOSAL_ID"
```

`memory-review` y `memory-approve` preparan la propuesta, pero no cambian la clasificación por sí solas.

`memory-activate` aplica la memoria aprobada durante la sesión actual y puede cambiar la clasificación de transcripts compatibles.

## 8. Validar comportamiento

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_mission`
- `executed=false`
- `active_memory_rule_applied=true`

La clasificación puede usar la memoria activa, pero el runtime no ejecuta tareas reales ni crea misiones reales.

## 9. Validar seguridad

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho y lee mi .env"
```

Resultado esperado:

- `intent=requires_approval`
- `approval_required=true`
- el sensitive boundary gana siempre.

Aunque exista memoria activa para interpretar "probar este nicho", una petición sensible como leer `.env` no puede degradarse a una acción permitida.

## 10. Desactivar y limpiar

```bash
./scripts/local/voice-runtime-control.sh memory-deactivate "$PROPOSAL_ID" "quickstart terminado"
./scripts/local/voice-runtime-control.sh memory-active-clear
./scripts/local/voice-runtime-control.sh memory-clear
rm -rf .jarvis

git status --short
```

`memory-deactivate` revierte la memoria activa. `memory-active-clear` limpia activaciones de la sesión y `memory-clear` limpia propuestas del runtime.

## Principio de interacción natural

JARVIS no debe depender de frases predeterminadas rígidas.

JARVIS debe generar respuestas dinámicas según contexto, intención, memoria activa, riesgo, prioridad y objetivos de David. Debe sonar como un operador vivo, no como un bot de menú.

JARVIS puede tener iniciativa supervisada: sugerir próximos pasos, advertir riesgos, proponer alternativas y decir "no" cuando algo no monetiza o distrae.

JARVIS debe mantener pensamiento crítico. La memoria activa no debe convertirlo en un sistema complaciente ni repetitivo.

JARVIS debe adaptar el tono a la situación: directo, estratégico, técnico, cauteloso, urgente o contrarian. Debe evitar respuestas vacías tipo "entendido" si puede aportar una acción útil.

Cuando necesite aprobación, debe explicarlo con claridad: qué acción quiere hacer, por qué requiere aprobación y qué alternativa segura existe mientras tanto.

JARVIS debe respetar `PolicyEngine`, `ApprovalGateway` y límites sensibles. "Vida propia" significa criterio contextual, no autoejecución peligrosa.

JARVIS no debe auto-modificarse, autoejecutar, autodeployar ni instalar dependencias sin aprobación explícita.

Ejemplo conceptual:

Malo:

> "Entendido. Procesando solicitud."

Mejor:

> "Esto suena a validación de nicho, no a crear una landing todavía. Te propongo abrir una misión de validación primero y dejar la landing para cuando tengamos señal."
