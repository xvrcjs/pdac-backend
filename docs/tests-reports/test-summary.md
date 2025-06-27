# Resumen de Informes de Tests

**Fecha:** 13/06/2025

A continuación se describen de forma resumida los casos de prueba ejecutados para cada aplicación. Las pruebas se corrieron por separado y se enfocaron únicamente en los escenarios principales de cada módulo.

## Administration
- Se validaron operaciones CRUD de clientes, tiempos del sistema de semáforo, OMIC y protocolos.
- Se comprobó la correcta resolución de URLs y el comportamiento de la vista principal.
- [Resultados detallados](administration/report.md)

## Claims
- Se evaluó la creación y manejo básico de reclamos.
- Se verificó que la URL de reclamos permita el acceso esperado y que la vista responda adecuadamente.
- [Resultados detallados](claims/report.md)

## Common
- Se revisó la validación de formularios personalizados, en especial el campo de selección múltiple.
- [Resultados detallados](common/report.md)

## Reports
- Se aseguró que los modelos de informes respondan correctamente sin datos adicionales.
- Se testeó el enlace de URLs y el funcionamiento de la vista asociada.
- [Resultados detallados](reports/report.md)

## Security
- Se probaron las operaciones sobre módulos y roles.
- Se revisó la resolución de URLs y el acceso a la vista principal.
- [Resultados detallados](security/report.md)

## Tickets
- Se cubrieron las operaciones básicas de tickets.
- Se comprobó que las URLs y la vista principal funcionen correctamente.
- [Resultados detallados](tickets/report.md)

## Users
- Se validó el ciclo de vida de cuentas de usuario y el acceso de inicio de sesión.
- [Resultados detallados](users/report.md)

## Gdeba
- Se verificó que la URL de generación de GEDO resuelva correctamente.
- Se evaluó la respuesta de la vista ante un reclamo inexistente.
- [Resultados detallados](gdeba/report.md)

---

Cada informe enlazado detalla el estado PASADO o FALLIDO de las pruebas y la duración estimada de cada caso.
