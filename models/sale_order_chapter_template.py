# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderChapterTemplate(models.Model):
    _name = 'sale.order.chapter.template'
    _description = 'Plantilla de Capítulo para Presupuestos'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre del Capítulo',
        required=True,
        help='Nombre del capítulo (ej: "MONTACARGAS MC-1700")'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del capítulo'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de aparición del capítulo'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Desmarcar para desactivar la plantilla'
    )
    
    section_ids = fields.One2many(
        comodel_name='sale.order.chapter.section.template',
        inverse_name='chapter_template_id',
        string='Secciones del Capítulo',
        help='Secciones predefinidas para este capítulo'
    )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )
    
    # Campos computados
    section_count = fields.Integer(
        string='Número de Secciones',
        compute='_compute_section_count',
        store=True
    )
    
    @api.depends('section_ids')
    def _compute_section_count(self):
        """Calcula el número de secciones en la plantilla"""
        for record in self:
            record.section_count = len(record.section_ids)
    
    @api.constrains('name')
    def _check_name_unique(self):
        """Valida que el nombre del capítulo sea único por compañía"""
        for record in self:
            if self.search_count([
                ('name', '=', record.name),
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(
                    _("Ya existe una plantilla de capítulo con el nombre '%s' en esta compañía.") % record.name
                )
    
    def copy(self, default=None):
        """Sobrescribe el método copy para añadir (Copia) al nombre"""
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = _("%s (Copia)") % self.name
        return super().copy(default)
    
    def action_view_sections(self):
        """Acción para ver las secciones de la plantilla"""
        self.ensure_one()
        return {
            'name': _('Secciones de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.chapter.section.template',
            'view_mode': 'list,form',
            'domain': [('chapter_template_id', '=', self.id)],
            'context': {
                'default_chapter_template_id': self.id,
                'search_default_chapter_template_id': self.id,
            },
            'target': 'current',
        }
    
    def create_chapter_from_template(self, sale_order_id):
        """Crea un capítulo en el presupuesto basado en esta plantilla"""
        self.ensure_one()
        
        # Crear el capítulo
        chapter_vals = {
            'sale_order_id': sale_order_id,
            'template_id': self.id,
            'name': self.name,
            'description': self.description,
            'sequence': self.sequence,
        }
        
        chapter = self.env['sale.order.chapter'].create(chapter_vals)
        
        # Crear las secciones del capítulo
        for section_template in self.section_ids:
            section_template.create_section_from_template(chapter.id)
        
        return chapter