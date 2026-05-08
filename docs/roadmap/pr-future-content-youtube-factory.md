# PR futuro — Content / YouTube Factory

## Objetivo

Documentar una futura fábrica de contenido para JARVIS enfocada en crear, validar y mejorar activos de contenido monetizable, especialmente canales de YouTube, Shorts, clips, guiones, miniaturas, narraciones y piezas reutilizables.

JARVIS debe poder convertir una oportunidad o nicho en un flujo de producción de contenido:

idea → investigación → guion → assets → voz → vídeo → revisión → publicación aprobada → medición → mejora.

## Casos de uso

- Crear canales nicho de YouTube.
- Generar ideas de vídeos.
- Analizar competencia.
- Crear guiones.
- Crear títulos y descripciones.
- Crear miniaturas.
- Generar imágenes o clips.
- Generar narraciones usando Voice Runtime Adapter.
- Crear Shorts.
- Crear intros/outros.
- Preparar calendarios de contenido.
- Medir rendimiento.
- Reutilizar contenido en varias plataformas.
- Crear contenido para afiliación.
- Crear contenido educativo.
- Crear contenido para validar microSaaS o productos digitales.

## Arquitectura deseada

JARVIS Core
→ Mission Control
→ Content Factory
→ adapters de generación
→ revisión humana
→ publicación aprobada
→ métricas
→ mejora

La Content Factory no debe vivir dentro del core como lógica pesada.
Debe coordinar adapters externos o internos de forma desacoplada.

## Candidatos de herramientas/adapters

### Open Generative AI

Uso potencial:
- estudio visual generativo.
- generación de imágenes.
- generación de vídeos.
- lip sync.
- clips cinematográficos.
- assets para Shorts.
- assets para YouTube.
- miniaturas o conceptos visuales.

Notas:
- Tratar como servicio externo o herramienta controlada.
- No meterlo directamente en el core.
- Revisar si depende de APIs externas como Muapi.
- Si usa APIs externas, debe quedar claro en configuración y permisos.
- No enviar imágenes, voces o datos sensibles sin aprobación.

### Voice Runtime Adapter

Uso potencial:
- narraciones.
- voz de JARVIS.
- podcasts.
- locuciones.
- intros/outros.
- doblaje.
- voz para Dominion / Overdrive Mode.

La publicación o uso comercial de audio generado requiere Approval Gate.

### Herramientas futuras

- Generadores locales de imagen.
- Generadores locales de vídeo.
- Editores de vídeo automatizados.
- ComfyUI u otros pipelines locales.
- APIs autorizadas de YouTube.
- APIs de analítica.
- Herramientas SEO.
- Sistemas de thumbnails A/B.
- Herramientas de scheduling.

## Scope inicial del futuro PR

### Must

- Documentar modelo de Content Mission.
- Definir flujo de creación de vídeo.
- Definir riesgos de publicación.
- Definir Approval Gate para publicar.
- Definir Approval Gate para campañas de pago.
- Definir Approval Gate para uso de identidad, voz o imagen.
- Definir estructura futura para adapters.
- Añadir tests solo cuando haya código en PR posterior.

### Should

- Preparar integración futura con Mission Control.
- Preparar integración futura con Voice Runtime Adapter.
- Preparar integración futura con Money Engine.
- Preparar métricas de rendimiento.
- Preparar sistema de revisión humana.
- Preparar análisis de ROI por pieza de contenido.

### Won’t

- No publicar automáticamente.
- No crear canales reales sin aprobación.
- No gastar dinero sin aprobación.
- No usar caras/personas reales sin permiso.
- No clonar voces de terceros.
- No generar deepfakes engañosos.
- No suplantar identidades.
- No manipular personas de forma encubierta.
- No explotar tragedias o crisis.
- No infringir copyright.
- No depender de una sola herramienta externa.

## Approval Gate

Deben requerir aprobación explícita:

- Crear o modificar un canal real.
- Publicar vídeo.
- Programar publicación.
- Borrar contenido.
- Cambiar branding público.
- Usar voz generada en contenido monetizado.
- Usar imagen o cara de una persona.
- Usar marcas registradas.
- Lanzar campañas de pago.
- Gastar dinero en ads.
- Enviar assets a APIs externas.
- Usar contenido sensible o polémico.
- Hacer claims médicos, financieros o legales.

## Protocolo de publicación

Antes de publicar, JARVIS debe mostrar:

- plataforma.
- canal.
- título.
- descripción.
- thumbnail.
- duración.
- assets usados.
- voz usada.
- riesgos.
- monetización esperada si aplica.
- si hay contenido sensible.
- si hay gasto asociado.
- acción exacta que se va a ejecutar.

Ejemplo:

"Acción sensible: publicar vídeo en YouTube.
Canal: canal nicho afiliación.
Título: Las 5 mejores herramientas IA para estudiantes.
Visibilidad: privado / no listado / público.
Gasto asociado: 0 €.
Riesgo: bajo.
¿Autorizas publicar este vídeo?"

Si hay gasto:

"Acción sensible: campaña de promoción.
Plataforma: YouTube Ads.
Presupuesto propuesto: 20 €.
Límite máximo autorizado: 20 €.
Duración: 24 horas.
¿Autorizas gastar exactamente 20 €?"

## Métricas futuras

JARVIS debe medir:

- views.
- CTR.
- retención.
- watch time.
- subscriptores ganados.
- ingresos.
- leads.
- clics afiliados.
- conversiones.
- coste por vídeo.
- beneficio por hora humana requerida.
- ROI por canal.
- ROI por formato.
- señales de abandono o duplicación.

## Relación con Money Engine

La Content Factory debe priorizar contenido con posibilidad real de retorno.

Criterios:

- potencial de monetización.
- dificultad.
- competencia.
- velocidad de validación.
- coste de producción.
- riesgo legal.
- vida útil del contenido.
- posibilidad de reutilización.
- potencial SEO.
- potencial afiliación.
- potencial de producto propio.

## Relación con Dominion / Overdrive Mode

Dominion Mode puede usarse como capa visual/conversacional para supervisar la Content Factory con tono más agresivo y estratégico.

Pero no cambia las reglas:

- no publica sin aprobación.
- no gasta sin aprobación.
- no usa identidad sin aprobación.
- no oculta acciones.
- no salta PolicyEngine.
- no salta ApprovalGateway.

## Riesgos

- Copyright.
- Reutilización de contenido protegido.
- Claims falsos.
- Deepfakes.
- Uso de caras/personas sin permiso.
- Uso de voces sin consentimiento.
- Dependencia de APIs externas.
- Costes de generación.
- Baneo de plataformas.
- Contenido de baja calidad.
- Automatización excesiva.
- Daño reputacional.
- Monetización débil.

## Decisión

JARVIS debe poder crear contenido, pero no debe publicar ni gastar sin aprobación humana.

La Content / YouTube Factory debe construirse después de:

1. Mission Control.
2. Voice Runtime Adapter.
3. Command Center base o integración mínima de revisión.
4. Adapters de generación controlados.
5. Sistema de métricas.
