# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    chapter_ids = fields.One2many(
        comodel_name='sale.order.chapter',
        inverse_name='sale_order_id',
        string='Capítulos',
        help='Capítulos organizados en este presupuesto'
    )
    
    # Campos computados
    chapter_count = fields.Integer(
        string='Número de Capítulos',
        compute='_compute_chapter_count',
        store=True
    )
    
    has_chapters = fields.Boolean(
        string='Tiene Capítulos',
        compute='_compute_has_chapters',
        store=True
    )
    
    chapter_amount_total = fields.Monetary(
        string='Total de Capítulos',
        compute='_compute_chapter_amount_total',
        store=True,
        help='Suma total de todos los capítulos'
    )
    
    @api.depends('chapter_ids')
    def _compute_chapter_count(self):
        """Calcula el número de capítulos en el presupuesto"""
        for record in self:
            record.chapter_count = len(record.chapter_ids)
    
    @api.depends('chapter_ids')
    def _compute_has_chapters(self):
        """Determina si el presupuesto tiene capítulos"""
        for record in self:
            record.has_chapters = bool(record.chapter_ids)
    
    @api.depends('chapter_ids.amount_total')
    def _compute_chapter_amount_total(self):
        """Calcula el total de todos los capítulos"""
        for record in self:
            record.chapter_amount_total = sum(chapter.amount_total for chapter in record.chapter_ids)
    
    def action_view_chapters(self):
        """Acción para ver los capítulos del presupuesto"""
        self.ensure_one()
        return {
            'name': _('Capítulos de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.chapter',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {
                'default_sale_order_id': self.id,
                'search_default_sale_order_id': self.id,
            },
            'target': 'current',
        }
    
    def action_add_chapter_wizard(self):
        """Acción para abrir el wizard de añadir capítulos"""
        self.ensure_one()
        return {
            'name': _('Añadir Capítulos'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.chapter.wizard',
            'view_mode': 'form',
            'context': {
                'default_sale_order_id': self.id,
            },
            'target': 'new',
        }
    
    def action_chapter_hierarchy_view(self):
        """Acción para ver la vista jerárquica de capítulos"""
        self.ensure_one()
        return {
            'name': _('Vista Jerárquica - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('sermaco_chapters.sale_order_chapter_hierarchy_form').id,
            'target': 'current',
        }
    
    def _ensure_conditions_sections(self):
        """Asegura que todos los capítulos tengan su sección de condiciones"""
        for chapter in self.chapter_ids:
            chapter.add_conditions_section()
    
    def action_organize_by_chapters(self):
        """Organiza las líneas existentes en capítulos automáticamente"""
        self.ensure_one()
        
        # Crear un capítulo "General" para líneas sin capítulo
        lines_without_chapter = self.order_line.filtered(lambda l: not l.chapter_id)
        
        if lines_without_chapter:
            general_chapter = self.env['sale.order.chapter'].create({
                'sale_order_id': self.id,
                'name': 'General',
                'description': 'Productos sin capítulo específico',
                'sequence': 1,
            })
            
            # Crear sección "Otros Conceptos" en el capítulo general
            other_section = self.env['sale.order.chapter.section'].create({
                'chapter_id': general_chapter.id,
                'name': 'Otros Conceptos',
                'sequence': 1,
                'section_type': 'other',
            })
            
            # Asignar las líneas a la sección
            lines_without_chapter.write({
                'chapter_id': general_chapter.id,
                'section_id': other_section.id,
            })
        
        return self.action_view_chapters()
    
    @api.model
    def create(self, vals):
        """Sobrescribe create para configuraciones iniciales"""
        order = super().create(vals)
        return order
    
    def write(self, vals):
        """Sobrescribe write para mantener consistencia"""
        result = super().write(vals)
        
        # Si se confirma el presupuesto, asegurar secciones de condiciones
        if vals.get('state') == 'sale':
            for order in self:
                order._ensure_conditions_sections()
        
        return result