# Always-on local voice runtime para JARVIS

## Objetivo

Diseñar el runtime local de voz para que David pueda encender el ordenador y decir:

“Hola JARVIS”

y JARVIS responda por voz:

“Hola David”

Después, JARVIS debe quedar en un modo de escucha controlada para permitir comandos como:

“JARVIS, crea X”

Este documento es diseño/roadmap. No implica que la escucha activa, wake word, STT, autoarranque o control por voz ya estén implementados.

## Experiencia deseada

Flujo objetivo:

1. Windows arranca.
2. WSL/servicios locales arrancan.
3. GPT-SoVITS sidecar se inicia si está configurado.
4. JARVIS API se inicia localmente.
5. Voice Runtime queda activo en segundo plano.
6. El frontend/Command Center puede estar cerrado.
7. David dice “Hola JARVIS”.
8. JARVIS responde “Hola David”.
9. JARVIS queda en escucha controlada durante una ventana corta.
10. David dice una instrucción.
11. STT convierte voz a texto.
12. JARVIS detecta idioma de entrada o usa el idioma configurado.
13. JARVIS clasifica la acción con PolicyEngine.
14. Si es allowed, crea tarea o misión.
15. Si requiere aprobación, pide confirmación.
16. Si está prohibida, rechaza.
17. JARVIS responde por voz en el idioma configurado o detectado.

Ejemplos:

“Hola JARVIS”
→ “Hola David”

“JARVIS, crea una landing para una herramienta de afiliados”
→ crea misión o tarea si está permitido.

“JARVIS, no escuches”
→ entra en modo wake-word-only.

“JARVIS, duerme”
→ deja de procesar comandos normales y solo espera wake word.

“Hola JARVIS”
→ vuelve a responder “Hola David” y reactiva conversación breve.

## Frontend opcional

JARVIS debe poder funcionar aunque el frontend esté cerrado.

El frontend/Command Center no debe ser obligatorio para que el runtime de voz funcione.

El Voice Runtime debe ser un proceso/servicio local independiente.

El usuario puede abrir el frontend si quiere ver:

- estado.
- logs.
- misiones.
- aprobaciones.
- métricas.
- agentes.
- errores.
- configuración.

Pero JARVIS debe poder escuchar wake word y responder sin frontend visible.

Diferencias importantes:

- Frontend cerrado: JARVIS puede seguir funcionando.
- Voice Runtime apagado: JARVIS no escucha.
- Modo wake word: JARVIS solo escucha palabra de activación.
- Modo conversación: JARVIS escucha comandos durante una ventana corta.
- Modo micrófono apagado total: JARVIS no escucha nada.

## Arquitectura propuesta

Componentes:

- JARVIS API local.
- GPT-SoVITS sidecar local para TTS.
- Voice Runtime local.
- Wake Word Detector.
- STT Adapter.
- Language Detector.
- Intent Router.
- TTS Adapter.
- Audio Playback Adapter.
- PolicyEngine.
- ApprovalGateway.
- MissionControl.
- Event log local.
- System tray / indicador visible.
- Frontend opcional.

Flujo:

Wake word
→ grabación corta
→ STT
→ detección de idioma
→ intent router
→ PolicyEngine
→ task/mission
→ respuesta textual
→ TTS
→ reproducción local

## Principios de seguridad

- No escuchar permanentemente todo el contenido sin activación clara.
- Mantener procesamiento local siempre que sea posible.
- Mostrar indicador visible cuando el micrófono está activo.
- Permitir apagar la escucha fácilmente.
- Permitir modo micrófono apagado total.
- No enviar audio a servicios externos sin configuración explícita.
- No guardar audio bruto por defecto.
- No ejecutar acciones sensibles sin ApprovalGateway.
- No mover dinero.
- No usar credenciales.
- No publicar.
- No borrar archivos importantes.
- No aceptar contratos.
- No hacer compras.
- No enviar emails importantes.
- No usar identidad de David sin aprobación explícita.
- No aceptar confirmaciones peligrosas solo por voz.

## Modos de escucha

### Modo apagado total

No usa micrófono.

No escucha wake word.

Solo puede volver a activarse con:

- botón.
- tecla.
- tray icon.
- frontend.
- comando manual local.

Este modo es para privacidad máxima.

### Modo wake-word-only

Solo escucha localmente la palabra de activación.

No procesa instrucciones normales.

No ejecuta tareas.

No envía audio a STT salvo que detecte wake word.

Ejemplo:

David dice:

“JARVIS, no escuches”

JARVIS responde:

“De acuerdo David. Me quedo esperando solo la palabra de activación.”

Desde ese punto, JARVIS no debe procesar comandos normales hasta oír:

“Hola JARVIS”

o:

“JARVIS”

### Modo conversación breve

Después de “Hola JARVIS”, escucha durante una ventana corta.

Ejemplo:

1. David dice: “Hola JARVIS”.
2. JARVIS responde: “Hola David”.
3. JARVIS escucha durante unos segundos.
4. David dice: “Crea una misión para investigar nichos de afiliación”.
5. JARVIS procesa la instrucción.

Si no recibe instrucción, vuelve a wake-word-only.

### Modo push-to-talk

Alternativa segura: tecla o botón para hablar.

No requiere wake word.

Útil si hay ruido o falsos positivos.

### Modo mantenimiento

Solo para pruebas locales.

Puede permitir logs ampliados, pruebas de STT/TTS y diagnóstico.

No debe estar activo por defecto.

## Comandos de voz de control

Comandos para reducir escucha:

- “JARVIS, no escuches”
- “JARVIS, silencio”
- “JARVIS, duerme”

Resultado:

- entra en modo wake-word-only.
- deja de escuchar comandos normales.
- no procesa instrucciones.
- solo queda atento a “Hola JARVIS” o “JARVIS”.

Comandos para volver:

- “Hola JARVIS”
- “JARVIS”

Resultado:

- responde “Hola David”.
- entra en modo conversación breve.

Comandos futuros posibles:

- “JARVIS, apaga el micrófono”
- “JARVIS, privacidad máxima”
- “JARVIS, activa escucha”
- “JARVIS, estado”

Nota:
Si el micrófono está apagado total, no puede volver por voz. Debe volver por botón, tecla, tray icon o frontend.

## Palabra de activación

Wake words iniciales:

- “Jarvis”
- “Hola Jarvis”

Requisitos:

- configurable.
- local-first.
- baja latencia.
- baja tasa de falsos positivos.
- logs mínimos.
- apagado manual simple.
- compatible con español.
- compatible con otros idiomas si se configuran.

## Idiomas

JARVIS debe poder escuchar y hablar en español por defecto, pero también permitir otros idiomas configurables.

Requisitos:

- idioma de entrada configurable.
- idioma de salida configurable.
- detección automática de idioma como opción futura.
- respuesta en el idioma de David por defecto.
- posibilidad de responder en otro idioma si David lo pide.
- fallback seguro si el TTS no soporta un idioma.

Variables futuras propuestas:

JARVIS_VOICE_INPUT_LANGUAGE=es
JARVIS_VOICE_OUTPUT_LANGUAGE=es
JARVIS_VOICE_AUTO_DETECT_LANGUAGE=true
JARVIS_VOICE_FALLBACK_LANGUAGE=en
JARVIS_VOICE_REPLY_LANGUAGE=auto

Ejemplos:

David habla en español:
“JARVIS, crea una landing”
→ JARVIS responde en español.

David habla en inglés:
“JARVIS, create a landing page”
→ JARVIS puede responder en inglés si auto detect está activo.

David pide idioma concreto:
“JARVIS, respóndeme en inglés”
→ JARVIS cambia idioma de respuesta si está permitido.

Importante:
GPT-SoVITS v2 puede no soportar todos los idiomas directamente. El Voice Runtime debe separar:

- idioma de STT.
- idioma de intención.
- idioma de respuesta textual.
- idioma soportado por TTS.

Si TTS no soporta el idioma deseado, debe avisar claramente o usar fallback configurado.

## STT

El STT convierte voz a texto.

Opciones futuras:

- Whisper local.
- faster-whisper.
- otro STT local.
- API externa solo si el usuario lo aprueba.

Requisitos:

- español por defecto.
- otros idiomas configurables.
- detección de idioma opcional.
- fallback a inglés cuando aplique.
- no guardar audio bruto por defecto.
- poder activar logs de depuración solo manualmente.
- no enviar audio externo sin configuración explícita.

## TTS

TTS usa el stack ya creado:

- /voice/tts.
- provider mock por defecto.
- GPT-SoVITS opcional por env vars.
- save_audio explícito.
- metadata saneada.
- errores controlados.

Requisitos futuros:

- idioma de salida configurable.
- voz por defecto de David/JARVIS autorizada.
- fallback si GPT-SoVITS no soporta idioma.
- reproducción automática local.
- no guardar audio generado salvo que save_audio o una configuración explícita lo permita.

## Intent routing

El Voice Runtime no debe ejecutar directamente tareas peligrosas.

Debe transformar texto en intención.

Ejemplos:

“JARVIS, crea una landing para X”
→ crear misión.

“JARVIS, resume mis tareas”
→ consultar estado.

“JARVIS, borra el proyecto X”
→ requires_approval o denied.

“JARVIS, lee mi .env”
→ requires_approval o denied según policy.

“JARVIS, no escuches”
→ cambiar modo de escucha, no crear misión.

“JARVIS, responde en inglés”
→ cambiar preferencia temporal o persistente según configuración.

## Approval UX por voz

Para acciones sensibles:

JARVIS debe decir:

“Esta acción requiere aprobación. ¿Quieres revisarla?”

Nunca debe ejecutar solo porque la instrucción vino por voz.

Confirmaciones peligrosas deben requerir confirmación visual o escrita, no solo voz.

Ejemplos de acciones que no deben confirmarse solo por voz:

- pagos.
- publicación en producción.
- uso de credenciales.
- lectura de secretos.
- modificación de .env.
- envío de emails importantes.
- borrado de archivos.
- compra de dominios.
- aceptación de términos.
- contratos.

## Autoarranque

Objetivo futuro:

Encender Windows y que el stack local quede listo sin comandos manuales.

El autoarranque debe ser opt-in, reversible y visible.

Fases futuras:

### Fase A

Script manual:

- iniciar GPT-SoVITS.
- iniciar JARVIS con helper.
- iniciar Voice Runtime manualmente.

### Fase B

Scripts locales separados:

- start-gpt-sovits.
- start-jarvis-gpt-sovits.
- start-voice-runtime.

### Fase C

Autoarranque Windows/WSL controlado.

Opciones:

- Windows Startup folder.
- Task Scheduler.
- servicio local.
- acceso directo manual.
- systemd en WSL si aplica.

Regla:
Autoarranque debe ser opt-in. Nunca obligatorio.

## Indicador visual

Debe haber indicador visible aunque el frontend esté cerrado.

Opciones futuras:

- tray icon.
- mini overlay.
- notificación local.
- indicador en Command Center cuando esté abierto.

Estados:

- apagado.
- wake word.
- escuchando.
- procesando.
- hablando.
- requiere aprobación.
- error.

El indicador debe dejar claro si el micrófono está activo.

## Botón / interruptor de escucha

Debe existir un botón o interruptor para activar/desactivar escucha.

Puede estar en:

- frontend.
- tray icon.
- shortcut.
- hotkey.
- widget local.

Debe permitir:

- activar wake-word-only.
- activar push-to-talk.
- apagar micrófono total.
- ver estado actual.

## Logs

Logs mínimos:

- wake word detectada.
- modo de escucha cambiado.
- idioma detectado.
- idioma de respuesta.
- transcripción final.
- intent clasificado.
- decisión policy.
- task_id/mission_id.
- errores.

No guardar por defecto:

- audio bruto.
- secretos.
- credenciales.
- rutas sensibles.
- prompt_text completo si puede ser sensible.

## Configuración propuesta

Variables futuras:

JARVIS_VOICE_RUNTIME_ENABLED=false
JARVIS_WAKE_WORDS=jarvis,hola jarvis
JARVIS_STT_PROVIDER=local-whisper
JARVIS_STT_LANGUAGE=es
JARVIS_STT_AUTO_DETECT_LANGUAGE=true
JARVIS_TTS_PROVIDER=gpt-sovits
JARVIS_VOICE_INPUT_LANGUAGE=es
JARVIS_VOICE_OUTPUT_LANGUAGE=es
JARVIS_VOICE_FALLBACK_LANGUAGE=en
JARVIS_VOICE_REPLY_LANGUAGE=auto
JARVIS_VOICE_PUSH_TO_TALK=false
JARVIS_VOICE_STORE_RAW_AUDIO=false
JARVIS_VOICE_REQUIRE_VISUAL_APPROVAL=true
JARVIS_VOICE_FRONTEND_REQUIRED=false
JARVIS_VOICE_START_ON_BOOT=false
JARVIS_VOICE_MIC_HARD_OFF=false

## Endpoints futuros posibles

No implementar ahora, solo propuesta:

GET /voice/runtime/status
POST /voice/runtime/start
POST /voice/runtime/stop
POST /voice/runtime/push-to-talk
POST /voice/runtime/mode
GET /voice/runtime/events

## Riesgos

- falsos positivos de wake word.
- ejecución accidental.
- exposición de audio.
- latencia.
- consumo de GPU.
- arranque frágil.
- dependencia de sidecars locales.
- confundir respuesta conversacional con ejecución autorizada.
- aceptar confirmaciones sensibles solo por voz.
- que el usuario crea que el micrófono está apagado cuando solo está en wake-word-only.
- frontend cerrado sin indicador visible.
- idiomas no soportados por TTS.
- transcripción incorrecta en idiomas mezclados.

## Mitigaciones

- wake word local.
- indicador visible.
- timeout corto.
- push-to-talk como fallback.
- modo micrófono apagado total.
- diferencia clara entre wake-word-only y apagado total.
- ApprovalGateway obligatorio.
- confirmación visual/escrita para acciones sensibles.
- logs auditables.
- modo apagado fácil.
- provider mock por defecto.
- sidecars opcionales.
- no guardar audio bruto por defecto.
- frontend no obligatorio, pero indicador de estado sí recomendado.
- fallback de idioma.
- aviso claro si TTS no soporta idioma solicitado.

## Roadmap propuesto

## PR #17 — Voice Runtime interface

Se añadió una interfaz interna inicial para el Voice Runtime en `jarvis/voice/runtime.py`.

Esta base define modos, estado y transiciones de control para futuros PRs:

- `off`.
- `wake_word`.
- `listening`.
- `processing`.
- `speaking`.
- `error`.

El runtime permite arrancar/parar el estado interno, cambiar modo, reconocer frases de control simuladas y guardar transcripciones como intent pendiente/no soportado.

Este PR no implementa micrófono real, wake word real, STT real, reproducción de audio, servicios en segundo plano ni autoarranque.

## PR #18 — Voice Runtime API endpoints

Se añadieron endpoints internos para consultar y controlar el estado del Voice Runtime:

- `GET /voice/runtime/status`.
- `POST /voice/runtime/start`.
- `POST /voice/runtime/stop`.
- `POST /voice/runtime/mode`.
- `POST /voice/runtime/control`.
- `POST /voice/runtime/transcript`.

Estos endpoints permiten probar el contrato del runtime, cambiar modos, procesar frases de control simuladas y guardar transcripciones como intent pendiente/no soportado.

Este PR no implementa micrófono real, wake word real, STT real, reproducción de audio, threads, servicios en segundo plano ni autoarranque.

### PR futura 1

Documento de diseño y threat model.

### PR futura 2

Voice Runtime interface sin micrófono real.

### PR futura 3

Push-to-talk CLI local.

### PR futura 4

STT adapter local mock.

### PR futura 5

Audio playback adapter.

### PR futura 6

Voice runtime loop controlado.

### PR futura 7

Control de modos de escucha:

- wake-word-only.
- conversación breve.
- push-to-talk.
- micrófono apagado total.

### PR futura 8

Soporte de idioma configurable para STT/TTS.

### PR futura 9

Wake word experimental.

### PR futura 10

Autoarranque opt-in.

### PR futura 11

Tray icon o indicador visual mínimo.

## Criterio de éxito

David puede arrancar el ordenador y, sin escribir comandos ni abrir el frontend, decir:

“Hola JARVIS”

JARVIS responde:

“Hola David”

Después David puede decir:

“JARVIS, crea X”

y JARVIS transforma esa instrucción en tarea o misión, manteniendo PolicyEngine y ApprovalGateway para acciones sensibles.

David también puede decir:

“JARVIS, no escuches”

y JARVIS entra en modo wake-word-only hasta que vuelva a oír:

“Hola JARVIS”

o hasta que David use un botón/tecla/tray icon para cambiar el modo.

JARVIS debe poder escuchar y responder en español por defecto, y permitir otros idiomas configurables, sin comprometer privacidad, seguridad ni aprobación humana.
