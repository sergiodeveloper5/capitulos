# -*- coding: utf-8 -*-
"""
MODELO PRINCIPAL: CAPÍTULO DE CONTRATO
=====================================

Este archivo define el modelo principal 'capitulo.contrato' que gestiona
los capítulos técnicos del sistema. Los capítulos son estructuras organizativas
que contienen secciones y productos para presupuestos de venta.

FUNCIONALIDADES PRINCIPALES:
1. Gestión de capítulos técnicos con secciones anidadas
2. Sistema de plantillas para reutilización de capítulos
3. Validaciones de integridad y dependencias
4. Operaciones CRUD con logging avanzado
5. Integración con presupuestos de venta (sale.order)

ARQUITECTURA DE DATOS:
- Capítulo (1) → Secciones (N) → Líneas de Producto (N)
- Relación de plantillas: Plantilla (1) → Capítulos derivados (N)
- Integración: Sale Order (N) ↔ Capítulos (N) [Many2many]

REFERENCIAS PRINCIPALES:
- models/capitulo_seccion.py: Modelo de secciones relacionadas
- models/sale_order.py: Integración con presupuestos
- wizard/capitulo_wizard.py: Asistente de gestión
- controllers/main.py: Endpoints web para JavaScript
- static/src/js/capitulos_accordion_widget.js: Widget frontend

MÉTODOS CLAVE:
- _compute_capitulos_dependientes_count(): Calcula dependencias de plantillas
- _onchange_plantilla_id(): Copia estructura desde plantilla
- action_crear_desde_plantilla(): Acción para crear desde plantilla
- unlink(): Eliminación con validaciones de dependencias
- action_eliminar_plantilla_forzado(): Eliminación forzada con desvinculación
- action_mostrar_dependencias(): Visualización de capítulos dependientes
"""

# IMPORTACIONES ESTÁNDAR DE ODOO
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

# CONFIGURACIÓN DE LOGGING
# Logger específico para operaciones de capítulos
_logger = logging.getLogger(__name__)

class CapituloContrato(models.Model):
    """
    MODELO PRINCIPAL: Capítulo de Contrato
    
    Gestiona capítulos técnicos que organizan productos en secciones
    para presupuestos de venta. Incluye sistema de plantillas para
    reutilización y validaciones de integridad.
    
    HERENCIA: models.Model (modelo base de Odoo)
    TABLA: capitulo_contrato
    """
    
    # CONFIGURACIÓN DEL MODELO
    _name = 'capitulo.contrato'
    _description = 'Capítulo de Contrato'

    # ==========================================
    # CAMPOS DE DATOS PRINCIPALES
    # ==========================================
    
    name = fields.Char(
        string='Nombre del Capítulo', 
        required=True,
        help='Nombre identificativo del capítulo técnico'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del capítulo y su propósito'
    )
    
    # RELACIÓN ONE2MANY: Un capítulo tiene múltiples secciones
    # REFERENCIA: models/capitulo_seccion.py → CapituloSeccion
    seccion_ids = fields.One2many(
        'capitulo.seccion', 
        'capitulo_id', 
        string='Secciones',
        help='Secciones que componen este capítulo'
    )
    
    condiciones_legales = fields.Text(
        string='Condiciones Legales',
        help='Condiciones legales específicas del capítulo'
    )
    
    # ==========================================
    # SISTEMA DE PLANTILLAS
    # ==========================================
    
    # RELACIÓN MANY2ONE: Referencia a plantilla base
    # PERMITE: Crear capítulos basados en plantillas existentes
    plantilla_id = fields.Many2one(
        'capitulo.contrato', 
        string='Basado en Plantilla', 
        help='Selecciona un capítulo existente como plantilla'
    )
    
    # CAMPO BOOLEANO: Marca si este capítulo es una plantilla
    # USADO EN: Validaciones y filtros de plantillas
    es_plantilla = fields.Boolean(
        string='Es Plantilla', 
        default=False,
        help='Marca este capítulo como plantilla para ser usado por otros'
    )
    
    # CAMPO COMPUTADO: Cuenta capítulos que usan esta plantilla
    # MÉTODO: _compute_capitulos_dependientes_count()
    capitulos_dependientes_count = fields.Integer(
        string='Capítulos Dependientes', 
        compute='_compute_capitulos_dependientes_count',
        help='Número de capítulos que usan esta plantilla'
    )
    
    # ==========================================
    # MÉTODOS COMPUTADOS
    # ==========================================
    
    @api.depends('es_plantilla')
    def _compute_capitulos_dependientes_count(self):
        """
        MÉTODO COMPUTADO: Calcula dependencias de plantillas
        
        Cuenta cuántos capítulos utilizan este registro como plantilla.
        Solo aplica para registros marcados como plantilla.
        
        DEPENDENCIAS:
        - Campo: es_plantilla
        
        LÓGICA:
        1. Si es_plantilla = True: Busca capítulos con plantilla_id = self.id
        2. Si es_plantilla = False: Retorna 0
        
        REFERENCIAS:
        - Usado en: Vista de plantillas para mostrar uso
        - Llamado por: action_mostrar_dependencias()
        """
        for record in self:
            if record.es_plantilla:
                # BÚSQUEDA: Capítulos que referencian esta plantilla
                record.capitulos_dependientes_count = self.search_count([
                    ('plantilla_id', '=', record.id)
                ])
            else:
                record.capitulos_dependientes_count = 0

    # ==========================================
    # MÉTODOS ONCHANGE (EVENTOS DE CAMBIO)
    # ==========================================

    @api.onchange('plantilla_id')
    def _onchange_plantilla_id(self):
        """
        EVENTO ONCHANGE: Copia estructura desde plantilla
        
        Se ejecuta cuando el usuario selecciona una plantilla.
        Copia automáticamente todas las secciones y productos
        de la plantilla al capítulo actual.
        
        TRIGGER: Cambio en campo plantilla_id
        
        PROCESO:
        1. Validar que existe plantilla_id
        2. Limpiar secciones existentes: [(5, 0, 0)]
        3. Iterar secciones de la plantilla
        4. Para cada sección, copiar líneas de productos
        5. Crear estructura vals para One2many
        6. Asignar secciones copiadas al capítulo actual
        7. Copiar condiciones legales
        
        ESTRUCTURA DE DATOS:
        - secciones_vals: Lista de tuplas (0, 0, {datos})
        - lineas_vals: Lista de tuplas para product_line_ids
        
        REFERENCIAS:
        - models/capitulo_seccion.py: Estructura de secciones
        - Usado en: Formulario de creación de capítulos
        """
        if self.plantilla_id:
            # PASO 1: Limpiar secciones existentes
            # (5, 0, 0) = Comando Odoo para eliminar todos los registros
            self.seccion_ids = [(5, 0, 0)]
            
            # PASO 2: Preparar estructura para copiar secciones
            secciones_vals = []
            
            # PASO 3: Iterar secciones de la plantilla
            for seccion in self.plantilla_id.seccion_ids:
                # PASO 3.1: Copiar líneas de productos de cada sección
                lineas_vals = []
                for linea in seccion.product_line_ids:
                    # (0, 0, {datos}) = Comando Odoo para crear nuevo registro
                    lineas_vals.append((0, 0, {
                        'product_id': linea.product_id.id,
                        'cantidad': linea.cantidad,
                        'precio_unitario': linea.precio_unitario,
                        'sequence': linea.sequence,
                        'descripcion_personalizada': linea.descripcion_personalizada,
                        'es_opcional': linea.es_opcional,
                    }))
                
                # PASO 3.2: Crear estructura de sección con líneas
                secciones_vals.append((0, 0, {
                    'name': seccion.name,
                    'sequence': seccion.sequence,
                    'descripcion': seccion.descripcion,
                    'es_fija': seccion.es_fija,
                    'product_line_ids': lineas_vals,  # Líneas copiadas
                }))
            
            # PASO 4: Asignar secciones copiadas
            self.seccion_ids = secciones_vals
            
            # PASO 5: Copiar condiciones legales
            self.condiciones_legales = self.plantilla_id.condiciones_legales

    # ==========================================
    # ACCIONES DE USUARIO (BOTONES)
    # ==========================================

    def action_crear_desde_plantilla(self):
        """
        ACCIÓN: Crear capítulo desde plantilla
        
        Abre un formulario para crear un nuevo capítulo basado
        en la plantilla actual. Pre-carga la plantilla en el contexto.
        
        REQUISITOS:
        - El registro actual debe ser una plantilla (es_plantilla=True)
        
        RETORNO:
        - Diccionario de acción de ventana de Odoo
        - Abre formulario en modo edición
        - Contexto incluye default_plantilla_id
        
        REFERENCIAS:
        - Usado en: Vista de plantillas (botón "Crear desde Plantilla")
        - Activa: _onchange_plantilla_id() automáticamente
        """
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Capítulo desde Plantilla',
            'res_model': 'capitulo.contrato',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_plantilla_id': self.id,  # Pre-cargar plantilla
                'form_view_initial_mode': 'edit',  # Modo edición
            }
        }
    
    # ==========================================
    # MÉTODOS DE ELIMINACIÓN CON VALIDACIONES
    # ==========================================
    
    def unlink(self):
        """
        MÉTODO SOBRESCRITO: Eliminación con validaciones
        
        Extiende el método unlink() estándar de Odoo para manejar
        eliminación de plantillas con dependencias.
        
        LÓGICA DE VALIDACIÓN:
        1. Para cada registro a eliminar
        2. Si es plantilla (es_plantilla=True)
        3. Buscar capítulos que la usan (plantilla_id=self.id)
        4. Si existen dependencias: Desvincular (plantilla_id=False)
        5. Registrar operación en logs
        6. Continuar con eliminación estándar
        
        VENTAJAS:
        - Evita errores de integridad referencial
        - Mantiene capítulos existentes funcionales
        - Registra operaciones para auditoría
        
        REFERENCIAS:
        - Llamado por: action_eliminar_plantilla_forzado()
        - Logs en: _logger.info()
        """
        for record in self:
            if record.es_plantilla:
                # BÚSQUEDA: Capítulos que usan esta plantilla
                capitulos_usando_plantilla = self.search([
                    ('plantilla_id', '=', record.id)
                ])
                
                if capitulos_usando_plantilla:
                    # DESVINCULACIÓN: Limpiar referencias a la plantilla
                    capitulos_usando_plantilla.write({'plantilla_id': False})
                    
                    # LOGGING: Registrar operación para auditoría
                    _logger.info(
                        f"Plantilla '{record.name}' eliminada. "
                        f"Se han desvinculado {len(capitulos_usando_plantilla)} "
                        f"capítulos que la utilizaban."
                    )
        
        # LLAMADA AL MÉTODO PADRE: Eliminación estándar de Odoo
        return super().unlink()
    
    def action_eliminar_plantilla_forzado(self):
        """
        ACCIÓN: Eliminación forzada de plantilla
        
        Elimina una plantilla desvinculando todos los capítulos
        que la utilizan. Proporciona feedback detallado al usuario.
        
        VALIDACIONES:
        1. Verificar que el registro es una plantilla
        2. Buscar capítulos dependientes
        3. Desvincular dependencias
        4. Eliminar plantilla
        5. Mostrar notificación de resultado
        
        CASOS DE USO:
        - Limpieza de plantillas obsoletas
        - Reorganización de estructura de capítulos
        - Mantenimiento de datos
        
        RETORNO:
        - Notificación de éxito con detalles
        - Lista de capítulos desvinculados
        
        REFERENCIAS:
        - Usa: unlink() sobrescrito
        - Logs en: _logger.info()
        """
        self.ensure_one()  # Validar que es un solo registro
        
        # VALIDACIÓN: Verificar que es una plantilla
        if not self.es_plantilla:
            raise UserError("Este registro no es una plantilla.")
        
        # BÚSQUEDA: Capítulos dependientes
        capitulos_dependientes = self.search([('plantilla_id', '=', self.id)])
        
        if capitulos_dependientes:
            # CASO: Plantilla con dependencias
            
            # PASO 1: Desvincular capítulos dependientes
            capitulos_dependientes.write({'plantilla_id': False})
            
            # PASO 2: Logging de la operación
            _logger.info(
                f"Plantilla '{self.name}' eliminada. "
                f"Capítulos desvinculados: {', '.join(capitulos_dependientes.mapped('name'))}"
            )
            
            # PASO 3: Eliminar la plantilla
            nombre_plantilla = self.name
            self.unlink()
            
            # PASO 4: Notificación detallada al usuario
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Plantilla Eliminada',
                    'message': (
                        f'La plantilla "{nombre_plantilla}" ha sido eliminada. '
                        f'Se han desvinculado {len(capitulos_dependientes)} capítulos '
                        f'que la utilizaban: {", ".join(capitulos_dependientes.mapped("name"))}'
                    ),
                    'type': 'success',
                    'sticky': True,  # Notificación persistente
                }
            }
        
        # CASO: Plantilla sin dependencias
        nombre_plantilla = self.name
        self.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Plantilla Eliminada',
                'message': f'La plantilla "{nombre_plantilla}" ha sido eliminada exitosamente.',
                'type': 'success',
                'sticky': False,  # Notificación temporal
            }
        }
    
    def action_mostrar_dependencias(self):
        """
        ACCIÓN: Mostrar capítulos dependientes
        
        Muestra una vista con todos los capítulos que utilizan
        la plantilla actual. Útil para auditoría y gestión.
        
        VALIDACIONES:
        1. Verificar que es una plantilla
        2. Buscar capítulos dependientes
        3. Si no hay dependencias: Mostrar notificación informativa
        4. Si hay dependencias: Abrir vista filtrada
        
        CASOS DE USO:
        - Auditoría de uso de plantillas
        - Verificación antes de eliminar
        - Gestión de dependencias
        
        RETORNO:
        - Vista de lista/formulario filtrada por dependencias
        - O notificación si no hay dependencias
        
        REFERENCIAS:
        - Usa: _compute_capitulos_dependientes_count()
        - Filtro: domain=[('plantilla_id', '=', self.id)]
        """
        self.ensure_one()
        
        # VALIDACIÓN: Verificar que es una plantilla
        if not self.es_plantilla:
            raise UserError("Este registro no es una plantilla.")
        
        # BÚSQUEDA: Capítulos dependientes
        capitulos_dependientes = self.search([('plantilla_id', '=', self.id)])
        
        if not capitulos_dependientes:
            # CASO: Sin dependencias
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sin Dependencias',
                    'message': (
                        f'La plantilla "{self.name}" no está siendo utilizada '
                        f'por ningún capítulo. Puede eliminarla de forma segura.'
                    ),
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        # CASO: Con dependencias - Mostrar vista filtrada
        return {
            'type': 'ir.actions.act_window',
            'name': f'Capítulos que usan la plantilla: {self.name}',
            'res_model': 'capitulo.contrato',
            'view_mode': 'list,form',
            'domain': [('plantilla_id', '=', self.id)],  # Filtro por plantilla
            'context': {'search_default_plantilla_id': self.id},
        }