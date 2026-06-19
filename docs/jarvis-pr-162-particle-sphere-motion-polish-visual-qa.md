# PR #162 - Particle Sphere Motion Polish + Visual QA

Fecha: 2026-06-19

## Resumen

PR #162 pertenece a Fase 1 - JARVIS usable en local. Es una PR visual/pulido/QA
sobre la base mergeada en #161. Mantiene intacto el contrato:

JARVIS gobierna. Hermes ejecuta.

No crea otro Hermes, no duplica runtime, no añade `/execute`, no aprueba ni
rechaza acciones reales, no activa sensores automaticamente, no abre Web Audio
nuevo, no sube audio bruto, no sube frames, no añade LLM externo, no añade APIs
externas y no cambia backend execution.

## Que se pulio

- La esfera central de `/jarvis` se mueve hacia una nube viva y volumetrica de
  particulas frio/blanco-hielo/cian, con aire entre particulas y sin masa
  solida.
- El Canvas 2D principal sube de 1420 a 2600 particulas precomputadas y usa una
  distribucion con profundidad real: capas exteriores, polvo interior ligero,
  variacion de tamano/opacidad y perspectiva.
- El centro deja de leerse como nucleo fijo: en idle casi desaparece, aparece
  por concentracion cuando la nube se comprime y se diluye al expandirse.
- La zona central queda limpia: no hay texto grande, logo, placa de lectura,
  crosshair visible ni reactor circular.
- Los laterales, chat/smart bar inferior, camara, approvals, audio bruto local,
  finance plegado, header y drawers se mantienen.
- Se añade Visual QA local plegado en el drawer de sistemas para forzar estados
  visuales sin ejecutar nada.

## Estados visuales

- `idle`: esfera media, respiracion muy lenta, energia minima, rotacion suave,
  variacion de escala casi fija y centro casi inexistente
  (`emergentCoreConcentration` cae a 0.008; ciclo visual 10.5s).
- `listening`: esfera mas pequena y concentrada, particulas tensas, pulso fino y
  contraccion visible (`listeningFocus=1`).
- `transcribing`: reflujo ordenado; las particulas se reorganizan como si
  recalcularan, sin picos de voz.
- `thinking`: turbulencia interna clara, remolinos/curl y redistribucion de
  particulas distinta de speaking (`thinkingTurbulence=1`).
- `speaking`: pseudo-audio determinista local; picos/ondas radiales empujan
  particulas hacia fuera, con expansion/contraccion mas fuerte.
- `alert` / `error`: picos mas agresivos, expansion mas brusca y canal cromatico
  calido/rojo separado.
- `stopped`: esfera reducida, atenuada y con bajo presupuesto de particulas.

## Como probar Visual QA

Opcion 1: abrir `/jarvis`, desplegar `Sistemas`, usar el bloque plegado
`Visual QA` y pulsar:

- Auto
- Idle
- Listening
- Transcribing
- Thinking
- Speaking
- Alert
- Stopped

Opcion 2: abrir con query param local:

```text
/jarvis?jarvisVisualPreview=speaking
/jarvis?jarvisVisualPreview=thinking
/jarvis?jarvisVisualPreview=listening
```

Este preview es solo frontend/local. No llama Hermes, no aprueba, no rechaza, no
activa microfono, no activa camara, no llama backend de ejecucion y no cambia
sensores. Solo reemplaza el estado visual que recibe `JarvisOrb3D`.

## Repos externas revisadas

| Repo | URL | Licencia visible | Que se tomo | Tipo |
| --- | --- | --- | --- | --- |
| `jincocodev/openclaw-jarvis-ui` | https://github.com/jincocodev/openclaw-jarvis-ui | ISC | Presencia orb-first, particulas, estados y power-save como referencia. | Reimplementacion visual |
| `Suryansh777777/Jarvis-CV` | https://github.com/Suryansh777777/Jarvis-CV | No visible en la pagina revisada | Referencia de HUD/camara; no se adopto vision ni tracking. | Estudiado/no copiado |
| `zoharbarzilai/Generative-3D-Audio-Visualizer` | https://github.com/zoharbarzilai/Generative-3D-Audio-Visualizer | No visible en la pagina revisada | Idea de esfera generativa que pulsa con audio. | Reimplementacion visual sin Web Audio |
| `harsh-raj00/my-jarvis` | https://github.com/harsh-raj00/my-jarvis | MIT | Referencia de esfera con muchas particulas y presencia cinematografica. | Reimplementacion visual |
| `TheStack-ai/jarvis-orb` | https://github.com/TheStack-ai/jarvis-orb | MIT | Concepto de presencia viva y estados visibles del pensamiento. | Reimplementacion conceptual |
| `chevgan/react-ai-voice-visualizer` | https://github.com/chevgan/react-ai-voice-visualizer | MIT | Estados `idle/listening/thinking/speaking`, smoothing y canvas 60fps como ideas. | Reimplementacion conceptual |
| `ethanplusai/jarvis` | https://github.com/ethanplusai/jarvis | Personal/non-commercial visible | Referencia negativa: no copiar action system, runtime, memoria ni automatizacion. | Estudiado/no adoptado |
| `pmndrs/react-three-fiber` | https://github.com/pmndrs/react-three-fiber | MIT | Evaluado como ruta futura para escena declarativa. | No usado |
| `pmndrs/drei` | https://github.com/pmndrs/drei | MIT | Evaluados helpers tipo Sparkles/performance/HUD. | No usado |
| `pmndrs/react-postprocessing` | https://github.com/pmndrs/react-postprocessing | MIT | Evaluado bloom/postprocessing. | No usado |

## Codigo copiado/adaptado/reimplementado

No se copio codigo externo.

Lo tomado fue reimplementacion visual/conceptual sobre el Canvas 2D y CSS
existentes:

- distribucion volumetrica de particulas;
- pseudo-audio determinista para speaking;
- remolino/curl interno para thinking;
- selector Visual QA local;
- contratos `data-*` para tests.

No se copiaron runtimes, servidores, WebSocket externos, MCP, installers,
sensores automaticos, APIs externas, TTS/STT externos, microfono Web Audio,
plugins, memory systems ni ejecucion.

## Fallback

Si Canvas 2D no esta disponible, `JarvisOrb3D` mantiene el fallback CSS de
particulas (`jarvis-css-particle-sphere-fallback`). El error tecnico queda en
`data-canvas-error`; no se muestra un mensaje tecnico visible en el centro y no
se muestra un circulo negro.

## Que NO se implemento

No se implemento runtime ni capacidad peligrosa nueva.

- No Three/R3F/Drei/Postprocessing.
- Ninguna dependencia nueva.
- No Web Audio nuevo.
- No amplitud real nueva.
- No auto mic.
- No auto camera.
- No sensores nuevos.
- No backend upload.
- No audio bruto al backend.
- No frames al backend.
- No STT/TTS nuevo.
- No wake real activo.
- No MediaPipe/TFJS.
- No endpoint de ejecucion nuevo.
- No approve/reject real.

## Riesgos pendientes

- La validacion sigue siendo principalmente estatica; no hay pixel-diff
  automatizado ni captura browser obligatoria.
- 2600 particulas en Canvas 2D deben validarse en hardware viejo; el budget y
  reduced motion estan presentes, pero no sustituyen medicion real de FPS.
- La reactividad speaking es determinista, no audio real. Es intencional para
  mantener privacidad y evitar permisos nuevos.
- El fallback CSS cubre ausencia de Canvas 2D, pero no garantiza paridad visual
  completa con el renderer principal.

## Siguiente PR recomendada

PR #163 deberia ser Visual Browser Verification: Playwright o herramienta
equivalente para abrir `/jarvis`, forzar estados via `jarvisVisualPreview`,
tomar screenshots desktop/mobile, verificar canvas no blanco/no negro, revisar
fallback, reduced motion y comprobar que speaking/thinking/listening producen
firmas visuales diferentes sin sensores.
