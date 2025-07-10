# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderChapterSectionTemplate(models.Model):
    _name = 'sale.order.chapter.section.template'
    _description = 'Plantilla de Sección de Capítulo'
    _order = 'chapter_template_id, sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre de la Sección',
        required=True,
        help='Nombre de la sección (ej: "Alquiler", "Montaje", "Portes")'
    )
    
    chapter_template_id = fields.Many2one(
        comodel_name='sale.order.chapter.template',
        string='Plantilla de Capítulo',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden dentro del capítulo'
    )
    
    section_type = fields.Selection([
        ('rental', 'Alquiler'),
        ('assembly', 'Montaje'),
        ('transport', 'Portes'),
        ('other', 'Otros Conceptos'),
        ('conditions', 'Condiciones Generales')
    ], string='Tipo de Sección', required=True, default='other')
    
    product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='chapter_section_template_product_rel',
        column1='section_template_id',
        column2='product_id',
        string='Productos Predefinidos',
        help='Productos que se añadirán automáticamente a esta sección'
    )
    
    is_readonly_commercial = fields.Boolean(
        string='Solo Lectura para Comercial',
        compute='_compute_readonly_commercial',
        store=True,
        help='Si está marcado, los comerciales no pueden editar esta sección'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción adicional de la sección'
    )
    
    company_id = fields.Many2one(
        related='chapter_template_id.company_id',
        string='Compañía',
        store=True
    )
    
    # Campos computados
    product_count = fields.Integer(
        string='Número de Productos',
        compute='_compute_product_count',
        store=True
    )
    
    @api.depends('section_type')
    def _compute_readonly_commercial(self):
        """Calcula si la sección es de solo lectura para comerciales"""
        for record in self:
            if record.section_type in ['rental', 'assembly', 'conditions']:
                record.is_readonly_commercial = True
            else:
                record.is_readonly_commercial = False
    
    @api.depends('product_ids')
    def _compute_product_count(self):
        """Calcula el número de productos predefinidos"""
        for record in self:
            record.product_count = len(record.product_ids)
    
    @api.constrains('name', 'chapter_template_id')
    def _check_name_unique_per_chapter(self):
        """Valida que el nombre de la sección sea único por capítulo"""
        for record in self:
            if self.search_count([
                ('name', '=', record.name),
                ('chapter_template_id', '=', record.chapter_template_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(
                    _("Ya existe una sección con el nombre '%s' en este capítulo.") % record.name
                )
    
    @api.constrains('section_type', 'chapter_template_id')
    def _check_conditions_section_unique(self):
        """Valida que solo haya una sección de condiciones por capítulo"""
        for record in self:
            if record.section_type == 'conditions':
                if self.search_count([
                    ('section_type', '=', 'conditions'),
                    ('chapter_template_id', '=', record.chapter_template_id.id),
                    ('id', '!=', record.id)
                ]) > 0:
                    raise ValidationError(
                        _("Solo puede haber una sección de 'Condiciones Generales' por capítulo.")
                    )
    
    @api.model
    def create(self, vals):
        """Sobrescribe create para ajustar la secuencia de condiciones"""
        if vals.get('section_type') == 'conditions':
            vals['sequence'] = 999  # Siempre al final
        return super().create(vals)
    
    def write(self, vals):
        """Sobrescribe write para ajustar la secuencia de condiciones"""
        if vals.get('section_type') == 'conditions':
            vals['sequence'] = 999  # Siempre al final
        return super().write(vals)
    
    def action_view_products(self):
        """Acción para ver los productos predefinidos"""
        self.ensure_one()
        return {
            'name': _('Productos de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.product_ids.ids)],
            'target': 'current',
        }
    
    def create_section_from_template(self, chapter_id):
        """Crea una sección en el capítulo basada en esta plantilla"""
        self.ensure_one()
        
        # Crear la sección
        section_vals = {
            'chapter_id': chapter_id,
            'template_section_id': self.id,
            'name': self.name,
            'sequence': self.sequence,
            'section_type': self.section_type,
            'is_readonly_commercial': self.is_readonly_commercial,
        }
        
        section = self.env['sale.order.chapter.section'].create(section_vals)
        
        # Crear líneas de productos predefinidos
        sale_order = self.env['sale.order.chapter'].browse(chapter_id).sale_order_id
        
        for product in self.product_ids:
            line_vals = {
                'order_id': sale_order.id,
                'product_id': product.id,
                'chapter_id': chapter_id,
                'section_id': section.id,
                'product_uom_qty': 1.0,
                'price_unit': product.list_price,
            }
            self.env['sale.order.line'].create(line_vals)
        
        return section