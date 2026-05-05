# JARVIS Architecture (MVP Foundation)

## Qué es JARVIS
JARVIS es un sistema personal de agentes IA para uso exclusivo de David, orientado a crear activos digitales y automatizaciones bajo supervisión humana.

## Qué papel tiene Hermes
Hermes Agent actúa como runtime interno de ejecución (conversación + tools). JARVIS añade una capa ligera de integración y gobernanza, sin reescribir Hermes ni alterar su comportamiento base.

## Por qué JARVIS no es un SaaS público
No es multi-tenant ni producto comercial. Es una infraestructura personal, con políticas de riesgo específicas y control humano explícito.

## Acciones que requieren aprobación
- usar credenciales
- leer `.env`
- borrar archivos
- instalar paquetes
- publicar en producción
- comprar dominios
- lanzar campañas de pago
- enviar emails masivos
- aceptar términos
- pagos
- bancos
- DNI o datos legales

## Acciones prohibidas siempre
- exfiltrar secretos
- saltarse aprobaciones
- ocultar acciones al usuario
- modificar claves/credenciales sin aprobación
- borrar el sistema o hacer comandos destructivos globales

## Fases siguientes
1. Base segura mínima (adapter + policy + approval en memoria)
2. Integrar policy checks en orquestación de tareas
3. Añadir auditoría persistente de aprobaciones
4. Orquestación por misiones y toolsets mínimos
5. Interfaz command center desacoplada
