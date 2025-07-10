# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class CapituloWizardSeccion(models.TransientModel):
    _name = 'capitulo.wizard.seccion'
    _description = 'Sección del Wizard de Capítulos'
    _order = 'sequence, id'
    
    wizard_id = fields.Many2one('capitulo.wizard', 'Wizard', required=True, ondelete='cascade')
    sequence = fields.Integer('Secuencia', default=10)
    name = fields.Char('Nombre de la Sección', required=True)
    es_fija = fields.Boolean('Es Fija', default=False)
    producto_ids = fields.One2many('capitulo.wizard.producto', 'seccion_id', 'Productos')
    
class CapituloWizardProducto(models.TransientModel):
    _name = 'capitulo.wizard.producto'
    _description = 'Producto del Wizard de Capítulos'
    _order = 'sequence, id'
    
    seccion_id = fields.Many2one('capitulo.wizard.seccion', 'Sección', required=True, ondelete='cascade')
    sequence = fields.Integer('Secuencia', default=10)
    product_id = fields.Many2one('product.product', 'Producto', required=True)
    quantity = fields.Float('Cantidad', default=1.0)
    product_uom_id = fields.Many2one('uom.uom', 'Unidad de Medida', related='product_id.uom_id', readonly=True)
    price_unit = fields.Float('Precio Unitario', related='product_id.list_price', readonly=True)
    es_fijo = fields.Boolean('Es Fijo', default=False)
    
class CapituloWizard(models.TransientModel):
    _name = 'capitulo.wizard'
    _description = 'Wizard para Gestión de Capítulos'

    # Campos básicos
    sale_order_id = fields.Many2one('sale.order', 'Presupuesto')
    action_type = fields.Selection([
        ('create', 'Crear Nuevo Capítulo'),
        ('template', 'Usar Plantilla'),
    ], string='Acción', required=True, default='create')
    
    # Para crear nuevo capítulo
    name = fields.Char('Nombre del Capítulo')
    description = fields.Text('Descripción')
    condiciones_particulares = fields.Html('Condiciones Particulares')
    
    # Para usar plantilla
    plantilla_id = fields.Many2one('capitulo.plantilla', 'Plantilla')
    
    # Secciones y productos
    seccion_ids = fields.One2many('capitulo.wizard.seccion', 'wizard_id', 'Secciones')
    
    # Opciones adicionales
    save_as_template = fields.Boolean('Guardar como Plantilla', default=False)
    template_name = fields.Char('Nombre de la Plantilla')
    
    # Control de vista
    show_create_fields = fields.Boolean(compute='_compute_show_fields')
    show_template_fields = fields.Boolean(compute='_compute_show_fields')
    show_template_name = fields.Boolean(compute='_compute_show_template_name')
    
    @api.depends('action_type')
    def _compute_show_fields(self):
        """Controlar qué campos mostrar según el tipo de acción"""
        for record in self:
            record.show_create_fields = record.action_type == 'create'
            record.show_template_fields = record.action_type == 'template'
    
    @api.depends('save_as_template')
    def _compute_show_template_name(self):
        """Mostrar campo de nombre de plantilla solo si se va a guardar como plantilla"""
        for record in self:
            record.show_template_name = record.save_as_template
    
    def action_confirm(self):
        """Confirmar acción del wizard"""
        if not self.sale_order_id:
            raise UserError('No se pudo encontrar el presupuesto asociado.')
            
        if self.action_type == 'create':
            capitulo = self._create_capitulo()
            if self.save_as_template:
                self._save_as_template(capitulo)
            return self._generate_lines_from_capitulo(capitulo)
        elif self.action_type == 'template':
            return self._use_template()
        else:
            raise UserError('Debe seleccionar una acción válida.')
    
    def _create_capitulo(self):
        """Crear nuevo capítulo con secciones y productos"""
        if not self.name:
            raise UserError('El nombre del capítulo es obligatorio')
        
        # Crear el capítulo
        capitulo_vals = {
            'name': self.name,
            'description': self.description,
            'condiciones_particulares': self.condiciones_particulares,
            'sale_order_id': self.sale_order_id.id,
        }
        capitulo = self.env['capitulo.capitulo'].create(capitulo_vals)
        
        # Crear secciones y productos del wizard
        for seccion_wizard in self.seccion_ids:
            seccion = self.env['capitulo.seccion'].create({
                'name': seccion_wizard.name,
                'capitulo_id': capitulo.id,
                'sequence': seccion_wizard.sequence,
                'es_fija': seccion_wizard.es_fija,
            })
            
            for producto_wizard in seccion_wizard.producto_ids:
                self.env['capitulo.producto'].create({
                    'product_id': producto_wizard.product_id.id,
                    'seccion_id': seccion.id,
                    'quantity': producto_wizard.quantity,
                    'sequence': producto_wizard.sequence,
                    'es_fijo': producto_wizard.es_fijo,
                })
        
        # Si no hay secciones del wizard, crear secciones por defecto
        if not self.seccion_ids:
            self.env['capitulo.seccion'].create_default_sections(capitulo.id)
        
        return capitulo
    
    def _use_template(self):
        """Usar plantilla para crear capítulo"""
        if not self.plantilla_id:
            raise UserError('Debe seleccionar una plantilla')
        
        # Crear capítulo desde plantilla
        capitulo = self.env['capitulo.capitulo'].create_from_template(
            self.plantilla_id.id, 
            self.sale_order_id.id
        )
        
        # Generar líneas de pedido y mostrar resultado
        return self._generate_lines_from_capitulo(capitulo)
    
    def _save_as_template(self, capitulo):
        """Guardar capítulo como plantilla"""
        if not self.template_name:
            template_name = f"Plantilla - {capitulo.name}"
        else:
            template_name = self.template_name
            
        plantilla = self.env['capitulo.plantilla'].create({
            'name': template_name,
            'description': capitulo.description,
            'condiciones_particulares': capitulo.condiciones_particulares,
        })
        
        # Copiar secciones y productos a la plantilla
        for seccion in capitulo.seccion_ids:
            seccion_plantilla = self.env['capitulo.seccion.plantilla'].create({
                'name': seccion.name,
                'plantilla_id': plantilla.id,
                'sequence': seccion.sequence,
                'es_fija': seccion.es_fija,
            })
            
            for producto in seccion.producto_ids:
                self.env['capitulo.producto.plantilla'].create({
                    'product_id': producto.product_id.id,
                    'seccion_plantilla_id': seccion_plantilla.id,
                    'quantity': producto.quantity,
                    'sequence': producto.sequence,
                    'es_fijo': producto.es_fijo,
                })
        
        return plantilla
    
    def _generate_lines_from_capitulo(self, capitulo):
        """Generar líneas de pedido desde el capítulo y mostrar el resultado"""
        # Generar las líneas
        capitulo.generate_sale_order_lines()
        
        # Retornar a la vista del pedido de venta con las líneas generadas
        return {
            'type': 'ir.actions.act_window',
            'name': f'Pedido de Venta - {self.sale_order_id.name}',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    @api.model
    def default_get(self, fields_list):
        """Valores por defecto"""
        res = super().default_get(fields_list)
        
        # Obtener sale_order_id del contexto activo
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        
        if active_model == 'sale.order' and active_id:
            res['sale_order_id'] = active_id
        elif self.env.context.get('default_sale_order_id'):
            res['sale_order_id'] = self.env.context['default_sale_order_id']
        
        # Si viene del contexto el action_type
        if self.env.context.get('default_action_type'):
            res['action_type'] = self.env.context['default_action_type']
        
        return res