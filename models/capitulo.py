# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CapituloContrato(models.Model):
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'
    _inherit = ['product.template']
    _order = 'name'
    
    # Configuración por defecto para productos de tipo capítulo
    @api.model
    def _get_default_category_id(self):
        category = self.env.ref('capitulos.product_category_capitulos', raise_if_not_found=False)
        return category.id if category else False

    # Heredamos name de product.template
    description = fields.Text(string='Descripción')
    seccion_ids = fields.One2many('capitulo.seccion', 'capitulo_id', string='Secciones')
    condiciones_legales = fields.Text(string='Condiciones Legales')
    plantilla_id = fields.Many2one('capitulo.contrato', string='Basado en Plantilla', 
                                   domain="[('es_plantilla', '=', True)]",
                                   help='Selecciona un capítulo existente como plantilla')
    es_plantilla = fields.Boolean(string='Es Plantilla', default=False,
                                  help='Marca este capítulo como plantilla para ser usado por otros')
    
    # Configuración específica para productos de tipo capítulo
    type = fields.Selection(default='service')
    categ_id = fields.Many2one(default=_get_default_category_id)
    is_capitulo = fields.Boolean(string='Es Capítulo', default=True)
    
    # Atributos para configuración de secciones
    attribute_line_ids = fields.One2many(
        'product.template.attribute.line', 'product_tmpl_id',
        string='Secciones Configurables',
        copy=True
    )
    capitulos_dependientes_count = fields.Integer(
        string='Capítulos Dependientes', 
        compute='_compute_capitulos_dependientes_count',
        help='Número de capítulos que usan esta plantilla'
    )
    
    @api.depends('es_plantilla')
    def _compute_capitulos_dependientes_count(self):
        """Calcula el número de capítulos que dependen de esta plantilla"""
        for record in self:
            if record.es_plantilla:
                record.capitulos_dependientes_count = self.search_count([('plantilla_id', '=', record.id)])
            else:
                record.capitulos_dependientes_count = 0

    @api.onchange('plantilla_id')
    def _onchange_plantilla_id(self):
        """Copia las secciones y productos de la plantilla seleccionada"""
        if self.plantilla_id:
            # Limpiar secciones existentes
            self.seccion_ids = [(5, 0, 0)]
            
            # Copiar secciones de la plantilla
            secciones_vals = []
            for seccion in self.plantilla_id.seccion_ids:
                # Copiar líneas de productos de la sección
                lineas_vals = []
                for linea in seccion.product_line_ids:
                    lineas_vals.append((0, 0, {
                        'product_id': linea.product_id.id,
                        'cantidad': linea.cantidad,
                        'precio_unitario': linea.precio_unitario,
                        'sequence': linea.sequence,
                        'descripcion_personalizada': linea.descripcion_personalizada,
                        'es_opcional': linea.es_opcional,
                    }))
                
                secciones_vals.append((0, 0, {
                    'name': seccion.name,
                    'sequence': seccion.sequence,
                    'descripcion': seccion.descripcion,
                    'es_fija': seccion.es_fija,
                    'product_line_ids': lineas_vals,
                }))
            
            self.seccion_ids = secciones_vals
            self.condiciones_legales = self.plantilla_id.condiciones_legales

    def action_crear_desde_plantilla(self):
        """Acción para crear un nuevo capítulo desde una plantilla"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Capítulo desde Plantilla',
            'res_model': 'capitulo.contrato',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_plantilla_id': self.id,
                'form_view_initial_mode': 'edit',
            }
        }
    
    def unlink(self):
        """Permite eliminar plantillas con validaciones mejoradas"""
        for record in self:
            if record.es_plantilla:
                # Verificar si la plantilla está siendo utilizada
                capitulos_usando_plantilla = self.search([('plantilla_id', '=', record.id)])
                if capitulos_usando_plantilla:
                    # En lugar de bloquear completamente, limpiar las referencias
                    capitulos_usando_plantilla.write({'plantilla_id': False})
                    # Mostrar mensaje informativo
                    _logger.info(
                        f"Plantilla '{record.name}' eliminada. Se han desvinculado {len(capitulos_usando_plantilla)} capítulos que la utilizaban."
                    )
        return super().unlink()
    
    def action_eliminar_plantilla_forzado(self):
        """Acción para eliminar una plantilla forzadamente, desvinculando capítulos dependientes"""
        self.ensure_one()
        if not self.es_plantilla:
            raise UserError("Este registro no es una plantilla.")
        
        # Buscar capítulos que usan esta plantilla
        capitulos_dependientes = self.search([('plantilla_id', '=', self.id)])
        
        if capitulos_dependientes:
            # Desvincular capítulos dependientes
            capitulos_dependientes.write({'plantilla_id': False})
            
            # Log de la operación
            _logger.info(
                f"Plantilla '{self.name}' eliminada. Capítulos desvinculados: {', '.join(capitulos_dependientes.mapped('name'))}"
            )
            
            # Eliminar la plantilla
            nombre_plantilla = self.name
            self.unlink()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Plantilla Eliminada',
                    'message': f'La plantilla "{nombre_plantilla}" ha sido eliminada. Se han desvinculado {len(capitulos_dependientes)} capítulos que la utilizaban: {', '.join(capitulos_dependientes.mapped("name"))}',
                    'type': 'success',
                    'sticky': True,
                }
            }
        
        # Eliminar la plantilla (sin dependencias)
        nombre_plantilla = self.name
        self.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Plantilla Eliminada',
                'message': f'La plantilla "{nombre_plantilla}" ha sido eliminada exitosamente.',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_mostrar_dependencias(self):
        """Muestra los capítulos que dependen de esta plantilla"""
        self.ensure_one()
        if not self.es_plantilla:
            raise UserError("Este registro no es una plantilla.")
        
        capitulos_dependientes = self.search([('plantilla_id', '=', self.id)])
        
        if not capitulos_dependientes:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin Dependencias',
                    'message': f'La plantilla "{self.name}" no está siendo utilizada por ningún capítulo. Puede eliminarla de forma segura.',
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Capítulos que usan la plantilla: {self.name}',
            'res_model': 'capitulo.contrato',
            'view_mode': 'list,form',
            'domain': [('plantilla_id', '=', self.id)],
            'context': {'search_default_plantilla_id': self.id},
        }