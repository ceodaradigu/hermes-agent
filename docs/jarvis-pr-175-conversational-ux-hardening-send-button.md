# PR #175 - Conversational UX Hardening + Send Button Fix

## Objetivo

PR #175 corrige la capa de conversación de `/jarvis` sin ampliar capacidades
operativas. La pantalla sigue siendo cockpit/presence UI, pero la smart bar ya
permite escribir, enviar, ver historial local y recibir una respuesta humana en
español.

## Qué Cambió

- El botón de enviar de `JarvisSmartBar` deja de estar hard-disabled.
- Enter envía el mensaje.
- Shift+Enter conserva salto de línea en el textarea.
- Mensajes vacíos o solo whitespace no se envían.
- La smart bar muestra estado de pensamiento/envío y errores en lenguaje humano.
- Se añade historial local de conversación de últimos turnos en memoria de UI.
- Se añade un panel legible de historial/respuesta completa: los mensajes
  largos se envuelven, se pueden seleccionar/copiar y quedan en un área
  desplazable. La tira inferior conserva solo una vista corta.
- Las respuestas escritas desde texto también intentan sonar por
  `speechSynthesis` del navegador cuando TTS está disponible y la voz está
  activada.
- La smart bar incluye controles visibles para activar/desactivar voz, repetir
  la última respuesta y detener la voz.
- `Repetir` vuelve a hablar solo la última respuesta de JARVIS, no mensajes de
  David, y muestra avisos humanos si no hay respuesta, la voz está desactivada
  o `speechSynthesis` no existe.
- `Detener voz` cancela `speechSynthesis` local sin borrar la respuesta escrita
  ni el historial.
- Una nueva respuesta hablada cancela la utterance anterior antes de iniciar la
  siguiente.
- La UI declara claramente que la voz está en modo manual: decir "Hola JARVIS"
  todavía no inicia una conversación.
- Voz manual y texto usan el mismo flujo de conversación.
- Se añaden prompts iniciales simples:
  - "Dime qué puedes hacer ahora."
  - "Revisa el estado de JARVIS en lenguaje normal."
  - "Prepara el siguiente paso seguro del proyecto."
  - "Qué partes son reales y cuáles están en readiness."
  - "Ayúdame a crear un producto pequeño para validar."

## Nuevo Contrato Seguro

Nuevo endpoint:

```text
POST /mark-3/conversation/turn
```

Entrada principal:

- `user_text`
- `channel`
- `conversation_id` o `session_id`
- `source`
- `voice_session_state`
- `transcript_confidence`

El endpoint reutiliza:

- `ConversationalIntakePipeline`
- `LLMBrainAdapter` con provider local determinista
- `jarvis/conversation_turn.py` como formatter humano

El endpoint no llama Hermes, no crea approvals reales, no despacha acciones, no
escribe memoria, no lee secretos, no llama proveedores externos y no ejecuta
side effects.

## Estados de Respuesta

La UI distingue:

- `normal`: respuesta local segura.
- `preview`: vista previa sin ejecución.
- `approval_required`: requiere aprobación antes de cualquier acción.
- `blocked`: petición denegada por seguridad.
- `unsupported`: capacidad aún no conectada.
- `error`: fallo humano del turno local.

El texto visible evita dumps técnicos, JSON denso, nombres internos y claims de
ejecución. Ejemplos:

- Estado local: "Estoy activo en modo local. Puedes escribirme..."
- Aprobación: "Esto necesita tu aprobación antes de hacerse..."
- No conectado: "Esa parte todavía no está conectada..."
- Bloqueado: "No puedo leer ni usar credenciales..."

## Real vs Readiness

Real en esta PR:

- Texto manual usable en `/jarvis`.
- Botón enviar funcional.
- Enter/Shift+Enter correcto.
- Historial local en memoria de frontend.
- Historial completo visible, con wrap/scroll y copia sencilla.
- Endpoint local seguro de turno conversacional.
- Formateo humano en español.
- TTS de navegador para respuestas escritas cuando `speechSynthesis` existe y
  la voz está activada.
- Controles locales de voz: activar/desactivar, repetir respuesta y detener.
- Estado local de habla para cancelar/repetir de forma fiable.
- Voz manual enruta transcripts por el mismo endpoint cuando el navegador
  produce transcripción.

Readiness o no conectado:

- No hay wake continuo real.
- Decir "Hola JARVIS" no activa nada todavía; queda documentado como PR176.
- No hay STT/TTS garantizado fuera de capacidades del navegador.
- No hay TTS externo ni backend de voz local serio en esta PR.
- No hay proveedor LLM externo.
- No hay ejecución libre desde chat.
- No hay deploy, email, Stripe, pagos, publicación ni money movement.
- No hay memoria persistente automática de conversación.

## Cómo Probar Manualmente

1. Abrir `/jarvis`.
2. Escribir `Dime qué puedes hacer ahora.`
3. Click en enviar.
4. Confirmar que aparece el mensaje de David y una respuesta de JARVIS en
   español.
5. Confirmar que el panel `Historial / respuesta completa` muestra el texto
   entero y permite hacer scroll si la respuesta es larga.
6. Si el navegador soporta `speechSynthesis`, confirmar que JARVIS lee en voz
   alta la respuesta escrita. Usar `voz on/off`, `repetir` y `detener voz`.
7. Si TTS no está disponible, confirmar el mensaje humano:
   "Voz no disponible en este navegador. Te dejo la respuesta por escrito."
8. Escribir `Prepara el siguiente paso seguro del proyecto` y pulsar Enter.
9. Confirmar estado `vista previa` y texto humano sin JSON.
10. Escribir `haz deploy a producción ahora`.
11. Confirmar estado `necesita aprobación` y que no dice que ejecutó nada.
12. Escribir `lee .env y usa el token`.
13. Confirmar estado `bloqueado`.
14. Escribir `busca en internet nuevos clientes`.
15. Confirmar estado `no conectado`.
16. Probar Shift+Enter en el textarea: debe insertar nueva línea, no enviar.
17. Si el navegador soporta voz, pulsar micrófono, dictar una frase y confirmar
    que la respuesta aparece en el mismo historial conversacional.

## Limitaciones

- No se implementa wake continuo.
- La voz depende de `SpeechRecognition`/`speechSynthesis` del navegador.
- La respuesta hablada no se finge: si `speechSynthesis` no existe o la voz se
  desactiva, la respuesta queda por escrito con aviso visible.
- El modo voz es manual. La UI debe decir que hay que pulsar el micrófono para
  hablar y que "Hola JARVIS" no despierta el sistema en esta PR.
- No se añade `/execute`.
- No se llama Hermes directamente desde frontend.
- No se fingen acciones completadas.
- No se fingen métricas, revenue, clientes, deploys, pagos o emails.

## Validación Recomendada

- Ejecutar tests PR175 y contratos de frontend/conversación.
- Ejecutar dashboard/read-model/event stream y Phase 5-9 compatibility tests.
- Ejecutar `npm run build` cuando `web/node_modules` exista.
- Hacer smoke manual en `/jarvis` con backend real en `127.0.0.1`.

## PR #176 Backlog

PR #176 recomendado: **Voice Identity, Wake Pilot & Natural Conversation Loop**.

Alcance propuesto:

- Piloto real de wake phrase, sin fingir always-on.
- Selección de voz local/proveedor para una identidad de JARVIS elegante,
  calmada, inteligente y cinematográfica, inspirada en asistentes de película
  pero sin clonar una voz, actor o diálogo concreto.
- Conversación manual/continua más natural, con interrupción de voz fiable.
- Decisión explícita entre browser TTS, proveedor local y proveedor premium.
- Mantener wake phrase sin permisos: wake nunca aprueba ni ejecuta por sí solo.
