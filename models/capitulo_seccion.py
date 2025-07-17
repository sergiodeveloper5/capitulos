from odoo import models, fields, api

class CapituloSeccion(models.Model):
    _name = 'capitulo.seccion'
    _description = 'Sección de Capítulo'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre de la Sección', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    
    # Campo de categoría de productos 
    product_category_id = fields.Many2one( 
        'product.category', 
        string='Categoría de Productos', 
        required=True, 
        help='Categoría de productos que se mostrarán en esta sección' 
    ) 
     
    # Campo de productos con dominio dinámico 
    product_ids = fields.Many2many( 
        'product.product', 
        string='Productos', 
        domain="[('sale_ok', '=', True), ('categ_id', 'child_of', product_category_id)]", 
        help='Selecciona los productos que quieres añadir a esta sección' 
    )
    
    capitulo_id = fields.Many2one('capitulo.contrato', string='Capítulo', ondelete='cascade')
    product_line_ids = fields.One2many('capitulo.seccion.line', 'seccion_id', string='Líneas de Producto')
    descripcion = fields.Text(string='Descripción')
    es_fija = fields.Boolean(string='Sección Fija', default=False, help="Si está marcado, esta sección no se puede modificar en el presupuesto")

    # Función onchange que filtra productos cuando cambia la categoría 
    @api.onchange('product_category_id') 
    def _onchange_product_category_id(self): 
        """Limpiar productos seleccionados cuando cambie la categoría""" 
        if self.product_category_id: 
            self.product_ids = [(5, 0, 0)]  # Limpiar productos seleccionados 
            return { 
                'domain': { 
                    'product_ids': [('sale_ok', '=', True), ('categ_id', 'child_of', self.product_category_id.id)] 
                } 
            }

class CapituloSeccionLine(models.Model):
    _name = 'capitulo.seccion.line'
    _description = 'Línea de Producto en Sección'
    _order = 'sequence, id'

    seccion_id = fields.Many2one('capitulo.seccion', string='Sección', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad', default=1, required=True)
    precio_unitario = fields.Float(string='Precio Unitario', related='product_id.list_price', readonly=False)
    sequence = fields.Integer(string='Secuencia', default=10)
    descripcion_personalizada = fields.Char(string='Descripción Personalizada')
    es_opcional = fields.Boolean(string='Opcional', default=False)
    
    @api.depends('cantidad', 'precio_unitario')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.cantidad * line.precio_unitario
    
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)