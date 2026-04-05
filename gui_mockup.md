# Mockup Interfaz Gráfica ProyectoVulcano

Este diagrama muestra la estructura visual de la interfaz inicial, inspirada en Surpac.

---

```mermaid
graph TD
    A[Menú Archivo] --> B[Menú Ejecutar]
    A --> C[Menú Ayuda]
    D[Toolbars] --> E[Navigator]
    D --> F[Status Bar]
    D --> G[Message Window]
    D --> H[Viewport]
    D --> I[Command Chooser]
    D --> J[Layer Chooser]
    H --> K[Panel de opciones]
    H --> L[Panel de módulos]
    H --> M[Visualización 3D/2D]
    H --> N[Exportación]
```
---

## Descripción de áreas

- **Menú Archivo:** Abrir, guardar, salir
- **Menú Ejecutar:** Correr vista/modelo
- **Menú Ayuda:** Información y soporte
- **Toolbars:** Accesos rápidos (zoom, undo, exportar)
- **Navigator:** Explorador de archivos y carpetas
- **Status Bar:** Estado, coordenadas, conexión
- **Message Window:** Mensajes, errores, log
- **Viewport:** Visualización principal (3D/2D)
- **Command Chooser:** Ejecución de scripts/comandos
- **Layer Chooser:** Gestión de capas activas
- **Panel de opciones:** Parámetros, filtros, sliders
- **Panel de módulos:** Activación/desactivación de módulos
- **Visualización 3D/2D:** Drillholes, bloques, secciones
- **Exportación:** Botones para exportar datos

---

Este mockup sirve como referencia visual y estructural para el desarrollo de la GUI de ProyectoVulcano.