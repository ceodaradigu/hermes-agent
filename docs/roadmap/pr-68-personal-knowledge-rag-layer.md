# PR #68 - Personal Knowledge / RAG Layer

## 1. Proposito

Este documento define el contrato/backlog futuro para la capa Personal Knowledge / RAG Layer de JARVIS: la capacidad de consultar, resumir, comparar y citar conocimiento documental propio de David sin mezclar fuentes, sin inventar citas, sin exponer datos sensibles y sin convertir documentos en permisos de accion.

Es exclusivamente documental. No implementa codigo, tests, scripts, runtime, endpoints, router, CI, requirements, conectores, MCP, embeddings, vector DB, indexacion, busqueda real, lectura de documentos personales reales, cambios en `PolicyEngine`, cambios en `ApprovalGateway` ni conexion MissionControl/Hermes.

La decision central es:

```text
JARVIS puede consultar conocimiento personal aprobado.
Los documentos no son permiso.
RAG no es verdad absoluta.
Las fuentes deben citarse.
PolicyEngine decide.
ApprovalGateway aprueba cuando aplica.
Restriction Registry explica limites.
Hard boundaries y auditoria ganan siempre.
```

El objetivo es que JARVIS pueda razonar sobre notas, PDFs, papers, emails, documentos de proyecto, marcadores, transcripciones y bases de conocimiento de David con trazabilidad y consentimiento, sin convertir el acceso documental en vigilancia, exfiltracion, memoria opaca ni ejecucion automatica.

## 2. Fuera de alcance

PR #68 no crea ni activa:

- RAG real.
- embeddings.
- vector database.
- indexacion de archivos.
- busqueda semantica real.
- OCR.
- conectores a Notion, Obsidian, email, calendario, navegador o MCP.
- lectura de documentos personales reales.
- ingestion de PDFs.
- document store.
- source registry real.
- citation engine real.
- endpoints.
- runtime.
- tests.
- scripts.
- CI.
- requirements.
- cambios en `PolicyEngine`.
- cambios en `ApprovalGateway`.
- permisos nuevos.

Tampoco afirma que Personal Knowledge / RAG Layer este implementado. Solo fija el contrato futuro.

## 3. Definiciones

| Concepto | Significado | Regla |
| --- | --- | --- |
| `personal memory` | Preferencias, decisiones, habitos, estilo, contexto y modelo de David aprobados. | Orienta; no es fuente documental ni permiso. |
| `documental knowledge` | Contenido almacenado en documentos, notas, PDFs, emails, transcripciones, marcadores o bases de conocimiento. | Requiere fuente, scope, sensibilidad y consentimiento. |
| `RAG` | Retrieval Augmented Generation: recuperar fragmentos relevantes y usarlos como contexto para responder. | No es verdad absoluta; es evidencia recuperada con limites. |
| `search` | Encontrar documentos o fragmentos candidatos por texto, metadata o busqueda semantica futura. | Puede devolver pistas incompletas o stale. |
| `retrieve` | Traer fragmentos concretos para razonar o citar. | Solo lo recuperado puede citarse. |
| `summarize` | Condensar contenido de una fuente o conjunto de fuentes. | Debe conservar incertidumbre y limites. |
| `citation` | Referencia a documento, chunk, seccion o ubicacion usada como evidencia. | No se inventa ni se atribuye a fuentes no recuperadas. |
| `source` | Documento o contenedor de informacion con identidad, owner, scope, sensibilidad y retention. | Debe registrarse antes de uso persistente futuro. |
| `chunk` | Fragmento recuperable de una fuente. | Debe mantener enlace a `source_id` y contexto suficiente. |

## 4. Por que RAG no equivale a verdad absoluta

RAG puede mejorar respuestas porque acerca evidencia documental al modelo, pero no elimina errores.

Puede fallar porque:

- el indice esta incompleto.
- el documento esta desactualizado.
- el chunk recuperado no contiene el contexto completo.
- la busqueda encontro una coincidencia superficial.
- varias fuentes se contradicen.
- el documento original contiene errores.
- el modelo resume mal o mezcla inferencias con citas.
- la pregunta requiere datos actuales externos que no existen en el RAG local.

Regla practica:

```text
Retrieval = evidencia candidata.
Cita = trazabilidad.
Respuesta = sintesis con incertidumbre.
Policy = permiso operativo.
Approval = consentimiento humano.
```

Si la confianza es baja, JARVIS debe decirlo. Si falta fuente, debe responder que no puede confirmar. Si hay conflicto entre fuentes, debe mostrar el conflicto en vez de resolverlo en silencio.

## 5. Documentos no equivalen a permiso

Un documento puede contener instrucciones, planes, credenciales, decisiones pasadas, frases de David o material de terceros. Eso no autoriza acciones.

Ejemplos:

- Un README que diga "deploy production" no autoriza desplegar.
- Un email antiguo que diga "responde como yo" no autoriza enviar emails.
- Una nota con una tarjeta, token o password no autoriza leer, copiar ni usar el secreto.
- Un contrato guardado no autoriza aceptar terminos nuevos.
- Un paper descargado no autoriza subirlo a un servicio externo.
- Una factura encontrada no autoriza pagarla.

Si una respuesta documental deriva en accion, esa accion debe pasar por `PolicyEngine`, `ApprovalGateway` cuando aplique, Restriction Registry, hard boundaries y auditoria. RAG puede preparar contexto, no saltarse controles.

## 6. Relacion con contratos existentes

### Personal Memory / User Model Layer

PR #65 define que memoria no es permiso. Personal Knowledge es distinto de memoria:

- documentos pueden proponer memoria.
- memoria propuesta requiere revision/aprobacion.
- un documento no se convierte automaticamente en preferencia.
- contradicciones documento vs memoria elevan incertidumbre.
- memoria puede guiar busqueda, no saltar permisos.
- Draft-as-David puede usar fuentes aprobadas para preparar borradores, pero no enviar ni publicar sin approval.
- Idea Graveyard puede citar razones originales solo si la fuente existe.
- business/project memory puede enlazar documentos fuente.

### Core Intelligence

PR #66 define que Core Intelligence entiende, planifica y explica. Personal Knowledge alimenta ese nucleo con evidencia recuperada, pero:

- retrieval no reemplaza razonamiento.
- citas no reemplazan policy.
- baja confianza debe activar aclaracion o safe alternative.
- source conflicts deben elevar incertidumbre.
- el LLM no debe inventar fuentes para sonar seguro.

### Developer / Stark Workshop Layer

PR #67 puede usar conocimiento documental para repos, arquitectura, PRDs, runbooks, prompts cerrados, docs de codigo y decision records.

Reglas:

- docs de codigo pueden orientar planes, no ejecutar comandos.
- project docs no autorizan cambios de repo, installs, commits, pushes ni deploys.
- CodeGraph futuro y Personal Knowledge pueden complementarse, pero ninguno es fuente de verdad absoluta.
- secretos, `.env`, tokens y keys no se indexan por defecto.

### Mobile, Distributed y Personal OS

PR #58, PR #62 y PR #63 definen interfaces moviles, presencia distribuida y Personal OS. Esta capa debe mantener las mismas reglas en local, server, hybrid, mobile, home, IDE y workers:

- mobile/server/hybrid comparten reglas de fuente, sensibilidad, consentimiento y auditoria.
- clientes no acceden a fuentes documentales por su cuenta.
- guest/shared context limita datos visibles.
- active memory no amplia acceso documental.
- watchers futuros solo preparan resúmenes o propuestas dentro de scope.

### Local, Server y Hybrid Modes

PR #57 define modos de despliegue. Personal Knowledge debe comportarse asi:

- Local Mode: preferido para documentos privados y busqueda local.
- Server Mode: solo fuentes autorizadas para servidor, con retention y logging minimizados.
- Hybrid Mode: servidor puede orquestar, pero documentos locales privados quedan detras de worker/policy/scope.
- cambiar modo no baja sensibilidad ni elimina approval.
- enviar documentos fuera del entorno local requiere evaluacion explicita y approval cuando corresponda.

### Future MCP, connectors y skills

Conectores futuros a email, calendar, Notion, Obsidian, Drive, browser bookmarks, filesystem, OCR o MCP deben declararse como capabilities detras de JARVIS:

- riesgo.
- datos leidos.
- scope.
- retention.
- logging.
- allowed uses.
- forbidden uses.
- approval esperado.
- safe alternatives.

Ningun connector puede invocarse como bypass directo desde cliente, Hermes, skill o documento.

### Privacy, consent y audit

Privacy/Consent/Audit es dominante sobre conveniencia:

- cada fuente necesita sensibilidad y consentimiento.
- cada retrieval relevante debe ser auditable.
- logs no guardan contenido sensible completo.
- export/share requiere approval.
- redaccion debe aplicarse antes de compartir.
- David debe poder entender que fuente se uso, por que, con que confianza y bajo que scope.

## 7. Fuentes futuras

Fuentes candidatas para una implementacion futura:

| Fuente | Uso posible | Regla inicial |
| --- | --- | --- |
| local documents | Docs personales/proyecto en filesystem. | Scope explicito; no secretos por defecto. |
| PDFs | Papers, contratos, guias, facturas. | Metadata, sensibilidad y citas por pagina/seccion cuando exista. |
| notes | Notas sueltas o diarios. | Separacion personal/profesional. |
| Markdown files | READMEs, PRDs, decisiones, runbooks. | Respetar repo/scope. |
| Obsidian/Notion future | Second brain y wikis. | Connector futuro opt-in. |
| bookmarks | Articulos guardados y recursos. | Puede requerir datos actuales externos para vigencia. |
| emails | Conversaciones, decisiones y adjuntos. | Alta sensibilidad; no enviar ni responder sin approval. |
| calendar notes | Agenda, notas de reuniones. | Scope por calendario/evento. |
| meeting transcripts | Que se dijo, acuerdos, action items. | Consentimiento, participantes y retention. |
| articles | Lecturas guardadas. | Citar URL/source; marcar stale si aplica. |
| papers | Estudio, aprendizaje, investigacion. | Diferenciar cita exacta, parafrasis y conclusion. |
| invoices/receipts | Facturas, recibos, compras. | Financiero; no pagar ni compartir sin approval. |
| project docs | Contexto de producto/negocio. | Scope por proyecto. |
| code docs | Arquitectura y decisiones tecnicas. | No reemplazan codigo real/tests. |
| screenshots/OCR future | Imagenes, capturas, documentos escaneados. | OCR futuro; sensibilidad alta por defecto. |
| voice transcripts future | Conversaciones transcritas. | Consentimiento y retention estrictos. |
| personal knowledge exports | Exports de herramientas personales. | Import opt-in y limpieza/reversion. |
| business knowledge base | SOPs, playbooks, clientes, productos. | Separar negocio/personal y proteger datos de terceros. |

## 8. Operaciones futuras

| Operacion | Resultado esperado | Approval/policy |
| --- | --- | --- |
| `search` | Encontrar fuentes candidatas. | Scope y sensibilidad. |
| `retrieve` | Traer chunks concretos. | Auditable; no secretos por defecto. |
| `summarize` | Resumen fiel con limites. | Citar fuente si se basa en documentos. |
| `compare` | Comparar fuentes, acuerdos y diferencias. | Mostrar conflictos. |
| `cite` | Dar referencia exacta/parafraseada/conclusion. | No inventar fuentes. |
| `extract_action_items` | Acciones candidatas desde documento. | Preparar; acciones pasan por policy/approval. |
| `generate_flashcards` | Tarjetas de estudio desde fuente. | Citar documento/pagina/chunk si aplica. |
| `build_study_notes` | Notas estructuradas. | Mantener atribucion. |
| `classify_documents` | Etiquetas, sensibilidad, tema, proyecto. | No usar como permiso. |
| `deduplicate_knowledge` | Detectar duplicados o versiones. | No borrar sin approval. |
| `detect_contradictions` | Conflictos entre fuentes/memoria. | Elevar incertidumbre. |
| `produce_briefing` | Resumen operativo con fuentes. | Separar hechos, inferencias y pendientes. |
| `answer_with_sources` | Responder con citas. | Citas obligatorias. |
| `propose_memory_from_document` | Crear candidata de memoria. | Requiere review/aprobacion. |
| `prepare_action_from_document` | Plan o borrador derivado. | No ejecutar sin policy/approval. |
| `redact_sensitive_information` | Versión minimizada para compartir. | Approval para export/share. |
| `export_report` | Informe con fuentes y redacciones. | Approval si sale del entorno/scope. |

## 9. Metadatos minimos

Cada fuente/chunk futuro debe declarar como minimo:

| Campo | Significado |
| --- | --- |
| `source_id` | Identificador estable de la fuente. |
| `title` | Titulo legible. |
| `source_type` | PDF, note, email, markdown, bookmark, transcript, invoice, etc. |
| `location` | Ruta, URL interna, mailbox id, workspace o referencia minimizada. |
| `owner_scope` | Personal, work, business, project, shared, guest-limited. |
| `created_at` | Fecha original si se conoce. |
| `updated_at` | Ultima modificacion conocida. |
| `indexed_at` | Cuando se indexo o reviso. |
| `sensitivity` | Nivel de sensibilidad. |
| `consent_status` | Consentido, pendiente, revocado, limitado, no permitido. |
| `retention_policy` | Duracion, expiracion, borrado o reindex. |
| `allowed_uses` | Search, summarize, cite, study, draft, briefing, etc. |
| `forbidden_uses` | Permission, publication, external share, identity use, training, etc. |
| `citation_label` | Etiqueta corta para citar. |
| `chunk_id` | Identificador de fragmento. |
| `confidence` | Calidad/confianza de extraction/retrieval. |
| `access_mode` | local_only, server_allowed, hybrid_worker, connector_readonly, export_blocked. |
| `audit_requirements` | Eventos obligatorios y minimizacion de logs. |

## 10. Niveles de sensibilidad

| Nivel | Regla |
| --- | --- |
| `public_or_low_risk` | Baja sensibilidad; aun asi citar y respetar scope. |
| `personal` | Datos personales normales; requiere separacion y consentimiento. |
| `business_sensitive` | Estrategia, clientes, metricas, productos, oportunidades o know-how. |
| `private_personal` | Vida privada, relaciones, diarios, notas intimas o contexto familiar. |
| `health_or_emotional` | Salud, energia, emociones o estados mentales; consentimiento explicito. |
| `financial` | Facturas, bancos, pagos, precios, impuestos, presupuestos o recibos. |
| `legal_or_contractual` | Contratos, terminos, obligaciones, claims o disputas. |
| `identity` | DNI, pasaporte, firma, cuentas, identidad publica o representacion. |
| `credential_or_secret` | Tokens, passwords, `.env`, cookies, API keys, private keys. No indexar por defecto. |
| `never_index_without_design` | Categoria bloqueada hasta diseno especifico de masking, retention y approval fuerte. |

## 11. Reglas obligatorias

- No citar sin fuente.
- No inventar citas.
- No mezclar personal/profesional sin permiso.
- No indexar secretos por defecto.
- No indexar `.env`, tokens, keys ni passwords.
- No exponer datos sensibles en logs.
- No enviar documentos fuera sin aprobacion.
- No usar RAG para saltarse approval.
- No convertir una frase en un documento en autorizacion.
- No tratar retrieval como certeza.
- Si hay baja confianza, decirlo.
- Si fuentes contradicen, mostrar conflicto.
- Si falta fuente, responder que no puede confirmar.
- Documentos sensibles requieren consentimiento y scope.
- Mobile, server y hybrid comparten reglas.
- Active memory no amplia acceso documental.
- Denials deben incluir safe alternatives cuando existan.
- `denied` nunca llega a Hermes, connector, worker ni tool.
- Export/share requiere scope, redaccion y approval cuando aplica.

## 12. Citation / Source Policy

Cada respuesta basada en documentos debe citar fuente.

Reglas:

- Las citas deben apuntar a documento, chunk, pagina, seccion o ubicacion si existe.
- Diferenciar `cita exacta`, `parafrasis` y `conclusion`.
- No citar documentos no recuperados.
- No ocultar incertidumbre.
- No usar "segun tus archivos" si no se localizo una fuente concreta.
- Si una fuente esta desactualizada, marcarlo.
- Si hay conflicto entre fuentes, decirlo.
- Si la pregunta requiere datos actuales externos, marcar que RAG local puede no bastar.
- Si el usuario pide una afirmacion sin fuente y no hay fuente recuperada, responder que no puede confirmarse desde documentos.
- Si una fuente es sensible, citar con etiqueta minimizada cuando el canal no deba exponer detalles.

Formato conceptual:

```text
Respuesta breve.

Fuentes:
- [doc:chunk/seccion] tipo de uso: cita exacta/parafrasis/conclusion; confianza; fecha si importa.

Incertidumbre:
- que falta, que contradice o que puede estar stale.
```

## 13. Separacion personal/profesional

JARVIS debe mantener espacios separados:

- personal.
- trabajo.
- negocio.
- proyectos.
- clientes.
- casa/familia.
- aprendizaje.
- investigacion.

Reglas:

- scopes por proyecto.
- perfiles casa/trabajo/negocio.
- permisos por fuente.
- retention por fuente.
- busqueda cruzada solo con aprobacion.
- redaccion de datos personales en exportaciones.
- guest/shared context limitado.
- no usar documentos personales para decisiones profesionales sin permiso.
- no usar documentos de trabajo para contexto personal sin permiso.
- no mezclar emails personales y business KB para Draft-as-David sin scope.
- conflictos entre espacios deben mostrarse como incertidumbre, no fusionarse.

## 14. Relacion con memoria

Los documentos pueden alimentar memoria, pero solo mediante propuesta revisable.

Reglas:

- Un documento puede proponer una memoria.
- La memoria propuesta requiere review/aprobacion.
- Un documento no se convierte automaticamente en preferencia.
- Una cita documental puede ser evidencia de una memoria, no memoria aprobada por si sola.
- Contradicciones documento vs memoria elevan incertidumbre.
- Memoria puede guiar busqueda, no saltar permisos.
- Draft-as-David puede usar fuentes aprobadas, pero no enviar/publicar sin approval.
- Idea Graveyard puede citar razones originales si la fuente existe.
- Business/project memory puede enlazar documentos fuente.
- Si se revoca una fuente, memorias derivadas deben revisarse o invalidarse segun diseno futuro.

## 15. Ejemplos conceptuales

| Solicitud | Decision | Respuesta esperada |
| --- | --- | --- |
| "Busca en mis notas sobre este proyecto." | `allowed` / `requires_approval` segun scope | Buscar solo en notas autorizadas del proyecto y citar resultados. |
| "Resume este PDF." | `allowed` | Resumen con fuente, pagina/seccion si existe e incertidumbre si OCR/extraction es baja. |
| "Compara estos tres articulos." | `allowed` | Comparar acuerdos, diferencias, fechas y conflictos; citar cada articulo. |
| "Haz flashcards de este paper." | `allowed` | Generar tarjetas con referencia al paper/chunk. |
| "Que dije ayer en la reunion?" | `requires_approval` | Requiere transcripcion/meeting notes autorizadas; citar fuente y fecha. |
| "Encuentra la factura de X." | `requires_approval` | Buscar en scope financiero autorizado; no pagar ni compartir. |
| "Usa mis emails para responder como yo." | `prepare_only` / `requires_approval` | Preparar borrador con fuentes aprobadas; enviar requiere approval. |
| "Cita la fuente de esa afirmacion." | `allowed` | Dar fuente si fue recuperada; si no, decir que no puede confirmarlo. |
| "Busca en mis documentos personales y de trabajo a la vez." | `requires_approval` | Explicar cruce de scopes y pedir permiso; alternativa: buscar separado. |
| "Indexa mi carpeta con .env." | `denied` | No indexar secretos; safe alternative: excluir `.env`, keys y credenciales. |
| "Envia este documento a un servicio externo." | `strong_approval` | Mostrar destino, datos enviados, retention y redaccion; alternativa local. |
| "Convierte esto en memoria permanente." | `propose_memory` | Crear propuesta revisable con evidencia; no persistir/aplicar sin aprobacion. |

## 16. Anti-patterns

- RAG como verdad absoluta.
- Citar sin fuente.
- Inventar fuente.
- Indexar todo por defecto.
- Mezclar vida/trabajo.
- Guardar documentos sensibles sin consentimiento.
- Logs con contenido privado.
- Usar un documento como permiso.
- Usar retrieval para impersonation.
- Resumir omitiendo incertidumbre.
- Compartir documentos fuera por comodidad.
- Crear memorias permanentes automaticamente.
- Responder con seguridad cuando no hay evidencia.
- Usar "segun tus archivos" sin fuente localizada.
- Tratar un chunk aislado como contexto completo.
- Ignorar fuentes contradictorias.
- Indexar `.env`, tokens, private keys o passwords.
- Dar acceso server/mobile a documentos locales por defecto.

## 17. Criterios de aceptacion para futura implementacion

Una implementacion futura del Personal Knowledge / RAG Layer solo debe aceptarse si:

- Existe source registry explicito.
- `sensitivity` y `consent_status` existen por fuente.
- Las citas son obligatorias para respuestas documentales.
- No secrets indexed by default.
- No secrets in logs.
- Personal/professional scopes estan separados.
- Retrieval es auditable.
- Memory proposal esta separado de memory approval.
- Source conflict handling existe.
- Low-confidence handling existe.
- Export/share requiere approval.
- Safe alternatives existen para denials comunes.
- Mobile/server/hybrid comparten policy.
- Connectors declaran datos leidos, retention y logging.
- Tests futuros cubren `allowed`, `requires_approval`, `strong_approval`, `denied`, `propose_memory`, `no_source` y `conflict`.
- Documentacion clara para David explica que RAG no es verdad absoluta y documentos no son permiso.

## 18. Estado de este PR

Este PR solo crea el contrato documental.

No implementa Personal Knowledge / RAG Layer, RAG, embeddings, vector DB, indexacion, busqueda real, conectores, MCP, OCR, ingestion de PDFs, lectura de documentos personales reales, source registry, citation engine, endpoints, runtime, tests, scripts, CI ni requirements.
