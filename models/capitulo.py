# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CapituloContrato(models.Model):
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'

    name = fields.Char(string='Nombre del Capítulo', required=True)
    description = fields.Text(string='Descripción')
    seccion_ids = fields.One2many('capitulo.seccion', 'capitulo_id', string='Secciones')
    condiciones_legales = fields.Text(string='Condiciones Legales')
    plantilla_id = fields.Many2one('capitulo.contrato', string='Basado en Plantilla', 
                                   help='Selecciona un capítulo existente como plantilla')
    es_plantilla = fields.Boolean(string='Es Plantilla', default=False,
                                  help='Marca este capítulo como plantilla para ser usado por otros')

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