# Funcionalidad de Filtrado por Categorías de Productos

## ✅ Implementado

### Nuevos Campos Añadidos:
1. **`product_category_id`** en `capitulo.seccion` - Para filtrar productos al crear capítulos
2. **`product_category_id`** en `capitulo.wizard.seccion` - Para filtrar productos en el wizard

### Funcionalidad:
- **Al crear capítulos**: Selecciona una categoría de productos en cada sección y solo aparecerán productos de esa categoría
- **Al modificar capítulos**: En el wizard, selecciona una categoría y solo aparecerán productos de esa categoría
- **Filtrado dinámico**: Usa `child_of` para incluir subcategorías automáticamente
- **Sin categoría**: Si no se selecciona categoría, aparecen todos los productos vendibles

### Ubicaciones del Filtrado:
1. **Formulario de Capítulos** → Secciones → Campo "Categoría de Productos"
2. **Wizard de Capítulos** → Secciones → Campo "Categoría de Productos"
3. **Modal "Seleccionar Producto"** → Filtrado automático por categoría de la sección

## Cómo Funciona

### 1. Configuración de Categorías en Secciones
- Cada sección de capítulo puede tener una **Categoría de Productos** asignada
- Esta categoría se configura en el campo `product_category_id` del modelo `capitulo.seccion`
- Se puede establecer tanto en el formulario de capítulos como en el wizard

### 2. Filtrado Automático en Modal de Selección
Cuando se hace clic en **"Añadir Producto"** en una sección:

1. **Detección de Categoría**: El sistema busca automáticamente si la sección tiene una categoría de productos configurada
2. **Filtrado Inteligente**: Si existe una categoría, el modal de selección filtra automáticamente los productos para mostrar solo los de esa categoría
3. **Indicador Visual**: El modal muestra un mensaje informativo indicando que se está filtrando por una categoría específica
4. **Búsqueda Contextual**: La búsqueda de productos se realiza únicamente dentro de la categoría seleccionada

### 3. Flujo Técnico

#### Backend (Python)
- **Modelo**: `capitulo.seccion` tiene el campo `product_category_id`
- **Método**: `_compute_capitulos_agrupados()` incluye la información de categoría en los datos JSON
- **Estructura de datos**: Cada sección incluye `category_id` y `category_name`

#### Frontend (JavaScript)
- **Detección**: `addProductToSection()` obtiene la categoría de la sección desde los datos
- **Modal**: `ProductSelectorDialog` recibe `categoryId` y `categoryName` como props
- **Filtrado**: La búsqueda RPC incluye el filtro `['categ_id', '=', categoryId]` cuando hay categoría

### 4. Experiencia de Usuario

#### Sin Categoría Configurada
- El modal muestra todos los productos disponibles
- Búsqueda libre sin restricciones

#### Con Categoría Configurada
- **Mensaje informativo**: "Filtrado por categoría: [Nombre de la Categoría]"
- **Productos limitados**: Solo se muestran productos de esa categoría
- **Búsqueda contextual**: La búsqueda se realiza únicamente dentro de la categoría
- **Mensaje de no resultados**: Indica que no se encontraron productos en esa categoría específica

### 5. Ventajas del Sistema

1. **Automatización**: No requiere selección manual de categoría por parte del usuario
2. **Consistencia**: Garantiza que solo se añadan productos apropiados a cada sección
3. **Eficiencia**: Reduce el tiempo de búsqueda al mostrar solo productos relevantes
4. **Flexibilidad**: Las secciones sin categoría mantienen acceso completo al catálogo
5. **Transparencia**: El usuario siempre sabe qué filtro se está aplicando

### 6. Casos de Uso

- **Sección "Alquiler"**: Configurada con categoría "Equipos de Alquiler"
- **Sección "Materiales"**: Configurada con categoría "Materiales de Construcción"
- **Sección "Mano de Obra"**: Sin categoría (acceso a todos los servicios)
- **Sección "Transporte"**: Configurada con categoría "Servicios de Transporte"

## Implementación Técnica

### Archivos Modificados:
1. `models/sale_order.py` - Método `_compute_capitulos_agrupados()`
2. `static/src/js/capitulos_accordion_widget.js` - Método `addProductToSection()`
3. `static/src/js/capitulos_accordion_widget.js` - Clase `ProductSelectorDialog`

### Estructura de Datos JSON:
```json
{
  "Capítulo Ejemplo": {
    "sections": {
      "Sección Alquiler": {
        "lines": [...],
        "condiciones_particulares": "",
        "category_id": 123,
        "category_name": "Equipos de Alquiler"
      }
    }
  }
}
```

Esta implementación proporciona un filtrado inteligente y automático que mejora significativamente la experiencia del usuario al añadir productos a las secciones de capítulos.

### Dominio Aplicado:
```xml
domain="[('sale_ok', '=', True)] if not parent.product_category_id else [('sale_ok', '=', True), ('categ_id', 'child_of', parent.product_category_id)]"
```

## Cómo Usar:
1. Ve a un capítulo o abre el wizard
2. En cualquier sección, selecciona una "Categoría de Productos"
3. Al añadir productos a esa sección, solo aparecerán los de la categoría seleccionada
4. Si no seleccionas categoría, aparecen todos los productos vendibles

## ✅ Funcionalidad Preservada:
- Todas las funcionalidades existentes se mantienen intactas
- Los capítulos existentes siguen funcionando normalmente
- El wizard mantiene toda su funcionalidad original
- Las plantillas se copian correctamente incluyendo las categorías