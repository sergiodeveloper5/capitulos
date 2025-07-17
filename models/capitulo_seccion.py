# -*- coding: utf-8 -*-
"""
MODELO DE SECCIONES: CAPÍTULO SECCIÓN
====================================

Este archivo define los modelos para las secciones dentro de los capítulos
y las líneas de productos que componen cada sección.

MODELOS INCLUIDOS:
1. CapituloSeccion: Secciones dentro de capítulos
2. CapituloSeccionLine: Líneas de productos dentro de secciones

ARQUITECTURA DE DATOS:
- Capítulo (1) → Secciones (N) → Líneas de Producto (N)
- Cada sección puede tener múltiples productos
- Cada línea de producto tiene cantidad, precio y configuración

FUNCIONALIDADES:
- Organización jerárquica de productos
- Cálculo automático de subtotales
- Secuenciación personalizable
- Productos opcionales y descripciones personalizadas
- Secciones fijas (no modificables en presupuestos)

REFERENCIAS PRINCIPALES:
- models/capitulo.py: Modelo padre de capítulos
- models/sale_order.py: Integración con presupuestos
- product.product: Productos estándar de Odoo
- static/src/js/capitulos_accordion_widget.js: Widget frontend
"""

# IMPORTACIONES ESTÁNDAR DE ODOO
from odoo import models, fields, api

class CapituloSeccion(models.Model):
    """
    MODELO: Sección de Capítulo
    
    Define las secciones que organizan productos dentro de un capítulo.
    Cada sección puede contener múltiples líneas de productos y tiene
    configuraciones específicas como secuencia y si es fija.
    
    HERENCIA: models.Model (modelo base de Odoo)
    TABLA: capitulo_seccion
    ORDEN: sequence, name (ordenación por secuencia y nombre)
    """
    
    # CONFIGURACIÓN DEL MODELO
    _name = 'capitulo.seccion'
    _description = 'Sección de Capítulo'
    _order = 'sequence, name'  # Ordenación por secuencia y nombre

    # ==========================================
    # CAMPOS PRINCIPALES
    # ==========================================
    
    name = fields.Char(
        string='Nombre de la Sección', 
        required=True,
        help='Nombre identificativo de la sección'
    )
    
    # CAMPO DE SECUENCIA: Para ordenar secciones dentro del capítulo
    # USADO EN: Vista de acordeón y ordenación automática
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición de la sección en el capítulo'
    )
    
    # RELACIÓN MANY2ONE: Cada sección pertenece a un capítulo
    # REFERENCIA: models/capitulo.py → CapituloContrato
    # ONDELETE CASCADE: Si se elimina el capítulo, se eliminan las secciones
    capitulo_id = fields.Many2one(
        'capitulo.contrato', 
        string='Capítulo', 
        ondelete='cascade',
        help='Capítulo al que pertenece esta sección'
    )
    
    # RELACIÓN ONE2MANY: Una sección tiene múltiples líneas de producto
    # REFERENCIA: CapituloSeccionLine (definido abajo)
    product_line_ids = fields.One2many(
        'capitulo.seccion.line', 
        'seccion_id', 
        string='Líneas de Producto',
        help='Productos incluidos en esta sección'
    )
    
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción detallada de la sección'
    )
    
    # CAMPO BOOLEANO: Indica si la sección es fija (no modificable)
    # USADO EN: Validaciones en presupuestos y widget JavaScript
    es_fija = fields.Boolean(
        string='Sección Fija', 
        default=False, 
        help="Si está marcado, esta sección no se puede modificar en el presupuesto"
    )

class CapituloSeccionLine(models.Model):
    """
    MODELO: Línea de Producto en Sección
    
    Define las líneas individuales de productos dentro de una sección.
    Cada línea representa un producto específico con cantidad, precio
    y configuraciones adicionales.
    
    HERENCIA: models.Model (modelo base de Odoo)
    TABLA: capitulo_seccion_line
    ORDEN: sequence, id (ordenación por secuencia y ID)
    """
    
    # CONFIGURACIÓN DEL MODELO
    _name = 'capitulo.seccion.line'
    _description = 'Línea de Producto en Sección'
    _order = 'sequence, id'  # Ordenación por secuencia e ID

    # ==========================================
    # CAMPOS DE RELACIÓN
    # ==========================================
    
    # RELACIÓN MANY2ONE: Cada línea pertenece a una sección
    # REFERENCIA: CapituloSeccion (definido arriba)
    # ONDELETE CASCADE: Si se elimina la sección, se eliminan las líneas
    seccion_id = fields.Many2one(
        'capitulo.seccion', 
        string='Sección', 
        ondelete='cascade', 
        required=True,
        help='Sección a la que pertenece esta línea de producto'
    )
    
    # RELACIÓN MANY2ONE: Referencia al producto estándar de Odoo
    # REFERENCIA: product.product (modelo estándar de Odoo)
    product_id = fields.Many2one(
        'product.product', 
        string='Producto', 
        required=True,
        help='Producto incluido en esta línea'
    )
    
    # ==========================================
    # CAMPOS DE CANTIDAD Y PRECIO
    # ==========================================
    
    cantidad = fields.Float(
        string='Cantidad', 
        default=1, 
        required=True,
        help='Cantidad del producto en esta línea'
    )
    
    # CAMPO RELACIONADO: Precio del producto con posibilidad de override
    # RELATED: Toma el precio de product_id.list_price
    # READONLY=False: Permite modificar el precio por línea
    precio_unitario = fields.Float(
        string='Precio Unitario', 
        related='product_id.list_price', 
        readonly=False,
        help='Precio unitario del producto (modificable)'
    )
    
    # ==========================================
    # CAMPOS DE CONFIGURACIÓN
    # ==========================================
    
    # CAMPO DE SECUENCIA: Para ordenar productos dentro de la sección
    # USADO EN: Vista de acordeón y ordenación automática
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición del producto en la sección'
    )
    
    descripcion_personalizada = fields.Char(
        string='Descripción Personalizada',
        help='Descripción específica para esta línea (opcional)'
    )
    
    # CAMPO BOOLEANO: Indica si el producto es opcional
    # USADO EN: Cálculos y visualización en presupuestos
    es_opcional = fields.Boolean(
        string='Opcional', 
        default=False,
        help='Indica si este producto es opcional en el presupuesto'
    )
    
    # ==========================================
    # CAMPOS COMPUTADOS
    # ==========================================
    
    # CAMPO COMPUTADO: Calcula el subtotal de la línea
    # MÉTODO: _compute_subtotal()
    # DEPENDENCIAS: cantidad, precio_unitario
    # STORE=True: Se almacena en base de datos para rendimiento
    subtotal = fields.Float(
        string='Subtotal', 
        compute='_compute_subtotal', 
        store=True,
        help='Subtotal calculado (cantidad × precio unitario)'
    )
    
    # ==========================================
    # MÉTODOS COMPUTADOS
    # ==========================================
    
    @api.depends('cantidad', 'precio_unitario')
    def _compute_subtotal(self):
        """
        MÉTODO COMPUTADO: Calcula subtotal de línea
        
        Calcula el subtotal multiplicando cantidad por precio unitario.
        Se ejecuta automáticamente cuando cambian los campos dependientes.
        
        DEPENDENCIAS:
        - cantidad: Cantidad del producto
        - precio_unitario: Precio unitario del producto
        
        FÓRMULA:
        subtotal = cantidad × precio_unitario
        
        CARACTERÍSTICAS:
        - Store=True: Se guarda en base de datos
        - Actualización automática en cambios
        - Usado en cálculos de totales de capítulos
        
        REFERENCIAS:
        - Usado en: models/sale_order.py para totales de capítulos
        - Mostrado en: Widget JavaScript del acordeón
        """
        for line in self:
            # CÁLCULO: Cantidad × Precio Unitario
            line.subtotal = line.cantidad * line.precio_unitario