# JARVIS End-to-End Prepare-Only Smoke After Phase S

Esta validación transversal comprueba que las foundations cerradas hasta Phase S
siguen exponiendo contratos prepare-only sin activar ejecución real.

## Alcance

El smoke carga la aplicación API y valida:

- `/health` y los status endpoints conocidos de las foundations principales.
- flags prepare-only y default-deny para ejecución, persistencia, llamadas externas,
  secretos, Hermes y ApprovalGateway.
- markers de Command Center y capacidades read-only de Operator Console.
- previews POST seleccionados de voz, móvil, visión, dispositivos, sandbox, tools,
  assets, deploy, marketing, revenue, scheduler, learning, Personal OS,
  personalización y Future/Moonshot.
- ausencia global de nombres de rutas peligrosas de ejecución, deploy, instalación,
  envío, sensores, memoria, PRs y control físico.
- separación de revenue projected/confirmed/gross/expenses/net.
- invariantes del mapa maestro: Phase S es la última fase implementada, no existe
  Phase T implícita y no se crean fases sin actualizar antes el mapa.

Los previews se invocan con un Hermes adapter y un ApprovalGateway que fallan
inmediatamente si son llamados. La suite también compara missions y tasks antes y
después para detectar mutación accidental.

## Garantías y límites

La suite garantiza que las superficies inspeccionadas conservan sus contratos
prepare-only y que los previews seleccionados no mutan el estado in-memory de la
API. No ejecuta Hermes real, no crea approvals reales, no usa secretos, no realiza
llamadas externas y no activa cámara, micrófono, pantalla, dispositivos ni
persistencia real.

No demuestra que capacidades runtime ajenas a las foundations prepare-only estén
deshabilitadas. Tampoco sustituye revisiones específicas de policy, approval,
seguridad o integración.

## Ejecución

Desde la raíz del repositorio:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_e2e_prepare_only_smoke_after_phase_s.py -q
```

El smoke invoca directamente los endpoints registrados por FastAPI. Esto conserva
la validación HTTP estructural de método/status y evita depender del hang conocido
de `TestClient` dentro de algunos entornos Codex.
