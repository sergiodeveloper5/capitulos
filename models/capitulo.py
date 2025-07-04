# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CapituloContrato(models.Model):
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'

    name = fields.Char(string='Nombre del Capítulo', required=True)
    description = fields.Text(string='Descripción')
    product_ids = fields.Many2many('product.product', string='Productos')
    condiciones_legales = fields.Text(string='Condiciones Legales')
    plantilla_id = fields.Many2one('capitulo.contrato', string='Basado en Plantilla', 
                                   help='Selecciona un capítulo existente como plantilla')
    es_plantilla = fields.Boolean(string='Es Plantilla', default=False,
                                  help='Marca este capítulo como plantilla para ser usado por otros')

    @api.onchange('plantilla_id')
    def _onchange_plantilla_id(self):
        """Carga los productos de la plantilla seleccionada"""
        if self.plantilla_id and not self.product_ids:
            # Copiar información básica de la plantilla
            self.description = self.plantilla_id.description
            self.condiciones_legales = self.plantilla_id.condiciones_legales
            
            # Copiar productos de la plantilla
            self.product_ids = [(6, 0, self.plantilla_id.product_ids.ids)]

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