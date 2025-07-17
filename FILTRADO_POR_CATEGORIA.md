# FUNCIONALIDAD DE FILTRADO POR CATEGORÍA DE PRODUCTOS

## Descripción General

Se ha implementado una nueva funcionalidad que permite filtrar productos por categoría al crear o editar secciones en el wizard de capítulos. Esta mejora facilita la selección de productos organizándolos por categorías específicas.

## Características Implementadas

### 1. Campo de Categoría en Secciones
- **Campo**: `product_category_id` en el modelo `CapituloWizardSeccion`
- **Tipo**: Many2one hacia `product.category`
- **Propósito**: Permite seleccionar una categoría de productos para filtrar la lista disponible

### 2. Filtrado Automático
- **Método**: `_onchange_product_category_id()`
- **Comportamiento**: 
  - Se ejecuta automáticamente al cambiar la categoría
  - Limpia los productos previamente seleccionados
  - Actualiza el dominio para mostrar solo productos de la categoría seleccionada
  - Incluye subcategorías usando el operador `child_of`

### 3. Integración en la Vista
- **Ubicación**: Formulario embebido de sección en el wizard
- **Posición**: En el grupo de configuración, junto a "Incluir en Presupuesto" y "Secuencia"
- **Ayuda contextual**: Tooltip explicativo para guiar al usuario

## Flujo de Trabajo

1. **Selección de Categoría**: El usuario selecciona una categoría en el campo "Categoría de Productos"
2. **Filtrado Automático**: El sistema filtra automáticamente los productos disponibles
3. **Limpieza de Selección**: Se limpian los productos previamente seleccionados
4. **Selección de Productos**: El usuario puede ahora seleccionar solo productos de la categoría elegida

## Código Implementado

### Modelo (capitulo_wizard.py)
```python
# Campo de categoría de productos
product_category_id = fields.Many2one(
    'product.category',
    string='Categoría de Productos',
    help='Categoría de productos que se mostrarán en esta sección'
)

# Método onchange para filtrado
@api.onchange('product_category_id')
def _onchange_product_category_id(self):
    """Filtra productos cuando cambia la categoría seleccionada."""
    if self.product_category_id:
        self.product_ids = [(5, 0, 0)]  # Limpiar productos seleccionados
        return {
            'domain': {
                'product_ids': [
                    ('sale_ok', '=', True), 
                    ('categ_id', 'child_of', self.product_category_id.id)
                ]
            }
        }
    else:
        return {
            'domain': {
                'product_ids': [('sale_ok', '=', True)]
            }
        }
```

### Vista (capitulo_wizard_view.xml)
```xml
<!-- Campo de categoría en configuración de sección -->
<field name="product_category_id" string="Categoría de Productos" 
       help="Selecciona una categoría para filtrar los productos disponibles"/>

<!-- Campo de producto con dominio dinámico -->
<field name="product_id" string="Producto" required="1" 
       domain="[('sale_ok', '=', True), '|', ('categ_id', 'child_of', parent.product_category_id), ('categ_id', '=', False)]"
       context="{'default_sale_ok': True}"/>
```

## Beneficios

1. **Organización Mejorada**: Los productos se organizan por categorías lógicas
2. **Búsqueda Más Rápida**: Reduce el tiempo de búsqueda al filtrar productos
3. **Menos Errores**: Evita seleccionar productos incorrectos al limitar las opciones
4. **Experiencia de Usuario**: Interfaz más intuitiva y fácil de usar
5. **Escalabilidad**: Funciona bien con grandes catálogos de productos

## Compatibilidad

- **Versión Odoo**: 18.0
- **Módulos Requeridos**: `product`, `sale_management`
- **Retrocompatibilidad**: Mantiene compatibilidad con secciones existentes sin categoría

## Notas Técnicas

- El filtrado incluye subcategorías usando el operador `child_of`
- Los productos sin categoría también se muestran para mantener flexibilidad
- El campo es opcional, permitiendo usar secciones sin filtrado si se desea
- Se incluye logging para debugging y seguimiento de cambios