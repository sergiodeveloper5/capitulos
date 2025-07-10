# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SaleOrderChapterWizard(models.TransientModel):
    _name = 'sale.order.chapter.wizard'
    _description = 'Wizard para Añadir Capítulos a Presupuestos'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Presupuesto',
        required=True,
        readonly=True
    )
    
    action_type = fields.Selection([
        ('add_template', 'Añadir desde Plantillas'),
        ('create_new', 'Crear Nuevo Capítulo')
    ], string='Tipo de Acción', required=True, default='add_template')
    
    # Campos para añadir desde plantillas
    template_ids = fields.Many2many(
        comodel_name='sale.order.chapter.template',
        relation='wizard_chapter_template_rel',
        column1='wizard_id',
        column2='template_id',
        string='Plantillas de Capítulos',
        help='Seleccione las plantillas que desea añadir al presupuesto'
    )
    
    # Campos para crear nuevo capítulo
    new_chapter_name = fields.Char(
        string='Nombre del Nuevo Capítulo',
        help='Nombre para el nuevo capítulo'
    )
    
    new_chapter_description = fields.Text(
        string='Descripción del Nuevo Capítulo',
        help='Descripción detallada del nuevo capítulo'
    )
    
    new_chapter_sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden del nuevo capítulo en el presupuesto'
    )
    
    # Campos informativos
    existing_chapter_count = fields.Integer(
        string='Capítulos Existentes',
        compute='_compute_existing_chapter_count'
    )
    
    available_template_count = fields.Integer(
        string='Plantillas Disponibles',
        compute='_compute_available_template_count'
    )
    
    company_id = fields.Many2one(
        related='sale_order_id.company_id',
        string='Compañía'
    )
    
    @api.depends('sale_order_id.chapter_ids')
    def _compute_existing_chapter_count(self):
        """Calcula el número de capítulos existentes en el presupuesto"""
        for record in self:
            record.existing_chapter_count = len(record.sale_order_id.chapter_ids)
    
    @api.depends('company_id')
    def _compute_available_template_count(self):
        """Calcula el número de plantillas disponibles"""
        for record in self:
            templates = self.env['sale.order.chapter.template'].search([
                ('active', '=', True),
                ('company_id', '=', record.company_id.id)
            ])
            record.available_template_count = len(templates)
    
    @api.onchange('action_type')
    def _onchange_action_type(self):
        """Limpia campos cuando cambia el tipo de acción"""
        if self.action_type == 'add_template':
            self.new_chapter_name = False
            self.new_chapter_description = False
            self.new_chapter_sequence = 10
        else:
            self.template_ids = [(5, 0, 0)]  # Limpiar selección
    
    @api.constrains('new_chapter_name', 'action_type')
    def _check_new_chapter_name(self):
        """Valida que se proporcione nombre para nuevo capítulo"""
        for record in self:
            if record.action_type == 'create_new' and not record.new_chapter_name:
                raise ValidationError(
                    _("Debe proporcionar un nombre para el nuevo capítulo.")
                )
    
    @api.constrains('template_ids', 'action_type')
    def _check_template_selection(self):
        """Valida que se seleccionen plantillas cuando corresponde"""
        for record in self:
            if record.action_type == 'add_template' and not record.template_ids:
                raise ValidationError(
                    _("Debe seleccionar al menos una plantilla de capítulo.")
                )
    
    def _check_duplicate_chapters(self, chapter_names):
        """Verifica si ya existen capítulos con los nombres dados"""
        existing_names = self.sale_order_id.chapter_ids.mapped('name')
        duplicates = set(chapter_names) & set(existing_names)
        
        if duplicates:
            raise UserError(
                _("Ya existen capítulos con los siguientes nombres en este presupuesto: %s") % 
                ', '.join(duplicates)
            )
    
    def action_add_chapters(self):
        """Acción principal para añadir capítulos"""
        self.ensure_one()
        
        if self.action_type == 'add_template':
            return self._add_chapters_from_templates()
        else:
            return self._create_new_chapter()
    
    def _add_chapters_from_templates(self):
        """Añade capítulos desde plantillas seleccionadas"""
        if not self.template_ids:
            raise UserError(_("Debe seleccionar al menos una plantilla."))
        
        # Verificar duplicados
        template_names = self.template_ids.mapped('name')
        self._check_duplicate_chapters(template_names)
        
        created_chapters = self.env['sale.order.chapter']
        
        for template in self.template_ids:
            chapter = template.create_chapter_from_template(self.sale_order_id.id)
            created_chapters |= chapter
        
        # Mensaje de éxito
        message = _("Se han añadido %d capítulos desde plantillas:") % len(created_chapters)
        for chapter in created_chapters:
            message += "\n• %s" % chapter.name
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Capítulos Añadidos'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _create_new_chapter(self):
        """Crea un nuevo capítulo básico"""
        if not self.new_chapter_name:
            raise UserError(_("Debe proporcionar un nombre para el nuevo capítulo."))
        
        # Verificar duplicados
        self._check_duplicate_chapters([self.new_chapter_name])
        
        # Crear el capítulo
        chapter_vals = {
            'sale_order_id': self.sale_order_id.id,
            'name': self.new_chapter_name,
            'description': self.new_chapter_description,
            'sequence': self.new_chapter_sequence,
        }
        
        chapter = self.env['sale.order.chapter'].create(chapter_vals)
        
        # Crear secciones básicas para comerciales
        is_commercial = self.env.user.has_group('sermaco_chapters.group_chapter_commercial')
        
        if is_commercial:
            # Crear secciones básicas que el comercial puede usar
            basic_sections = [
                {
                    'name': 'Portes',
                    'section_type': 'transport',
                    'sequence': 1,
                },
                {
                    'name': 'Otros Conceptos',
                    'section_type': 'other',
                    'sequence': 2,
                }
            ]
            
            for section_data in basic_sections:
                section_data.update({
                    'chapter_id': chapter.id,
                })
                self.env['sale.order.chapter.section'].create(section_data)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Capítulo Creado'),
                'message': _("Se ha creado el capítulo '%s' exitosamente.") % chapter.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_preview_templates(self):
        """Acción para previsualizar las plantillas seleccionadas"""
        self.ensure_one()
        
        if not self.template_ids:
            raise UserError(_("Debe seleccionar al menos una plantilla para previsualizar."))
        
        return {
            'name': _('Vista Previa de Plantillas'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.chapter.template',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.template_ids.ids)],
            'target': 'new',
        }
    
    def action_view_existing_chapters(self):
        """Acción para ver los capítulos existentes en el presupuesto"""
        self.ensure_one()
        
        return {
            'name': _('Capítulos Existentes'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.chapter',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.sale_order_id.id)],
            'target': 'new',
        }
    
    @api.model
    def default_get(self, fields_list):
        """Establece valores por defecto"""
        result = super().default_get(fields_list)
        
        # Si se llama desde un presupuesto, establecer el ID
        if self.env.context.get('active_model') == 'sale.order':
            result['sale_order_id'] = self.env.context.get('active_id')
        
        return result