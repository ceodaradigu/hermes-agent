# PR #160 - Presence UI real + 3D Orb/HUD adoption

Fecha: 2026-06-18

## Resumen

PR #160 mueve `/jarvis` desde una consola tipo dashboard hacia una Presence UI
local, cinematografica y orb-first. La pantalla principal prioriza el nucleo
JARVIS, una smart bar humana y paneles contextuales minimos. Los detalles
tecnicos siguen disponibles, pero plegados en `Sistemas`, `details` o
secciones secundarias.

Esta PR sigue siendo visual/UI/presence. No crea otro Hermes, no duplica runtime
de ejecucion, no añade `/execute`, no llama Hermes desde frontend, no aprueba,
no rechaza y no abre capacidades peligrosas nuevas.

## Que cambio visualmente

- Header mas ligero: muestra presencia local, estado read-only/approval y kill
  switch visible. El texto tecnico de brain/intake queda oculto para lectores o
  en drawer.
- Layout orb-first: centro dominante con `JarvisOrb3D`, laterales reducidos y
  panel derecho contextual.
- Orbe reforzado: estado `approval_required`, marcas de performance budget,
  anillos extra, glow, profundidad, fallback visible y `motion-reduce`.
- Smart bar premium: acepta borrador local de texto sin enviar nada, mantiene
  voz manual opt-in, respuesta humana corta, transcripcion local y detalles
  plegados de intent/risk.
- Camara lateral premium: modulo local con preview opt-in, modo ampliado manual
  y privacidad visible. No arranca camara al cargar.
- Approval panel contextual: mantiene preview read-only y botones
  deshabilitados; los detalles de cards quedan plegados.
- Finance/ROI y estado tecnico se plegaron para que no compitan con la
  presencia.

## Repos externas estudiadas

| Repo | URL | Licencia visible | Que se tomo | Tipo |
| --- | --- | --- | --- | --- |
| jincocodev/openclaw-jarvis-ui | https://github.com/jincocodev/openclaw-jarvis-ui | ISC | Patron conceptual de orbe vivo con particulas, estados, power-save y HUD; se descarto servidor, chat, TTS, system monitor y gateway. | Reimplementacion visual |
| Suryansh777777/Jarvis-CV | https://github.com/Suryansh777777/Jarvis-CV | No visible en la pagina revisada | Inspiracion de composicion AR/HUD y panel de camara; se descartaron MediaPipe, gesture control, face tracking y permisos automaticos. | Reimplementacion visual |
| zoharbarzilai/Generative-3D-Audio-Visualizer | https://github.com/zoharbarzilai/Generative-3D-Audio-Visualizer | No visible en la pagina revisada | Inspiracion de esfera generativa, starfield y bloom; se descarto Web Audio, microfono y playlist. | Reimplementacion visual |
| harsh-raj00/my-jarvis | https://github.com/harsh-raj00/my-jarvis | MIT | Inspiracion de experiencia cinematografica, rings, particulas y HUD; se descarto FastAPI, Gemini, ElevenLabs, plugins, smart home, email y WebSocket runtime. | Reimplementacion visual |
| TheStack-ai/jarvis-orb | https://github.com/TheStack-ai/jarvis-orb | MIT | Concepto "presence, not a tool" y orbe como visibilidad de pensamiento; se descarto MCP server, memoria persistente, instaladores y desktop runtime. | Reimplementacion conceptual |
| chevgan/react-ai-voice-visualizer | https://github.com/chevgan/react-ai-voice-visualizer | MIT | Patrones de estados `idle/listening/thinking/speaking`, retina budget y canvas optimizado; se descarto paquete, hooks de microfono y Web Audio API. | Reimplementacion visual |
| ethanplusai/jarvis | https://github.com/ethanplusai/jarvis | Personal/non-commercial visible | Referencia negativa para no copiar runtime: acciones reales, API keys, Claude Code tasks, Mail/Calendar/Notes y screen context quedan fuera. | Estudiado/no adoptado |
| pmndrs/react-three-fiber | https://github.com/pmndrs/react-three-fiber | MIT | Evaluado como posible dependencia autorizada para R3F. No se añadio porque el WebGL manual existente cubre el objetivo con menos riesgo. | Estudiado/no usado |
| pmndrs/drei | https://github.com/pmndrs/drei | MIT | Evaluado para helpers 3D. No se añadio. | Estudiado/no usado |
| pmndrs/react-postprocessing | https://github.com/pmndrs/react-postprocessing | MIT | Evaluado para bloom/postprocessing. No se añadio. | Estudiado/no usado |

No se copio codigo externo. Las ideas visuales se reimplementaron sobre los
componentes existentes de Hermes/JARVIS.

## Dependencias añadidas

Ninguna.

Motivo: `JarvisOrb3D` ya tenia WebGL manual con shaders, particulas, fallback y
performance budget. Mantenerlo evita peso de bundle, cambios de lockfile y
riesgo de migracion innecesaria en una PR visual. Se mantiene abierta una PR
futura para R3F si hace falta una escena 3D mas compleja.

## Como probar

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.

python -m py_compile $(find jarvis -name '*.py')
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20
git diff --check

cd web
npm ci
npm run build
```

Verificacion manual recomendada:

1. Abrir `/jarvis`.
2. Confirmar que el nucleo domina la pantalla y los paneles tecnicos estan
   plegados.
3. Escribir un borrador en la smart bar y confirmar que el boton enviar sigue
   deshabilitado.
4. Pulsar microfono solo manualmente; stop/cancel debe cerrar el loop.
5. Abrir camara solo con `Abrir`; expandir/contraer el panel; confirmar que no
   hay upload backend ni frames en event stream.
6. Forzar WebGL no disponible o context lost en devtools y confirmar fallback.
7. Activar `prefers-reduced-motion` y confirmar que las animaciones se reducen.

## Riesgos

- El orbe sigue siendo WebGL manual, no R3F. Es mas ligero, pero requiere
  mantenimiento directo de shaders/matrices.
- La camara ampliable es un dock/floating panel manual, no drag-and-drop libre.
- La smart bar acepta borrador local, pero no envia texto; la ejecucion futura
  requiere otra PR con ruta gobernada.
- No hay screenshot automatizado en esta PR; la validacion principal es build,
  tests de contrato y revision manual.

## Performance budget

- Pixel ratio limitado a `1.75` en estado activo y `1.35` en reposo.
- `particleBudget` por estado: menos particulas en idle/stopped, mas en estados
  activos.
- `targetFrameMs` por estado: idle throttled, active cercano a 60fps, stopped
  mas lento.
- `prefers-reduced-motion` reduce frame rate, wave y particulas.
- Buffer WebGL estatico; no se recrean particulas por frame.
- Fallback CSS visible para ausencia de WebGL, fallo de shader o perdida de
  contexto.

## Que NO se implemento

- No R3F/Three/drei/postprocessing como dependencias nuevas.
- No wake real activo.
- No STT/TTS nuevo.
- No MediaPipe, TFJS ni sensores nuevos.
- No camera/mic auto-start.
- No upload de audio, video o frames.
- No backend LLM/proveedor externo.
- No Hermes dispatch desde frontend.
- No approve/reject real.
- No deploy, email, Stripe, dinero, credenciales o lectura de `.env`.

## Siguiente PR recomendada dentro de Fase 1

PR #161 - Presence verification and visual QA:

- Verificacion con browser screenshot para desktop/mobile.
- Test Playwright de canvas no blanco y fallback WebGL.
- Medicion simple de frame budget en idle/active/reduced-motion.
- Ajustes responsive de camara lateral para pantallas medianas.
- Sin runtime nuevo y sin capacidades peligrosas.
