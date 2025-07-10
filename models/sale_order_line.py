# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    chapter_id = fields.Many2one(
        comodel_name='sale.order.chapter',
        string='Capítulo',
        help='Capítulo al que pertenece esta línea',
        ondelete='set null'
    )
    
    section_id = fields.Many2one(
        comodel_name='sale.order.chapter.section',
        string='Sección',
        help='Sección del capítulo a la que pertenece esta línea',
        ondelete='set null'
    )
    
    # Campos relacionados para facilitar búsquedas y reportes
    chapter_name = fields.Char(
        related='chapter_id.name',
        string='Nombre del Capítulo',
        store=True
    )
    
    section_name = fields.Char(
        related='section_id.name',
        string='Nombre de la Sección',
        store=True
    )
    
    section_type = fields.Selection(
        related='section_id.section_type',
        string='Tipo de Sección',
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
    
    @api.depends('section_id.section_type')
    def _compute_can_edit_commercial(self):
        """Determina si un comercial puede editar esta línea"""
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        is_admin = self.env.user.has_group('sermaco_chapters.group_chapter_admin')
        
        for record in self:
            if is_admin:
                record.can_edit_commercial = True
            elif is_commercial:
                if record.section_id:
                    record.can_edit_commercial = record.section_id.section_type in ['transport', 'other']
                else:
                    record.can_edit_commercial = True  # Líneas sin sección pueden editarse
            else:
                record.can_edit_commercial = False
    
    @api.depends('section_id.section_type')
    def _compute_can_delete_commercial(self):
        """Determina si un comercial puede eliminar esta línea"""
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        is_admin = self.env.user.has_group('sermaco_chapters.group_chapter_admin')
        
        for record in self:
            if is_admin:
                record.can_delete_commercial = True
            elif is_commercial:
                if record.section_id:
                    record.can_delete_commercial = record.section_id.section_type in ['transport', 'other']
                else:
                    record.can_delete_commercial = True  # Líneas sin sección pueden eliminarse
            else:
                record.can_delete_commercial = False
    
    @api.onchange('chapter_id')
    def _onchange_chapter_id(self):
        """Limpia la sección cuando cambia el capítulo"""
        if self.chapter_id:
            self.section_id = False
            return {
                'domain': {
                    'section_id': [('chapter_id', '=', self.chapter_id.id)]
                }
            }
        else:
            self.section_id = False
            return {
                'domain': {
                    'section_id': [('id', '=', False)]
                }
            }
    
    @api.onchange('section_id')
    def _onchange_section_id(self):
        """Actualiza el capítulo cuando cambia la sección"""
        if self.section_id:
            self.chapter_id = self.section_id.chapter_id
    
    def _check_commercial_permissions(self, operation='write'):
        """Verifica permisos de comercial para operaciones en líneas"""
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        is_admin = self.env.user.has_group('sermaco_chapters.group_chapter_admin')
        
        if is_admin:
            return True
        
        if is_commercial:
            for record in self:
                if record.section_id and record.section_id.section_type in ['rental', 'assembly', 'conditions']:
                    section_type_name = dict(record.section_id._fields['section_type'].selection)[record.section_id.section_type]
                    
                    if operation == 'unlink':
                        raise UserError(
                            _("No tiene permisos para eliminar productos de la sección '%s'. "
                              "Las secciones de tipo '%s' son de solo lectura para comerciales.") % 
                            (record.section_id.name, section_type_name)
                        )
                    
                    if operation == 'write':
                        raise UserError(
                            _("No tiene permisos para modificar productos de la sección '%s'. "
                              "Las secciones de tipo '%s' son de solo lectura para comerciales.") % 
                            (record.section_id.name, section_type_name)
                        )
        
        return True
    
    @api.model
    def create(self, vals):
        """Sobrescribe create para validaciones adicionales"""
        # Si se especifica una sección, asegurar que el capítulo coincida
        if vals.get('section_id'):
            section = self.env['sale.order.chapter.section'].browse(vals['section_id'])
            vals['chapter_id'] = section.chapter_id.id
        
        return super().create(vals)
    
    def write(self, vals):
        """Sobrescribe write para verificar permisos"""
        # Verificar permisos antes de modificar
        self._check_commercial_permissions('write')
        
        # Si se especifica una sección, asegurar que el capítulo coincida
        if vals.get('section_id'):
            section = self.env['sale.order.chapter.section'].browse(vals['section_id'])
            vals['chapter_id'] = section.chapter_id.id
        
        # Si se cambia el capítulo, limpiar la sección si no pertenece al nuevo capítulo
        if vals.get('chapter_id'):
            for record in self:
                if record.section_id and record.section_id.chapter_id.id != vals['chapter_id']:
                    vals['section_id'] = False
        
        return super().write(vals)
    
    def unlink(self):
        """Sobrescribe unlink para verificar permisos"""
        self._check_commercial_permissions('unlink')
        return super().unlink()
    
    def action_move_to_section(self):
        """Acción para mover la línea a otra sección"""
        self.ensure_one()
        
        # Verificar permisos
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        
        if is_commercial and self.section_id and self.section_id.section_type in ['rental', 'assembly', 'conditions']:
            raise UserError(
                _("No tiene permisos para mover productos de secciones de solo lectura.")
            )
        
        return {
            'name': _('Mover a Sección'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'res_id': self.id,
            'view_mode': 'form',
            'context': {
                'form_view_ref': 'sermaco_chapters.sale_order_line_move_section_form',
            },
            'target': 'new',
        }
    
    @api.model
    def _get_chapter_section_info(self):
        """Método auxiliar para obtener información de capítulos y secciones"""
        result = []
        for line in self:
            info = {
                'line_id': line.id,
                'product_name': line.product_id.name,
                'chapter_name': line.chapter_name or 'Sin Capítulo',
                'section_name': line.section_name or 'Sin Sección',
                'section_type': line.section_type or False,
                'can_edit': line.can_edit_commercial,
                'can_delete': line.can_delete_commercial,
            }
            result.append(info)
        return result