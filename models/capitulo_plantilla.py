# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CapituloPlantilla(models.Model):
    _name = 'capitulo.plantilla'
    _description = 'Plantilla de Capítulo'
    _order = 'name'

    name = fields.Char('Nombre de la Plantilla', required=True)
    description = fields.Text('Descripción')
    
    # Secciones de la plantilla
    seccion_ids = fields.One2many('capitulo.seccion.plantilla', 'plantilla_id', 'Secciones')
    
    # Condiciones particulares
    condiciones_particulares = fields.Html('Condiciones Particulares')
    
    # Información adicional
    active = fields.Boolean('Activo', default=True)
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)
    
    # Campos de auditoría
    create_date = fields.Datetime('Fecha de Creación', readonly=True)
    create_uid = fields.Many2one('res.users', 'Creado por', readonly=True)
    write_date = fields.Datetime('Última Modificación', readonly=True)
    write_uid = fields.Many2one('res.users', 'Modificado por', readonly=True)
    
    def copy_to_capitulo(self, sale_order_id):
        """Copiar plantilla a un nuevo capítulo"""
        return self.env['capitulo.capitulo'].create_from_template(self.id, sale_order_id)
    
    @api.model
    def create_montacargas_template(self):
        """Crear plantilla de ejemplo MONTACARGAS MC-1700"""
        # Verificar si ya existe
        existing = self.search([('name', '=', 'MONTACARGAS MC-1700')])
        if existing:
            return existing
        
        # Crear la plantilla
        template_vals = {
            'name': 'MONTACARGAS MC-1700',
            'description': 'MONTACARGAS DE MATERIALES, CON PARA EN TERRAZA PARA DESEMBARCO.',
            'condiciones_particulares': '''
                <p><strong>CONDICIONES PARTICULARES</strong></p>
                <ol>
                    <li>La empresa proporcionará forma de corriente trifásica de 5 hilos (3F+N+T) de 32 amperios y diferencial a pie de cada equipo, para conexión de la misma.</li>
                    <li>Será por cuenta del cliente el acondicionamiento/aportado de terreno para el montaje.</li>
                    <li>Los trabajos de montaje y desmontaje se realizarán por SERMACO estos trabajos deberán ser realizados por personal cualificado por Sermaco, informes a los realizados por Sermaco, estos trabajos deberán estar incluidos en el precio del montaje, por lo que su importe será facturado aparte.</li>
                    <li>Los trabajos de montaje y desmontaje se realizarán en una sola fase continua, en caso de que deban ser realizados en varias fases por causas del cliente, los gastos de desplazamiento de personal y maquinaria serán por cuenta del cliente.</li>
                    <li>La empresa facilitará grúa torre o móvil para los montajes, desmontajes, cargas y descargas de materiales.</li>
                    <li>Los precios indicados no consideran que el montaje y desmontaje se realice en una sola fase continua, en caso de que deban ser realizados en varias fases por causas del cliente, los gastos de desplazamiento de personal y maquinaria serán por cuenta del cliente.</li>
                    <li>El cliente facilitará grúa torre o móvil para los montajes, desmontajes, cargas y descargas de materiales.</li>
                    <li>Los precios indicados no consideran trabajos nocturnos, festivos o en condiciones climatológicas adversas.</li>
                    <li>En el caso de que el cliente gestione el transporte de los materiales con sus medios, habrá de asumir un cargo por gestión de almacén de 50 euros por servicio.</li>
                    <li>Es responsabilidad del cliente garantizar la resistencia de la estructura portante así como de la zona de apoyo. Sermaco aportará información técnica de las cargas.</li>
                </ol>
            '''
        }
        
        template = self.create(template_vals)
        
        # Crear secciones por defecto
        secciones_data = [
            {'name': 'Alquiler', 'sequence': 10, 'es_fija': True},
            {'name': 'Montaje', 'sequence': 20, 'es_fija': True},
            {'name': 'Portes', 'sequence': 30, 'es_fija': False},
            {'name': 'Otros Conceptos', 'sequence': 40, 'es_fija': False},
        ]
        
        for seccion_data in secciones_data:
            seccion_data['plantilla_id'] = template.id
            self.env['capitulo.seccion.plantilla'].create(seccion_data)
        
        return template