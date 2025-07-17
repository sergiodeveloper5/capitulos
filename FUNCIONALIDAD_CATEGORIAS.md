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