"""
MODELO DE SECCIONES DE CAPÍTULOS
===============================

Este archivo define los modelos para gestionar las secciones dentro de los capítulos
y las líneas de productos que contienen.

MODELOS INCLUIDOS:
- CapituloSeccion: Secciones que organizan productos por tipo de servicio
- CapituloSeccionLine: Líneas individuales de productos dentro de cada sección

CARACTERÍSTICAS:
- Organización jerárquica: Capítulo > Sección > Líneas de Producto
- Secuenciación automática para ordenamiento
- Secciones fijas que no se pueden modificar en presupuestos
- Filtrado por categorías de productos
- Cálculo automático de subtotales
- Productos opcionales marcables

TIPOS DE SECCIÓN SOPORTADOS:
- Alquiler: Equipos y materiales en alquiler
- Montaje: Servicios de instalación
- Desmontaje: Servicios de retirada
- Portes: Transporte y logística
- Otros: Servicios adicionales

@author: Sistema de Capítulos Técnicos
@version: 1.0
@since: 2024
"""

from odoo import models, fields, api

class CapituloSeccion(models.Model):
    """
    SECCIONES DE CAPÍTULO
    ====================
    
    Organizan los productos dentro de un capítulo por tipo de servicio.
    Permiten estructurar presupuestos de forma lógica y facilitan
    la gestión de diferentes tipos de productos y servicios.
    """
    _name = 'capitulo.seccion'
    _description = 'Sección de Capítulo'
    _order = 'sequence, name'

    # ==========================================
    # CAMPOS BÁSICOS
    # ==========================================

    name = fields.Char(
        string='Nombre de la Sección', 
        required=True,
        help='Nombre descriptivo de la sección (ej: "Alquiler de Grúas", "Montaje de Estructura")'
    )
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición de la sección dentro del capítulo'
    )
    
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción detallada del contenido y alcance de la sección'
    )

    # ==========================================
    # RELACIONES
    # ==========================================
    
    capitulo_id = fields.Many2one(
        'capitulo.contrato', 
        string='Capítulo', 
        ondelete='cascade',
        help='Capítulo al que pertenece esta sección'
    )
    
    product_line_ids = fields.One2many(
        'capitulo.seccion.line', 
        'seccion_id', 
        string='Líneas de Producto',
        help='Productos incluidos en esta sección'
    )

    # ==========================================
    # CONFIGURACIÓN
    # ==========================================
    
    es_fija = fields.Boolean(
        string='Sección Fija', 
        default=False, 
        help="Si está marcado, esta sección no se puede modificar en el presupuesto"
    )
    
    # Campo para filtrar productos por categoría
    product_category_id = fields.Many2one(
        'product.category', 
        string='Categoría de Productos',
        help='Selecciona una categoría para filtrar los productos disponibles en esta sección'
    )

class CapituloSeccionLine(models.Model):
    """
    LÍNEAS DE PRODUCTO EN SECCIÓN
    =============================
    
    Representa productos individuales dentro de una sección, con sus
    cantidades, precios y configuraciones específicas.
    """
    _name = 'capitulo.seccion.line'
    _description = 'Línea de Producto en Sección'
    _order = 'sequence, id'

    # ==========================================
    # RELACIONES PRINCIPALES
    # ==========================================

    seccion_id = fields.Many2one(
        'capitulo.seccion', 
        string='Sección', 
        ondelete='cascade', 
        required=True,
        help='Sección a la que pertenece esta línea de producto'
    )
    
    product_id = fields.Many2one(
        'product.product', 
        string='Producto', 
        required=True,
        help='Producto incluido en esta línea'
    )

    # ==========================================
    # DATOS COMERCIALES
    # ==========================================
    
    cantidad = fields.Float(
        string='Cantidad', 
        default=1, 
        required=True,
        help='Cantidad del producto a incluir'
    )
    
    precio_unitario = fields.Float(
        string='Precio Unitario', 
        related='product_id.list_price', 
        readonly=False,
        help='Precio unitario del producto (editable para ajustes específicos)'
    )
    
    subtotal = fields.Float(
        string='Subtotal', 
        compute='_compute_subtotal', 
        store=True,
        help='Importe total de la línea (cantidad × precio unitario)'
    )

    # ==========================================
    # CONFIGURACIÓN Y ORGANIZACIÓN
    # ==========================================
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición del producto dentro de la sección'
    )
    
    descripcion_personalizada = fields.Char(
        string='Descripción Personalizada',
        help='Descripción específica para esta línea, sobrescribe la descripción del producto'
    )
    
    es_opcional = fields.Boolean(
        string='Opcional', 
        default=False,
        help='Marca este producto como opcional en el presupuesto'
    )

    # ==========================================
    # MÉTODOS COMPUTADOS
    # ==========================================
    
    @api.depends('cantidad', 'precio_unitario')
    def _compute_subtotal(self):
        """
        CÁLCULO DE SUBTOTAL
        ==================
        
        Calcula automáticamente el importe total de cada línea
        multiplicando cantidad por precio unitario.
        """
        for line in self:
            line.subtotal = line.cantidad * line.precio_unitario