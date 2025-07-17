# -*- coding: utf-8 -*-
"""
Módulo de Capítulos Técnicos para Odoo 18
==========================================

Este módulo permite organizar presupuestos y pedidos de venta en una estructura 
jerárquica de capítulos y secciones técnicas, con un sistema avanzado de plantillas.

Autor: Sergio Vadillo
Fecha: Diciembre 2024
Versión: 18.0.1.1.0
"""

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

# Configuración del logger para debugging y monitoreo
_logger = logging.getLogger(__name__)

class CapituloContrato(models.Model):
    """
    Modelo principal para la gestión de capítulos técnicos.
    
    Este modelo representa la estructura principal de un capítulo técnico que puede
    contener múltiples secciones organizadas por tipo de servicio (alquiler, montaje,
    desmontaje, portes, otros).
    
    Características principales:
    - Sistema de plantillas reutilizables
    - Gestión de dependencias entre plantillas y capítulos
    - Estructura jerárquica: Capítulo → Secciones → Productos
    - Integración con pedidos de venta de Odoo
    """
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'

    # ========================================
    # CAMPOS BÁSICOS DEL CAPÍTULO
    # ========================================
    
    name = fields.Char(
        string='Nombre del Capítulo', 
        required=True,
        help='Nombre identificativo del capítulo técnico'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del capítulo y su propósito'
    )
    
    # ========================================
    # RELACIONES CON OTROS MODELOS
    # ========================================
    
    seccion_ids = fields.One2many(
        'capitulo.seccion', 
        'capitulo_id', 
        string='Secciones',
        help='Secciones que componen este capítulo (alquiler, montaje, etc.)'
    )
    
    condiciones_legales = fields.Text(
        string='Condiciones Legales',
        help='Condiciones legales específicas aplicables a este capítulo'
    )
    
    # ========================================
    # SISTEMA DE PLANTILLAS
    # ========================================
    
    plantilla_id = fields.Many2one(
        'capitulo.contrato', 
        string='Basado en Plantilla', 
        help='Selecciona un capítulo existente como plantilla para copiar su estructura'
    )
    
    es_plantilla = fields.Boolean(
        string='Es Plantilla', 
        default=False,
        help='Marca este capítulo como plantilla para ser reutilizado por otros capítulos'
    )
    
    # ========================================
    # CAMPOS COMPUTADOS
    # ========================================
    
    capitulos_dependientes_count = fields.Integer(
        string='Capítulos Dependientes', 
        compute='_compute_capitulos_dependientes_count',
        help='Número de capítulos que utilizan esta plantilla como base'
    )
    
    # ========================================
    # MÉTODOS COMPUTADOS
    # ========================================
    
    @api.depends('es_plantilla')
    def _compute_capitulos_dependientes_count(self):
        """
        Calcula el número de capítulos que dependen de esta plantilla.
        
        Este método se ejecuta automáticamente cuando cambia el campo 'es_plantilla'
        y cuenta cuántos capítulos utilizan este registro como plantilla base.
        
        Returns:
            None: Actualiza el campo capitulos_dependientes_count directamente
        """
        for record in self:
            if record.es_plantilla:
                # Buscar todos los capítulos que referencian este como plantilla
                record.capitulos_dependientes_count = self.search_count([
                    ('plantilla_id', '=', record.id)
                ])
            else:
                # Si no es plantilla, no puede tener dependientes
                record.capitulos_dependientes_count = 0

    # ========================================
    # MÉTODOS DE EVENTOS (ONCHANGE)
    # ========================================

    @api.onchange('plantilla_id')
    def _onchange_plantilla_id(self):
        """
        Copia automáticamente la estructura de la plantilla seleccionada.
        
        Este método se ejecuta cuando el usuario selecciona una plantilla en el formulario
        y copia todas las secciones, productos y configuraciones de la plantilla al
        capítulo actual.
        
        Proceso:
        1. Limpia las secciones existentes
        2. Copia cada sección de la plantilla
        3. Para cada sección, copia todas sus líneas de productos
        4. Copia las condiciones legales de la plantilla
        
        Returns:
            None: Modifica los campos del registro actual
        """
        if self.plantilla_id:
            # Paso 1: Limpiar secciones existentes para evitar duplicados
            self.seccion_ids = [(5, 0, 0)]  # Comando (5,0,0) elimina todos los registros
            
            # Paso 2: Copiar secciones de la plantilla
            secciones_vals = []
            for seccion in self.plantilla_id.seccion_ids:
                # Paso 3: Copiar líneas de productos de cada sección
                lineas_vals = []
                for linea in seccion.product_line_ids:
                    # Comando (0,0,{}) crea un nuevo registro con los valores especificados
                    lineas_vals.append((0, 0, {
                        'product_id': linea.product_id.id,
                        'cantidad': linea.cantidad,
                        'precio_unitario': linea.precio_unitario,
                        'sequence': linea.sequence,
                        'descripcion_personalizada': linea.descripcion_personalizada,
                        'es_opcional': linea.es_opcional,
                    }))
                
                # Crear la sección con sus líneas de productos
                secciones_vals.append((0, 0, {
                    'name': seccion.name,
                    'sequence': seccion.sequence,
                    'descripcion': seccion.descripcion,
                    'es_fija': seccion.es_fija,
                    'product_category_id': seccion.product_category_id.id if seccion.product_category_id else False,
                    'product_line_ids': lineas_vals,
                }))
            
            # Aplicar todas las secciones copiadas
            self.seccion_ids = secciones_vals
            
            # Paso 4: Copiar condiciones legales
            self.condiciones_legales = self.plantilla_id.condiciones_legales

    # ========================================
    # MÉTODOS DE ACCIÓN (BOTONES)
    # ========================================

    def action_crear_desde_plantilla(self):
        """
        Acción para crear un nuevo capítulo basado en esta plantilla.
        
        Este método se ejecuta cuando el usuario hace clic en el botón "Crear desde Plantilla"
        y abre un formulario para crear un nuevo capítulo utilizando este registro como base.
        
        Returns:
            dict: Acción de ventana para abrir el formulario de creación
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Capítulo desde Plantilla',
            'res_model': 'capitulo.contrato',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_plantilla_id': self.id,  # Pre-seleccionar esta plantilla
                'form_view_initial_mode': 'edit',  # Abrir en modo edición
            }
        }
    
    # ========================================
    # MÉTODOS DE CICLO DE VIDA (ORM HOOKS)
    # ========================================
    
    def unlink(self):
        """
        Sobrescribe el método de eliminación para manejar plantillas con dependencias.
        
        Este método se ejecuta antes de eliminar registros y maneja el caso especial
        de plantillas que están siendo utilizadas por otros capítulos.
        
        Comportamiento:
        - Si es una plantilla con dependencias: desvincula los capítulos dependientes
        - Si no es plantilla o no tiene dependencias: eliminación normal
        - Registra la operación en logs para auditoría
        
        Returns:
            bool: True si la eliminación fue exitosa
        """
        for record in self:
            if record.es_plantilla:
                # Verificar si la plantilla está siendo utilizada
                capitulos_usando_plantilla = self.search([('plantilla_id', '=', record.id)])
                if capitulos_usando_plantilla:
                    # Desvincular automáticamente en lugar de bloquear la eliminación
                    capitulos_usando_plantilla.write({'plantilla_id': False})
                    
                    # Registrar la operación para auditoría
                    _logger.info(
                        f"Plantilla '{record.name}' eliminada. Se han desvinculado "
                        f"{len(capitulos_usando_plantilla)} capítulos que la utilizaban."
                    )
        
        # Proceder con la eliminación normal
        return super().unlink()
    
    # ========================================
    # MÉTODOS DE GESTIÓN DE PLANTILLAS
    # ========================================
    
    def action_eliminar_plantilla_forzado(self):
        """
        Elimina una plantilla forzadamente, desvinculando todos los capítulos dependientes.
        
        Este método proporciona una forma segura de eliminar plantillas que están en uso,
        desvinculando automáticamente todos los capítulos que la utilizan y mostrando
        una notificación detallada al usuario.
        
        Proceso:
        1. Valida que el registro sea una plantilla
        2. Busca todos los capítulos dependientes
        3. Desvincula los capítulos (plantilla_id = False)
        4. Elimina la plantilla
        5. Muestra notificación con detalles de la operación
        
        Returns:
            dict: Acción de notificación con el resultado de la operación
            
        Raises:
            UserError: Si el registro no es una plantilla
        """
        self.ensure_one()
        if not self.es_plantilla:
            raise UserError("Este registro no es una plantilla.")
        
        # Buscar capítulos que usan esta plantilla
        capitulos_dependientes = self.search([('plantilla_id', '=', self.id)])
        
        if capitulos_dependientes:
            # Desvincular capítulos dependientes
            capitulos_dependientes.write({'plantilla_id': False})
            
            # Registrar la operación en logs
            _logger.info(
                f"Plantilla '{self.name}' eliminada. Capítulos desvinculados: "
                f"{', '.join(capitulos_dependientes.mapped('name'))}"
            )
            
            # Guardar información antes de eliminar
            nombre_plantilla = self.name
            nombres_dependientes = capitulos_dependientes.mapped('name')
            
            # Eliminar la plantilla
            self.unlink()
            
            # Mostrar notificación detallada
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Plantilla Eliminada',
                    'message': (
                        f'La plantilla "{nombre_plantilla}" ha sido eliminada. '
                        f'Se han desvinculado {len(nombres_dependientes)} capítulos que la utilizaban: '
                        f'{", ".join(nombres_dependientes)}'
                    ),
                    'type': 'success',
                    'sticky': True,  # Notificación persistente para operaciones importantes
                }
            }
        
        # Caso: plantilla sin dependencias
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