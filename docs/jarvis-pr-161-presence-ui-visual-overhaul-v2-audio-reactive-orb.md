# PR #161 - Presence UI Visual Overhaul v2 + Audio-Reactive Orb

Fecha: 2026-06-18

## Resumen

PR #161 corrige la direccion visual de `/jarvis` despues de #160. La pantalla
sigue siendo visual/UI/presence dentro de Fase 1: JARVIS gobierna. Hermes
ejecuta. No se crea otro Hermes, no se duplica runtime, no se añade `/execute`,
no hay approve/reject real, no hay POST/PUT/DELETE desde `/jarvis` y no se
abren permisos peligrosos nuevos.

Contrato intacto: JARVIS gobierna. Hermes ejecuta.

La remodelacion se centra en presencia viva: fondo mucho mas oscuro, brillo
general contenido, esfera/nube de particulas frias como protagonista,
concentracion/nucleo azul-blanco solo emergente, estados visuales reactivos y
laterales mas premium/menos dashboard.

## Por que #160 fue insuficiente

#160 movio `/jarvis` hacia una pantalla orb-first, pero aun dejaba una lectura
demasiado uniforme:

- fondo, halo, particulas y nucleo vivian casi todos en el mismo cian;
- el glow estaba repartido por toda la escena, no concentrado en el centro;
- el nucleo no tenia suficiente contraste ni tono propio;
- los paneles laterales seguian pareciendo dashboard operativo;
- speaking/listening/thinking cambiaban estado, pero no se sentian
  suficientemente vivos;
- la presencia no tenia todavia una separacion visual agresiva/final de JARVIS.

## Que cambio visualmente

- Fondo de `/jarvis` movido a negro azulado/petroleo oscuro (`#00030a`), con
  grid y radiales mucho mas bajos.
- Capas de color explicitas:
  - fondo: `#00030a`;
  - halo exterior: cian/azul frio contenido;
  - particulas: cian/turquesa frio;
  - nucleo: azul-blanco luminoso `#e6fbff`;
  - approval/alert/error: canal calido/rojo separado.
- `JarvisOrb3D` deja de usar WebGL/shader como visual principal y renderiza una
  esfera de particulas en Canvas 2D puro.
- La escena principal declara `canvas-2d-particle-sphere-primary`,
  `no-webgl-primary`, `no-solid-core` y `no-central-jarvis-text` para que el
  contrato visual sea testeable.
- La concentracion central usa densidad emergente de particulas y un glow muy
  contenido, no una bola fija ni un logo.
- Estados visuales:
  `idle`, `wake_listening`, `listening`, `transcribing`, `thinking`, `speaking`,
  `approval_required`, `alert`, `error`, `stopped`, `executing`.
- Laterales marcados como paneles premium/minimos y plegados: status, contrato,
  approvals, camara, audio bruto y finance ya no compiten con el centro.
- Smart bar mas protagonista: transcripcion y respuesta humana siguen visibles,
  los detalles tecnicos siguen plegados y el boton de enviar sigue disabled.
- Camara lateral mas premium, ampliable y opt-in: no auto-start, no upload, no
  frames, no vision analysis.

## Correccion visual posterior a prueba en navegador

La primera iteracion de #161 oscurecio bien la escena y separo el nucleo, pero
dejo tres problemas: el nucleo se leia como una mancha blanca demasiado plana,
las particulas perdieron presencia y escribir/hablar no producia reaccion
visual clara.

La correccion mezcla lo mejor de #160 y #161:

- Se conserva el fondo mucho mas oscuro y los laterales discretos.
- Se recupera un campo visible de particulas cian/turquesa:
  - Canvas 2D dibuja 1420 particulas visibles en una esfera con profundidad;
  - `particleBudget` nunca queda en cero;
  - se añade una capa CSS de micro-particulas orbitando para que el campo siga
    vivo incluso si el canvas baja intensidad.
- El nucleo deja de ser una superficie blanca plana:
  - se reduce el area blanca directa;
  - el texto/logo central `JARVIS` se elimina del orbe;
  - se sustituye por concentracion emergente de particulas que se comprime o se
    diluye segun el estado.
- `listening`, `speaking`, `transcribing` y texto/transcripcion/respuesta local
  reciente suben energia de ondas, particulas y anillos sin Web Audio nuevo.

## Correccion particle sphere por referencias visuales nuevas

David paso referencias de una esfera JARVIS en movimiento: una nube de
particulas fria/blanca/cian, con centro energetico pequeño y picos radiales al
hablar. La direccion visual se corrigio otra vez para alejar el orbe de un
reactor circular plano:

- La geometria declarada ahora es `particle sphere / sphere of particles`.
- El renderer principal es Canvas 2D: 1420 particulas, profundidad simulada,
  tamanos/opacidades variables y rotacion orbital organica.
- `speaking` usa `speakingSpikeEnergy`, `radialSpikeEnergy` y una curva
  pseudo-audio determinista local: las particulas salen en picos radiales, la
  esfera se expande/contrae y aparecen ondas desde el centro.
- `thinking` usa `thinkingTurbulence`: remolino interno y movimiento no lineal
  distinto de speaking.
- `listening` usa `listeningFocus`: esfera mas concentrada, pulso fino y
  atencion sin explosion.
- `transcribing` usa `transcribingReflow`: superficie/reorganizacion controlada.
- Se añade capa CSS `jarvis-speaking-spike` como refuerzo visual de picos de
  habla. No captura audio, no usa Web Audio y no abre permisos.
- El bloque visual central se elimina: no queda texto, logo, placa de lectura ni
  bola fija. El centro aparece solo como concentracion temporal de particulas
  (`emergentCoreConcentration`) y se diluye cuando la esfera se expande.

## Correccion puntual: sin logo ni nucleo solido central

La correccion final de #161 quita la representacion visual fija de JARVIS dentro
del orbe. La UI general sigue mostrando JARVIS en header/smart bar cuando
corresponde, pero el centro del orbe ya no contiene:

- imagen o logo central;
- texto `JARVIS`;
- placa oscura fija;
- bola blanca fija;
- nucleo solido permanente.

En su lugar, `JarvisOrb3D` renderiza una concentracion de 84 particulas
emergentes (`jarvis-emergent-core-particle`) dentro de la particle sphere. Esa
concentracion aumenta en `listening`, `thinking` y `speaking`, y baja en `idle`
o `stopped`. El resultado esperado es que el centro exista solo cuando la nube
se comprime, y que desaparezca visualmente cuando las particulas se separan.

## Correccion definitiva: Canvas 2D particle sphere limpia

La version definitiva cambia de estrategia: no se sigue intentando arreglar el
shader/WebGL actual como visual principal. El centro usa Canvas 2D puro y deja
WebGL fuera del path visual principal:

- se eliminaron las lineas crosshair visibles;
- las marcas HUD heredadas quedan solo como contrato oculto, no como visual
  dominante;
- el texto tecnico inferior del orbe pasa a `sr-only` para dejar limpia la zona
  central;
- si Canvas 2D falla, no se muestra circulo negro ni mensaje tecnico visible:
  se renderiza una esfera CSS de 360 particulas
  (`jarvis-css-particle-sphere-fallback`) y el error queda solo en atributos
  ocultos/data;
- la esfera tiene tamaño dinamico por estado con `sphereScaleMin`,
  `sphereScaleMid`, `sphereScaleMax` y `jarvis-sphere-size-breathe`;
- `radialSpikeEnergy` permite picos fuertes en `speaking` y picos mas agresivos
  tambien en `alert/error`, manteniendo la estetica de particle sphere.

Contrato visual final: la escena central debe leerse como nube/esfera viva de
particulas blanco frio/azul hielo sobre fondo azul noche. No debe leerse como
logo, nucleo fijo, reactor circular ni HUD tecnico.

## Audio-reactive / voice-reactive

No se abrio Web Audio, no se captura amplitud nueva y no se pidieron permisos
nuevos. La reactividad usa señales ya disponibles:

- `localVoiceState`;
- `visualState`;
- borrador local reciente de la smart bar, solo como booleano visual temporal;
- transcripcion/respuesta local ya existente en frontend;
- `voice_session` / wake state del read model/event stream;
- `conversationActive`;
- approval/error/kill switch.

`useJarvisOrbState` traduce esos estados en energia visual:

- `idle`: respiracion lenta y particulas reducidas;
- `wake_listening`: atencion ligera;
- `listening`: pulso mas fino y particulas activas;
- `transcribing`: ondas contenidas;
- `thinking`: dinamica interna mas compleja;
- `speaking`: particulas/glow mas activos;
- texto/transcripcion/respuesta reciente: boost temporal de particulas/anillos
  sin enviar texto ni ejecutar nada;
- `approval_required`: canal calido separado;
- `error/alert`: cambio visual claro;
- `stopped`: estado calmado/apagado.

Esto cumple el objetivo de reaccion convincente sin auto-start de microfono, sin
audio bruto al backend y sin crear runtime nuevo.

## Repos externas estudiadas

| Repo | URL | Licencia visible | Que se tomo | Tipo | Por que no rompe JARVIS |
| --- | --- | --- | --- | --- | --- |
| `jincocodev/openclaw-jarvis-ui` | https://github.com/jincocodev/openclaw-jarvis-ui | ISC | Patrones de orbe con particulas, estados, power save y audio visualizer. | Reimplementacion visual | No se copio server, Gateway WS, TTS, tasks, memory ni system monitor. |
| `Suryansh777777/Jarvis-CV` | https://github.com/Suryansh777777/Jarvis-CV | No visible en la pagina revisada | Referencia de HUD AR, camara premium y composicion 3D. | Reimplementacion visual | No se adopto MediaPipe, face/hand tracking, Web Audio ni permisos automaticos. |
| `zoharbarzilai/Generative-3D-Audio-Visualizer` | https://github.com/zoharbarzilai/Generative-3D-Audio-Visualizer | No visible en la pagina revisada | Idea de esfera/reactividad/particulas/starfield. | Reimplementacion visual | No se copio Web Audio, microfono, playlist, PWA ni controles de audio. |
| `harsh-raj00/my-jarvis` | https://github.com/harsh-raj00/my-jarvis | MIT | Referencia de presencia cinematografica, particulas, anillos y estados voice. | Reimplementacion visual | No se adopto FastAPI, Gemini, ElevenLabs, plugins, email, smart home, WS runtime ni acciones. |
| `TheStack-ai/jarvis-orb` | https://github.com/TheStack-ai/jarvis-orb | MIT | Concepto de presencia/AI thinking visible en un orbe. | Reimplementacion conceptual | No se adopto MCP server, memoria, Tauri, installers ni brain paralelo. |
| `chevgan/react-ai-voice-visualizer` | https://github.com/chevgan/react-ai-voice-visualizer | MIT | Estados `idle/listening/thinking/speaking`, retina/perf budget, smoothing conceptual. | Reimplementacion visual | No se instalo el paquete ni hooks de microfono/Web Audio/VAD. |
| `ethanplusai/jarvis` | https://github.com/ethanplusai/jarvis | Personal/non-commercial visible | Referencia negativa para no copiar acciones reales ni memoria/action system. | Estudiado/no adoptado | No se adopto system action tags, Claude Code tasks, Mail/Calendar, browser automation ni memoria runtime. |
| `pmndrs/react-three-fiber` | https://github.com/pmndrs/react-three-fiber | MIT | Evaluado como ruta futura para escena declarativa React/Three. | Estudiado/no usado | No se añadio dependencia; Canvas 2D cubre esta correccion con menor riesgo. |
| `pmndrs/drei` | https://github.com/pmndrs/drei | MIT | Evaluados `AdaptiveDpr`, `PerformanceMonitor`, `Hud`, `Sparkles`. | Estudiado/no usado | No se añadio dependencia ni escena nueva. |
| `pmndrs/react-postprocessing` | https://github.com/pmndrs/react-postprocessing | MIT | Evaluado bloom/postprocessing/vignette. | Estudiado/no usado | No se añadio dependencia; glow simulado queda local en CSS/Canvas. |

No se copio codigo externo. Todo lo adoptado fue reimplementacion visual o
conceptual sobre los componentes existentes de Hermes/JARVIS.

## Dependencias añadidas

Ninguna dependencia nueva.

Motivo: la correccion definitiva necesitaba una esfera fiable que no dependiera
de shader/WebGL. Canvas 2D puro y CSS fallback resuelven el problema sin
lockfile churn, sin librerias visuales nuevas y con menor superficie de fallo.

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
2. Confirmar que el fondo es mucho mas oscuro y la esfera de particulas domina.
3. Probar estados del loop local de voz: idle, listening, transcribing,
   thinking, speaking y stop.
4. Confirmar que speaking/listening suben particulas/ondas sin pedir permisos
   nuevos fuera del boton manual.
5. Forzar Canvas 2D no disponible y confirmar fallback CSS de particulas sin
   mensaje tecnico visible.
6. Activar `prefers-reduced-motion` y confirmar que la escena baja movimiento.
7. Abrir camara solo con `Abrir`; confirmar no auto-start, no upload y stop.
8. Confirmar que la smart bar conserva respuesta humana, transcripcion y
   detalles plegados.

## Riesgos

- Canvas 2D dibuja 1420 particulas por frame en modo normal; el budget limita
  pixel ratio y frame rate, pero conviene validarlo en hardware viejo.
- La reactividad es state-driven, no amplitud real. Es intencional para no abrir
  permisos nuevos en esta PR.
- Sin screenshot automatizado todavia; los tests son contratos de fuente/build.
- Algunos detalles visuales se validan por marcadores y build, no por pixel diff.

## Performance budget

- `pixelRatio` limitado a `1.65` activo y `1.35` reposo.
- `particleBudget` por estado: stopped 900, idle 2400, texto local reciente
  3000, listening 3200, transcribing 3200, thinking 3500 y speaking 3800.
- `targetFrameMs` por estado: idle throttled, activo cercano a 60fps, stopped
  mas lento.
- `prefers-reduced-motion` baja frame rate, wave, reactividad y particulas.
- Particulas Canvas precomputadas; no se recrea la nube por frame.
- Fallback CSS si Canvas 2D no existe o falla el contexto.
- No se añadio postprocessing real ni libreria pesada.

## Que NO se implemento

- No Three/R3F/Drei/Postprocessing como dependencia nueva.
- No Web Audio nuevo.
- No captura de amplitud real nueva.
- No wake real activo.
- No STT/TTS nuevo.
- No MediaPipe/TFJS ni sensores nuevos.
- No camera/mic auto-start.
- No upload de audio, video o frames.
- No backend LLM/proveedor externo.
- No Hermes dispatch desde frontend.
- No approve/reject real.
- No deploy, email, Stripe, dinero, credenciales o lectura de `.env`.

## Siguiente PR recomendada dentro de Fase 1

PR #162 - Presence Visual QA + Browser Verification:

- Playwright/agent-browser screenshots desktop/mobile de `/jarvis`.
- Canvas nonblank check y fallback CSS de particulas automatizado.
- Snapshot visual de reduced motion.
- Medicion simple de frame budget en idle/listening/speaking.
- Ajustes responsive para pantallas medianas.
- Mantener exactamente el contrato: JARVIS gobierna, Hermes ejecuta, frontend no
  ejecuta Hermes y wake phrase nunca aprueba.
