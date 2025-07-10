# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaleOrderChapterSection(models.Model):
    _name = 'sale.order.chapter.section'
    _description = 'Sección de Capítulo en Presupuesto'
    _order = 'chapter_id, sequence, name'
    _rec_name = 'name'

    chapter_id = fields.Many2one(
        comodel_name='sale.order.chapter',
        string='Capítulo',
        required=True,
        ondelete='cascade'
    )
    
    template_section_id = fields.Many2one(
        comodel_name='sale.order.chapter.section.template',
        string='Plantilla de Sección',
        help='Plantilla utilizada para crear esta sección'
    )
    
    name = fields.Char(
        string='Nombre de la Sección',
        required=True
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
    
    is_readonly_commercial = fields.Boolean(
        string='Solo Lectura para Comercial',
        compute='_compute_readonly_commercial',
        store=True,
        help='Si está marcado, los comerciales no pueden editar esta sección'
    )
    
    line_ids = fields.One2many(
        comodel_name='sale.order.line',
        inverse_name='section_id',
        string='Líneas de Productos',
        help='Productos incluidos en esta sección'
    )
    
    sale_order_id = fields.Many2one(
        related='chapter_id.sale_order_id',
        string='Presupuesto',
        store=True
    )
    
    company_id = fields.Many2one(
        related='chapter_id.company_id',
        string='Compañía',
        store=True
    )
    
    partner_id = fields.Many2one(
        related='chapter_id.partner_id',
        string='Cliente',
        store=True
    )
    
    # Campos computados
    line_count = fields.Integer(
        string='Número de Líneas',
        compute='_compute_line_count',
        store=True
    )
    
    amount_total = fields.Monetary(
        string='Total de la Sección',
        compute='_compute_amount_total',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        related='sale_order_id.currency_id',
        string='Moneda',
        store=True
    )
    
    # Campos de control de permisos
    can_edit_commercial = fields.Boolean(
        string='Comercial Puede Editar',
        compute='_compute_can_edit_commercial'
    )
    
    can_delete_commercial = fields.Boolean(
        string='Comercial Puede Eliminar',
        compute='_compute_can_delete_commercial'
    )
    
    @api.depends('section_type')
    def _compute_readonly_commercial(self):
        """Calcula si la sección es de solo lectura para comerciales"""
        for record in self:
            if record.section_type in ['rental', 'assembly', 'conditions']:
                record.is_readonly_commercial = True
            else:
                record.is_readonly_commercial = False
    
    @api.depends('line_ids')
    def _compute_line_count(self):
        """Calcula el número de líneas en la sección"""
        for record in self:
            record.line_count = len(record.line_ids)
    
    @api.depends('line_ids.price_subtotal')
    def _compute_amount_total(self):
        """Calcula el total de la sección"""
        for record in self:
            record.amount_total = sum(line.price_subtotal for line in record.line_ids)
    
    @api.depends('section_type')
    def _compute_can_edit_commercial(self):
        """Determina si un comercial puede editar esta sección"""
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        is_admin = self.env.user.has_group('sermaco_chapters.group_chapter_admin')
        
        for record in self:
            if is_admin:
                record.can_edit_commercial = True
            elif is_commercial:
                record.can_edit_commercial = record.section_type in ['transport', 'other']
            else:
                record.can_edit_commercial = False
    
    @api.depends('section_type')
    def _compute_can_delete_commercial(self):
        """Determina si un comercial puede eliminar esta sección"""
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        is_admin = self.env.user.has_group('sermaco_chapters.group_chapter_admin')
        
        for record in self:
            if is_admin:
                record.can_delete_commercial = True
            elif is_commercial:
                # Los comerciales no pueden eliminar secciones fijas
                record.can_delete_commercial = False
            else:
                record.can_delete_commercial = False
    
    @api.constrains('name', 'chapter_id')
    def _check_name_unique_per_chapter(self):
        """Valida que el nombre de la sección sea único por capítulo"""
        for record in self:
            if self.search_count([
                ('name', '=', record.name),
                ('chapter_id', '=', record.chapter_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(
                    _("Ya existe una sección con el nombre '%s' en este capítulo.") % record.name
                )
    
    @api.constrains('section_type', 'chapter_id')
    def _check_conditions_section_unique(self):
        """Valida que solo haya una sección de condiciones por capítulo"""
        for record in self:
            if record.section_type == 'conditions':
                if self.search_count([
                    ('section_type', '=', 'conditions'),
                    ('chapter_id', '=', record.chapter_id.id),
                    ('id', '!=', record.id)
                ]) > 0:
                    raise ValidationError(
                        _("Solo puede haber una sección de 'Condiciones Generales' por capítulo.")
                    )
    
    def _check_commercial_permissions(self, operation='write'):
        """Verifica permisos de comercial para operaciones"""
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        is_admin = self.env.user.has_group('sermaco_chapters.group_chapter_admin')
        
        if is_admin:
            return True
        
        if is_commercial:
            for record in self:
                if operation == 'unlink' and record.section_type in ['rental', 'assembly', 'conditions']:
                    raise UserError(
                        _("No tiene permisos para eliminar la sección '%s'. "
                          "Las secciones de tipo '%s' son fijas.") % (record.name, dict(record._fields['section_type'].selection)[record.section_type])
                    )
                
                if operation == 'write' and record.section_type in ['rental', 'assembly', 'conditions']:
                    raise UserError(
                        _("No tiene permisos para modificar la sección '%s'. "
                          "Las secciones de tipo '%s' son de solo lectura para comerciales.") % (record.name, dict(record._fields['section_type'].selection)[record.section_type])
                    )
        
        return True
    
    @api.model
    def create(self, vals):
        """Sobrescribe create para ajustar la secuencia de condiciones"""
        if vals.get('section_type') == 'conditions':
            vals['sequence'] = 999  # Siempre al final
        return super().create(vals)
    
    def write(self, vals):
        """Sobrescribe write para verificar permisos y ajustar secuencia"""
        self._check_commercial_permissions('write')
        
        if vals.get('section_type') == 'conditions':
            vals['sequence'] = 999  # Siempre al final
        
        return super().write(vals)
    
    def unlink(self):
        """Sobrescribe unlink para verificar permisos"""
        self._check_commercial_permissions('unlink')
        return super().unlink()
    
    def action_view_lines(self):
        """Acción para ver las líneas de la sección"""
        self.ensure_one()
        return {
            'name': _('Líneas de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'list,form',
            'domain': [('section_id', '=', self.id)],
            'context': {
                'default_section_id': self.id,
                'default_chapter_id': self.chapter_id.id,
                'default_order_id': self.sale_order_id.id,
            },
            'target': 'current',
        }
    
    def action_add_product(self):
        """Acción para añadir producto a la sección"""
        self.ensure_one()
        
        # Verificar permisos
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        is_admin = self.env.user.has_group('sermaco_chapters.group_chapter_admin')
        
        if is_commercial and self.section_type not in ['transport', 'other']:
            raise UserError(
                _("No tiene permisos para añadir productos a la sección '%s'. "
                  "Solo puede añadir productos en secciones de 'Portes' y 'Otros Conceptos'.") % self.name
            )
        
        return {
            'name': _('Añadir Producto a %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'form',
            'context': {
                'default_section_id': self.id,
                'default_chapter_id': self.chapter_id.id,
                'default_order_id': self.sale_order_id.id,
            },
            'target': 'new',
        }