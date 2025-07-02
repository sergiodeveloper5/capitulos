# -*- coding: utf-8 -*-

from odoo import models, fields, api

# Modelo principal de Capitulo de Contrato
class CapituloContrato(models.Model):
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'

    name = fields.Char(string='Nombre del Capítulo', required=True)
    description = fields.Text(string='Descripción del Capítulo')

    # Campo One2many que enlaza con las líneas de detalle del capítulo
    # 'capitulo.contrato.linea' es el _name del modelo de las líneas
    # 'capitulo_id' es el campo Many2one en el modelo de líneas que apunta a este modelo
    chapter_line_ids = fields.One2many(
        'capitulo.contrato.linea',
        'capitulo_id',
        string='Líneas de Detalle de Capítulo'
    )

    value = fields.Integer(string='Valor Base')
    value2 = fields.Float(compute="_value_pc", store=True, string='Valor Calculado')

    @api.depends('value')
    def _value_pc(self):
        for record in self:
            record.value2 = float(record.value) / 100

# Nuevo Modelo para las Líneas de Detalle del Capítulo
class CapituloContratoLinea(models.Model):
    _name = 'capitulo.contrato.linea'
    _description = 'Línea de Detalle del Capítulo de Contrato'

    name = fields.Char(string='Descripción de la Línea', required=True)

    # Campo 'type' que se usa en la vista anidada
    type = fields.Selection([
        ('material', 'Material'),
        ('mano_obra', 'Mano de Obra'),
        ('servicio', 'Servicio'),
        ('otro', 'Otro'),
    ], string='Tipo', default='material', required=True)

    # Campos 'precio_unitario' y 'cantidad' que se usan en la vista anidada
    precio_unitario = fields.Float(string='Precio Unitario', digits=(16, 2))
    cantidad = fields.Float(string='Cantidad', digits=(16, 2), default=1.0)
    total_linea = fields.Float(string='Total de Línea', compute='_compute_total_linea', store=True)

    # Campo Many2one que enlaza cada línea de detalle con su Capítulo padre
    capitulo_id = fields.Many2one(
        'capitulo.contrato',  # _name del modelo principal
        string='Capítulo Asociado',
        required=True,
        ondelete='cascade'  # Borra las líneas si se borra el capítulo
    )

    @api.depends('precio_unitario', 'cantidad')
    def _compute_total_linea(self):
        for record in self:
            record.total_linea = record.precio_unitario * record.cantidad