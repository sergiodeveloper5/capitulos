# -*- coding: utf-8 -*-
"""
Módulo de Secciones de Capítulos Técnicos
==========================================

Este módulo define los modelos para las secciones de capítulos y sus líneas de productos.
Las secciones organizan los productos dentro de un capítulo, permitiendo una estructura
jerárquica y ordenada para la gestión de presupuestos técnicos.

Autor: Sergio
Fecha: 2024
Versión: 1.0
"""

from odoo import models, fields, api


class CapituloSeccion(models.Model):
    """
    Modelo para las secciones dentro de un capítulo técnico.
    
    Una sección agrupa productos relacionados dentro de un capítulo, permitiendo
    organizar el presupuesto de manera estructurada. Cada sección puede tener
    múltiples líneas de productos y puede configurarse para filtrar productos
    por categoría específica.
    
    Características principales:
    - Organización jerárquica: Capítulo > Sección > Líneas de Producto
    - Secuenciación personalizable para ordenamiento
    - Filtrado automático por categoría de productos
    - Secciones fijas que no se pueden modificar en presupuestos
    - Descripción detallada para cada sección
    """
    _name = 'capitulo.seccion'
    _description = 'Sección de Capítulo'
    _order = 'sequence, name'  # Ordenar por secuencia y luego por nombre

    # ========================================
    # CAMPOS BÁSICOS DE IDENTIFICACIÓN
    # ========================================
    
    name = fields.Char(
        string='Nombre de la Sección', 
        required=True,
        help='Nombre descriptivo de la sección (ej: "Materiales Eléctricos", "Mano de Obra")'
    )
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición de la sección dentro del capítulo. Menor número = mayor prioridad'
    )
    
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción detallada del contenido y propósito de esta sección'
    )
    
    # ========================================
    # CAMPOS DE RELACIÓN Y JERARQUÍA
    # ========================================
    
    capitulo_id = fields.Many2one(
        'capitulo.contrato', 
        string='Capítulo', 
        ondelete='cascade',
        help='Capítulo al que pertenece esta sección. Se elimina automáticamente si se elimina el capítulo'
    )
    
    product_line_ids = fields.One2many(
        'capitulo.seccion.line', 
        'seccion_id', 
        string='Líneas de Producto',
        help='Lista de productos incluidos en esta sección con sus cantidades y precios'
    )
    
    # ========================================
    # CAMPOS DE CONFIGURACIÓN Y FILTRADO
    # ========================================
    
    es_fija = fields.Boolean(
        string='Sección Fija', 
        default=False, 
        help='Si está marcado, esta sección no se puede modificar en el presupuesto. '
             'Útil para secciones estándar que siempre deben incluirse'
    )
    
    product_category_id = fields.Many2one(
        'product.category', 
        string='Categoría de Productos',
        help='Selecciona una categoría para filtrar automáticamente los productos disponibles. '
             'Solo se mostrarán productos de esta categoría al añadir productos a la sección'
    )


class CapituloSeccionLine(models.Model):
    """
    Modelo para las líneas de productos dentro de una sección de capítulo.
    
    Cada línea representa un producto específico con su cantidad, precio y configuración
    dentro de una sección. Permite personalizar la descripción y marcar productos como
    opcionales para mayor flexibilidad en los presupuestos.
    
    Características principales:
    - Relación directa con productos del catálogo
    - Cálculo automático de subtotales
    - Productos opcionales para presupuestos flexibles
    - Secuenciación personalizable
    - Descripción personalizada por línea
    - Precios editables independientes del catálogo
    """
    _name = 'capitulo.seccion.line'
    _description = 'Línea de Producto en Sección'
    _order = 'sequence, id'  # Ordenar por secuencia y luego por ID

    # ========================================
    # CAMPOS DE RELACIÓN PRINCIPAL
    # ========================================
    
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
        help='Producto del catálogo que se incluye en esta línea'
    )
    
    # ========================================
    # CAMPOS DE CANTIDAD Y PRECIO
    # ========================================
    
    cantidad = fields.Float(
        string='Cantidad', 
        default=1, 
        required=True,
        help='Cantidad del producto a incluir en el presupuesto'
    )
    
    precio_unitario = fields.Float(
        string='Precio Unitario', 
        related='product_id.list_price', 
        readonly=False,
        help='Precio por unidad del producto. Se toma del catálogo pero puede modificarse'
    )
    
    subtotal = fields.Float(
        string='Subtotal', 
        compute='_compute_subtotal', 
        store=True,
        help='Importe total de la línea (cantidad × precio unitario)'
    )
    
    # ========================================
    # CAMPOS DE CONFIGURACIÓN Y PERSONALIZACIÓN
    # ========================================
    
    sequence = fields.Integer(
        string='Secuencia', 
        default=10,
        help='Orden de aparición de la línea dentro de la sección'
    )
    
    descripcion_personalizada = fields.Char(
        string='Descripción Personalizada',
        help='Descripción específica para esta línea, diferente a la descripción del producto'
    )
    
    es_opcional = fields.Boolean(
        string='Opcional', 
        default=False,
        help='Si está marcado, este producto es opcional y puede incluirse o no en el presupuesto final'
    )
    
    # ========================================
    # MÉTODOS COMPUTADOS
    # ========================================
    
    @api.depends('cantidad', 'precio_unitario')
    def _compute_subtotal(self):
        """
        Calcula el subtotal de cada línea de producto.
        
        Este método se ejecuta automáticamente cuando cambian la cantidad o el precio unitario,
        recalculando el subtotal como el producto de ambos valores.
        
        Decorador @api.depends:
        - 'cantidad': Se recalcula cuando cambia la cantidad
        - 'precio_unitario': Se recalcula cuando cambia el precio
        
        El campo 'subtotal' está marcado como store=True para persistir el valor
        en la base de datos y mejorar el rendimiento en consultas.
        """
        for line in self:
            line.subtotal = line.cantidad * line.precio_unitario