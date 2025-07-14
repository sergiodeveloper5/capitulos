# Widget Acordeón para Capítulos

## Descripción
Este módulo incluye un widget personalizado que muestra los capítulos de un presupuesto en formato acordeón cuando hay más de un capítulo, permitiendo colapsar/expandir cada capítulo individualmente.

## Funcionalidades

### 1. Vista Acordeón
- **Activación automática**: Se activa cuando hay más de un capítulo en el presupuesto
- **Colapso individual**: Cada capítulo puede colapsarse/expandirse independientemente
- **Vista tabular**: Cada capítulo muestra sus secciones y productos en formato tabla
- **Totales por capítulo**: Se muestra el total de cada capítulo

### 2. Estructura de Datos
El widget utiliza el campo computado `capitulos_agrupados` que genera un JSON con la siguiente estructura:

```json
{
  "Capítulo 1": {
    "sections": {
      "Alquiler": {
        "lines": [
          {
            "sequence": 1,
            "product_name": "Producto A",
            "name": "Descripción del producto",
            "product_uom_qty": 2.0,
            "product_uom": "Unidades",
            "price_unit": 100.0,
            "price_subtotal": 200.0
          }
        ]
      }
    },
    "total": 200.0
  }
}
```

### 3. Archivos Principales

#### JavaScript Widget
- **Archivo**: `static/src/js/capitulos_accordion_widget.js`
- **Función**: Renderiza el acordeón con Bootstrap
- **Características**:
  - Manejo de estado de colapso
  - Animaciones suaves
  - Iconos dinámicos
  - Tabla responsive

#### Estilos CSS
- **Archivo**: `static/src/css/capitulos_accordion.css`
- **Función**: Estilos personalizados para el acordeón
- **Características**:
  - Diseño responsive
  - Colores diferenciados para secciones y totales
  - Efectos hover
  - Animaciones de transición

#### Vista XML
- **Archivo**: `views/sale_order_views.xml`
- **Función**: Integra el widget en la vista del pedido
- **Lógica**: Muestra acordeón si hay >1 capítulo, sino vista tradicional

#### Modelo Python
- **Archivo**: `models/sale_order.py`
- **Función**: Campo computado `capitulos_agrupados`
- **Proceso**: Agrupa líneas por capítulo y sección

### 4. Comportamiento

#### Condiciones de Activación
- **Un capítulo o menos**: Vista tradicional con `section_and_note_one2many`
- **Más de un capítulo**: Vista acordeón con widget personalizado

#### Interacción del Usuario
- **Click en encabezado**: Colapsa/expande el capítulo
- **Estado persistente**: El estado de colapso se mantiene durante la sesión
- **Iconos dinámicos**: Chevron que cambia según el estado

### 5. Ventajas

#### Escalabilidad
- **Manejo de muchos capítulos**: Soluciona el problema de 40+ capítulos
- **Vista compacta**: Solo se muestran los capítulos expandidos
- **Navegación fácil**: Acceso rápido a cualquier capítulo

#### Usabilidad
- **Interfaz intuitiva**: Comportamiento estándar de acordeón
- **Información organizada**: Estructura clara por capítulos y secciones
- **Totales visibles**: Resumen financiero por capítulo

### 6. Instalación

1. Los archivos ya están incluidos en el módulo
2. El `__manifest__.py` incluye los assets necesarios
3. Al actualizar el módulo, el widget estará disponible automáticamente

### 7. Compatibilidad

- **Odoo 18.0+**
- **Bootstrap 4/5** (para estilos de acordeón)
- **jQuery** (para interacciones)
- **Navegadores modernos** (Chrome, Firefox, Safari, Edge)

### 8. Personalización

Para personalizar el widget:

1. **Estilos**: Modificar `capitulos_accordion.css`
2. **Comportamiento**: Editar `capitulos_accordion_widget.js`
3. **Estructura de datos**: Ajustar `_compute_capitulos_agrupados` en `sale_order.py`

### 9. Solución de Problemas

#### Widget no se muestra
- Verificar que hay más de un capítulo
- Comprobar que los assets están cargados
- Revisar la consola del navegador para errores JavaScript

#### Datos no se cargan
- Verificar el campo `capitulos_agrupados` en el modelo
- Comprobar que las líneas tienen los campos `es_encabezado_capitulo` y `es_encabezado_seccion` correctos

#### Estilos no se aplican
- Verificar que el CSS está incluido en `__manifest__.py`
- Limpiar caché del navegador
- Comprobar que no hay conflictos CSS

Esta implementación proporciona una solución elegante y escalable para manejar presupuestos con múltiples capítulos, mejorando significativamente la experiencia del usuario.