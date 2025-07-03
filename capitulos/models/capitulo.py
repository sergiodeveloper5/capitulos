# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CapituloContrato(models.Model):
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'

    name = fields.Char(string='Nombre del Capítulo', required=True)
    codigo = fields.Char(string='Código', required=True)
    description = fields.Text(string='Descripción')
    componente_ids = fields.One2many('capitulo.componente', 'capitulo_id', string='Componentes')
    condiciones_legales = fields.Text(string='Condiciones Legales')