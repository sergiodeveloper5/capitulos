# -*- coding: utf-8 -*-
"""
EXTENSIÓN DEL MODELO PRODUCT.TEMPLATE PARA CAPÍTULOS TÉCNICOS
============================================================

Este archivo extiende el modelo estándar de productos de Odoo para integrar
la funcionalidad de capítulos técnicos y clasificación por tipos de sección.

FUNCIONALIDAD PRINCIPAL:
- Asociación de productos con capítulos específicos
- Clasificación de productos por tipo de sección técnica
- Métodos de búsqueda especializada para el wizard de capítulos
- Integración con el sistema de presupuestos estructurados

CAMPOS AÑADIDOS:
- capitulo_id: Relación Many2one con capítulos técnicos
- tipo_seccion: Clasificación del producto por tipo de servicio

TIPOS DE SECCIÓN SOPORTADOS:
- alquiler: Productos de alquiler de equipos
- montaje: Servicios de montaje e instalación
- desmontaje: Servicios de desmontaje y retirada
- portes: Servicios de transporte y logística
- otros: Servicios adicionales no clasificados

MÉTODOS PRINCIPALES:
- _search_by_capitulo_seccion(): Búsqueda filtrada por capítulo y tipo

INTEGRACIÓN:
- wizard/capitulo_wizard.py: Utiliza la búsqueda especializada
- models/capitulo.py: Relación con capítulos técnicos
- views/product_views.xml: Campos adicionales en formularios

REFERENCIAS:
- models/capitulo.py: Modelo CapituloContrato
- wizard/capitulo_wizard.py: CapituloWizard
- views/product_views.xml: Vistas extendidas de productos
"""

from odoo import models, fields, api

class ProductTemplate(models.Model):
    """
    Extensión del modelo de plantilla de productos para soporte de capítulos técnicos.
    
    Añade funcionalidad para asociar productos con capítulos específicos y
    clasificarlos por tipo de sección técnica para facilitar su organización
    en presupuestos estructurados.
    
    HERENCIA: product.template (modelo estándar de Odoo)
    TABLA: product_template (tabla existente con campos adicionales)
    """
    _inherit = 'product.template'
    
    # CAMPO DE RELACIÓN CON CAPÍTULOS
    # Permite asociar productos con capítulos técnicos específicos
    capitulo_id = fields.Many2one(
        'capitulo.contrato',                    # Modelo relacionado
        string='Capítulo',                      # Etiqueta en interfaz
        help='Capítulo técnico al que pertenece este producto. '
             'Facilita la organización y búsqueda de productos '
             'específicos para cada tipo de servicio.'
    )
    
    # CAMPO DE CLASIFICACIÓN POR TIPO DE SECCIÓN
    # Categoriza productos según el tipo de servicio técnico
    tipo_seccion = fields.Selection([
        ('alquiler', 'Alquiler'),               # Equipos en alquiler
        ('montaje', 'Montaje'),                 # Servicios de instalación
        ('desmontaje', 'Desmontaje'),           # Servicios de retirada
        ('portes', 'Portes'),                   # Transporte y logística
        ('otros', 'Otros')                      # Servicios adicionales
    ], 
        string='Tipo de Sección',               # Etiqueta en interfaz
        help='Clasificación del producto según el tipo de servicio técnico. '
             'Utilizado para organizar productos en secciones específicas '
             'dentro de los capítulos de presupuestos.'
    )
    
    @api.model
    def _search_by_capitulo_seccion(self, capitulo_id=None, tipo_seccion=None):
        """
        Búsqueda especializada de productos por capítulo y tipo de sección.
        
        Método utilizado principalmente por el wizard de capítulos para
        filtrar productos relevantes según el contexto de creación.
        
        PARÁMETROS:
        -----------
        capitulo_id (int, opcional): ID del capítulo para filtrar productos
        tipo_seccion (str, opcional): Tipo de sección para filtrar productos
        
        RETORNA:
        --------
        recordset: Conjunto de productos que coinciden con los criterios
        
        LÓGICA:
        -------
        1. Construye dominio de búsqueda dinámicamente
        2. Aplica filtros según parámetros proporcionados
        3. Ejecuta búsqueda en base de datos
        4. Retorna recordset filtrado
        
        CASOS DE USO:
        ------------
        - Wizard de capítulos: Mostrar productos relevantes por sección
        - Autocompletado: Filtrar productos por contexto
        - Reportes: Análisis de productos por categoría
        
        REFERENCIAS:
        -----------
        - wizard/capitulo_wizard.py: Utiliza este método para filtrado
        - controllers/main.py: Puede usar para búsquedas especializadas
        """
        # CONSTRUCCIÓN DINÁMICA DEL DOMINIO DE BÚSQUEDA
        domain = []
        
        # Filtro por capítulo (si se especifica)
        if capitulo_id:
            domain.append(('capitulo_id', '=', capitulo_id))
        
        # Filtro por tipo de sección (si se especifica)
        if tipo_seccion:
            domain.append(('tipo_seccion', '=', tipo_seccion))
        
        # EJECUCIÓN DE BÚSQUEDA Y RETORNO
        return self.search(domain)