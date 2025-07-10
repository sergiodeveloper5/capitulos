# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderChapter(models.Model):
    _name = 'sale.order.chapter'
    _description = 'Capítulo de Presupuesto'
    _order = 'sale_order_id, sequence, name'
    _rec_name = 'name'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Presupuesto',
        required=True,
        ondelete='cascade'
    )
    
    template_id = fields.Many2one(
        comodel_name='sale.order.chapter.template',
        string='Plantilla de Capítulo',
        help='Plantilla utilizada para crear este capítulo'
    )
    
    name = fields.Char(
        string='Nombre del Capítulo',
        required=True
    )
    
    description = fields.Text(
        string='Descripción'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden en el presupuesto'
    )
    
    section_ids = fields.One2many(
        comodel_name='sale.order.chapter.section',
        inverse_name='chapter_id',
        string='Secciones del Capítulo'
    )
    
    company_id = fields.Many2one(
        related='sale_order_id.company_id',
        string='Compañía',
        store=True
    )
    
    partner_id = fields.Many2one(
        related='sale_order_id.partner_id',
        string='Cliente',
        store=True
    )
    
    # Campos computados
    section_count = fields.Integer(
        string='Número de Secciones',
        compute='_compute_section_count',
        store=True
    )
    
    line_count = fields.Integer(
        string='Número de Líneas',
        compute='_compute_line_count',
        store=True
    )
    
    amount_total = fields.Monetary(
        string='Total del Capítulo',
        compute='_compute_amount_total',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        related='sale_order_id.currency_id',
        string='Moneda',
        store=True
    )
    
    @api.depends('section_ids')
    def _compute_section_count(self):
        """Calcula el número de secciones en el capítulo"""
        for record in self:
            record.section_count = len(record.section_ids)
    
    @api.depends('section_ids.line_ids')
    def _compute_line_count(self):
        """Calcula el número total de líneas en el capítulo"""
        for record in self:
            record.line_count = sum(len(section.line_ids) for section in record.section_ids)
    
    @api.depends('section_ids.line_ids.price_subtotal')
    def _compute_amount_total(self):
        """Calcula el total del capítulo"""
        for record in self:
            total = 0.0
            for section in record.section_ids:
                for line in section.line_ids:
                    total += line.price_subtotal
            record.amount_total = total
    
    @api.constrains('name', 'sale_order_id')
    def _check_name_unique_per_order(self):
        """Valida que el nombre del capítulo sea único por presupuesto"""
        for record in self:
            if self.search_count([
                ('name', '=', record.name),
                ('sale_order_id', '=', record.sale_order_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(
                    _("Ya existe un capítulo con el nombre '%s' en este presupuesto.") % record.name
                )
    
    def action_view_sections(self):
        """Acción para ver las secciones del capítulo"""
        self.ensure_one()
        return {
            'name': _('Secciones de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.chapter.section',
            'view_mode': 'list,form',
            'domain': [('chapter_id', '=', self.id)],
            'context': {
                'default_chapter_id': self.id,
                'search_default_chapter_id': self.id,
            },
            'target': 'current',
        }
    
    def action_view_lines(self):
        """Acción para ver todas las líneas del capítulo"""
        self.ensure_one()
        line_ids = []
        for section in self.section_ids:
            line_ids.extend(section.line_ids.ids)
        
        return {
            'name': _('Líneas de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list,form',
            'domain': [('id', 'in', line_ids)],
            'target': 'current',
        }
    
    def add_conditions_section(self):
        """Añade automáticamente la sección de condiciones generales"""
        self.ensure_one()
        
        # Verificar si ya existe una sección de condiciones
        existing_conditions = self.section_ids.filtered(
            lambda s: s.section_type == 'conditions'
        )
        
        if not existing_conditions:
            # Crear la sección de condiciones generales
            conditions_vals = {
                'chapter_id': self.id,
                'name': 'Condiciones Generales',
                'sequence': 999,
                'section_type': 'conditions',
                'is_readonly_commercial': True,
            }
            
            self.env['sale.order.chapter.section'].create(conditions_vals)
    
    @api.model
    def create(self, vals):
        """Sobrescribe create para añadir condiciones automáticamente"""
        chapter = super().create(vals)
        chapter.add_conditions_section()
        return chapter