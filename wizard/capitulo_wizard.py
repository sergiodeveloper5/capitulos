# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class CapituloWizard(models.TransientModel):
    _name = 'capitulo.wizard'
    _description = 'Wizard para Gestión de Capítulos'

    # Campos básicos
    sale_order_id = fields.Many2one('sale.order', 'Presupuesto', required=True)
    action_type = fields.Selection([
        ('create', 'Crear Nuevo Capítulo'),
        ('template', 'Usar Plantilla'),
    ], string='Acción', required=True, default='create')
    
    # Para crear nuevo capítulo
    name = fields.Char('Nombre del Capítulo')
    description = fields.Text('Descripción')
    
    # Para usar plantilla
    plantilla_id = fields.Many2one('capitulo.plantilla', 'Plantilla')
    
    # Control de vista
    show_create_fields = fields.Boolean(compute='_compute_show_fields')
    show_template_fields = fields.Boolean(compute='_compute_show_fields')
    
    @api.depends('action_type')
    def _compute_show_fields(self):
        for wizard in self:
            wizard.show_create_fields = wizard.action_type == 'create'
            wizard.show_template_fields = wizard.action_type == 'template'
    
    def action_confirm(self):
        """Confirmar acción del wizard"""
        if self.action_type == 'create':
            return self._create_capitulo()
        elif self.action_type == 'template':
            return self._use_template()
    
    def _create_capitulo(self):
        """Crear nuevo capítulo"""
        if not self.name:
            raise UserError('El nombre del capítulo es obligatorio')
        
        # Crear el capítulo
        capitulo_vals = {
            'name': self.name,
            'description': self.description,
            'sale_order_id': self.sale_order_id.id,
        }
        capitulo = self.env['capitulo.capitulo'].create(capitulo_vals)
        
        # Crear secciones por defecto
        self.env['capitulo.seccion'].create_default_sections(capitulo.id)
        
        # Abrir el capítulo para edición (vista admin)
        return {
            'name': f'Capítulo: {capitulo.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.capitulo',
            'res_id': capitulo.id,
            'view_mode': 'form',
            'view_id': self.env.ref('capitulos.view_capitulo_form_admin').id,
            'target': 'current',
        }
    
    def _use_template(self):
        """Usar plantilla para crear capítulo"""
        if not self.plantilla_id:
            raise UserError('Debe seleccionar una plantilla')
        
        # Crear capítulo desde plantilla
        capitulo = self.env['capitulo.capitulo'].create_from_template(
            self.plantilla_id.id, 
            self.sale_order_id.id
        )
        
        # Abrir el capítulo para edición (vista admin)
        return {
            'name': f'Capítulo: {capitulo.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'capitulo.capitulo',
            'res_id': capitulo.id,
            'view_mode': 'form',
            'view_id': self.env.ref('capitulos.view_capitulo_form_admin').id,
            'target': 'current',
        }
    
    @api.model
    def default_get(self, fields_list):
        """Valores por defecto"""
        res = super().default_get(fields_list)
        
        # Si viene del contexto el sale_order_id
        if self.env.context.get('default_sale_order_id'):
            res['sale_order_id'] = self.env.context['default_sale_order_id']
        
        # Si viene del contexto el action_type
        if self.env.context.get('default_action_type'):
            res['action_type'] = self.env.context['default_action_type']
        
        return res