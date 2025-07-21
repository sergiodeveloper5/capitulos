# -*- coding: utf-8 -*-

"""
MODELO PRINCIPAL DE CAPÍTULOS DE CONTRATO
=========================================

Este archivo define el modelo principal 'capitulo.contrato' que gestiona
los capítulos técnicos y sus plantillas en el sistema de presupuestos.

CARACTERÍSTICAS PRINCIPALES:
- Sistema de plantillas reutilizables
- Gestión de dependencias entre capítulos
- Copia automática de secciones desde plantillas
- Validaciones para eliminación segura de plantillas
- Acciones para gestión de dependencias

ESTRUCTURA DE DATOS:
- Capítulos: Contenedores principales con nombre, descripción y condiciones legales
- Plantillas: Capítulos marcados como reutilizables
- Dependencias: Relaciones entre capítulos y sus plantillas base
- Secciones: Organizadas dentro de cada capítulo

FUNCIONALIDADES:
- Creación de capítulos desde plantillas existentes
- Copia automática de estructura completa (secciones + productos)
- Eliminación controlada con desvinculación automática
- Visualización de dependencias entre plantillas y capítulos

@author: Sistema de Capítulos Técnicos
@version: 1.0
@since: 2024
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CapituloContrato(models.Model):
    """
    MODELO PRINCIPAL DE CAPÍTULOS DE CONTRATO
    ========================================
    
    Gestiona los capítulos técnicos que organizan productos y servicios
    en presupuestos estructurados. Incluye sistema de plantillas para
    reutilización y estandarización de capítulos comunes.
    """
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'

    # ==========================================
    # CAMPOS BÁSICOS
    # ==========================================
    
    name = fields.Char(
        string='Nombre del Capítulo', 
        required=True,
        help='Nombre descriptivo del capítulo (ej: "Alquiler de Equipos", "Montaje Estructural")'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del alcance y contenido del capítulo'
    )
    
    condiciones_legales = fields.Text(
        string='Condiciones Legales',
        help='Términos y condiciones específicas aplicables a este capítulo'
    )

    # ==========================================
    # RELACIONES
    # ==========================================
    
    seccion_ids = fields.One2many(
        'capitulo.seccion', 
        'capitulo_id', 
        string='Secciones',
        help='Secciones que organizan los productos dentro del capítulo'
    )

    # ==========================================
    # SISTEMA DE PLANTILLAS
    # ==========================================
    
    plantilla_id = fields.Many2one(
        'capitulo.contrato', 
        string='Basado en Plantilla',
        domain=[('es_plantilla', '=', True)],
        help='Selecciona un capítulo existente como plantilla base'
    )
    
    es_plantilla = fields.Boolean(
        string='Es Plantilla', 
        default=False,
        help='Marca este capítulo como plantilla para ser reutilizado por otros capítulos'
    )
    
    capitulos_dependientes_count = fields.Integer(
        string='Capítulos Dependientes', 
        compute='_compute_capitulos_dependientes_count',
        help='Número de capítulos que utilizan esta plantilla como base'
    )

    # ==========================================
    # MÉTODOS COMPUTADOS
    # ==========================================
    
    @api.depends('es_plantilla')
    def _compute_capitulos_dependientes_count(self):
        """
        CONTADOR DE DEPENDENCIAS
        =======================
        
        Calcula cuántos capítulos utilizan este registro como plantilla.
        Útil para validar eliminaciones y mostrar el impacto de cambios.
        """
        for record in self:
            if record.es_plantilla:
                record.capitulos_dependientes_count = self.search_count([('plantilla_id', '=', record.id)])
            else:
                record.capitulos_dependientes_count = 0

    # ==========================================
    # EVENTOS DE CAMBIO
    # ==========================================

    @api.onchange('plantilla_id')
    def _onchange_plantilla_id(self):
        """
        COPIA AUTOMÁTICA DESDE PLANTILLA
        ================================
        
        Cuando se selecciona una plantilla, copia automáticamente:
        - Todas las secciones con su configuración
        - Todos los productos con cantidades y precios
        - Condiciones legales de la plantilla
        
        Esto permite crear capítulos consistentes basados en estructuras probadas.
        """
        if self.plantilla_id:
            # Limpiar secciones existentes para evitar duplicados
            self.seccion_ids = [(5, 0, 0)]
            
            # Copiar secciones de la plantilla con toda su estructura
            secciones_vals = []
            for seccion in self.plantilla_id.seccion_ids:
                # Copiar líneas de productos de cada sección
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
                
                # Crear la sección con sus productos
                secciones_vals.append((0, 0, {
                    'name': seccion.name,
                    'sequence': seccion.sequence,
                    'descripcion': seccion.descripcion,
                    'es_fija': seccion.es_fija,
                    'product_line_ids': lineas_vals,
                }))
            
            # Aplicar la estructura copiada
            self.seccion_ids = secciones_vals
            self.condiciones_legales = self.plantilla_id.condiciones_legales

    # ==========================================
    # ACCIONES DE USUARIO
    # ==========================================

    def action_crear_desde_plantilla(self):
        """
        ACCIÓN: CREAR DESDE PLANTILLA
        =============================
        
        Abre un formulario para crear un nuevo capítulo basado en esta plantilla.
        Útil para crear múltiples capítulos similares de forma rápida.
        """
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

    # ==========================================
    # GESTIÓN DE ELIMINACIÓN
    # ==========================================
    
    def unlink(self):
        """
        ELIMINACIÓN CONTROLADA DE PLANTILLAS
        ====================================
        
        Sobrescribe el método de eliminación para manejar plantillas con dependencias:
        - Si es una plantilla con capítulos dependientes, los desvincula automáticamente
        - Registra la operación en logs para auditoría
        - Permite eliminación segura sin romper referencias
        """
        for record in self:
            if record.es_plantilla:
                # Buscar capítulos que dependen de esta plantilla
                capitulos_usando_plantilla = self.search([('plantilla_id', '=', record.id)])
                if capitulos_usando_plantilla:
                    # Desvincular automáticamente en lugar de bloquear
                    capitulos_usando_plantilla.write({'plantilla_id': False})
                    # Registrar la operación para auditoría
                    _logger.info(
                        f"Plantilla '{record.name}' eliminada. Se han desvinculado {len(capitulos_usando_plantilla)} capítulos que la utilizaban."
                    )
        return super().unlink()
    
    def action_eliminar_plantilla_forzado(self):
        """
        ACCIÓN: ELIMINACIÓN FORZADA DE PLANTILLA
        ========================================
        
        Elimina una plantilla desvinculando automáticamente todos los capítulos
        que la utilizan. Muestra notificación detallada del impacto.
        """
        self.ensure_one()
        if not self.es_plantilla:
            raise UserError("Este registro no es una plantilla.")
        
        # Buscar y procesar dependencias
        capitulos_dependientes = self.search([('plantilla_id', '=', self.id)])
        
        if capitulos_dependientes:
            # Desvincular capítulos dependientes
            capitulos_dependientes.write({'plantilla_id': False})
            
            # Registrar operación en logs
            _logger.info(
                f"Plantilla '{self.name}' eliminada. Capítulos desvinculados: {', '.join(capitulos_dependientes.mapped('name'))}"
            )
            
            # Eliminar la plantilla
            nombre_plantilla = self.name
            self.unlink()
            
            # Notificar al usuario del impacto
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
        
        # Caso sin dependencias - eliminación directa
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
        """
        ACCIÓN: MOSTRAR DEPENDENCIAS
        ============================
        
        Muestra una lista de todos los capítulos que utilizan esta plantilla.
        Útil para evaluar el impacto antes de modificar o eliminar una plantilla.
        """
        self.ensure_one()
        if not self.es_plantilla:
            raise UserError("Este registro no es una plantilla.")
        
        capitulos_dependientes = self.search([('plantilla_id', '=', self.id)])
        
        # Caso sin dependencias
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
        
        # Mostrar lista de capítulos dependientes
        return {
            'type': 'ir.actions.act_window',
            'name': f'Capítulos que usan la plantilla: {self.name}',
            'res_model': 'capitulo.contrato',
            'view_mode': 'list,form',
            'domain': [('plantilla_id', '=', self.id)],
            'context': {'search_default_plantilla_id': self.id},
        }