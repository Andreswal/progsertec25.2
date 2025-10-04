
from django.db import models

# ----------------------------------------------------------------------
# 0. CLASE ABSTRACTA (AUDITORÍA)
# ----------------------------------------------------------------------

class TimeStampedModel(models.Model):
    """
    Clase abstracta para añadir automáticamente campos de fecha de creación 
    y modificación a los modelos que hereden de ella.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación") 
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Modificación") 

    class Meta:
        abstract = True
        # Se puede quitar la ordenación si la hereda una clase que necesita otra (como Reparacion)
        ordering = ['-created_at'] 


# ----------------------------------------------------------------------
# 1. ENTIDADES BASE (Cliente, Técnico, Marca, Repuesto)
# ----------------------------------------------------------------------

# --- Modelos de Catálogo ---
class TipoEquipo(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Tipo de Equipo")
    
    class Meta:
        verbose_name = "Tipo de Equipo"
        verbose_name_plural = "Tipos de Equipo"

    def __str__(self):
        return self.nombre

class Marca(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Marca")

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"

    def __str__(self):
        return self.nombre   
    
class Equipo(TimeStampedModel):
    # Clave de Filtrado Unificada
    serie_imei = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Nro. Serie / IMEI",
        help_text="Clave única para identificar el equipo."
    )
    
    # Claves Foráneas de Catálogo (Asegúrate de que TipoEquipo y Marca están DEFINIDAS ARRIBA)
    tipo = models.ForeignKey('TipoEquipo', on_delete=models.SET_NULL, null=True, verbose_name="Tipo de Equipo")
    marca = models.ForeignKey('Marca', on_delete=models.SET_NULL, null=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, verbose_name="Modelo", help_text="Ej. iPhone 12, XPS 13")
    
    # Campos Opcionales
    accesorios = models.TextField(blank=True, verbose_name="Accesorios Entregados")
    estado_general = models.TextField(blank=True, verbose_name="Estado General y Estético")
    
    # Campo de Garantía
    fecha_compra = models.DateField(blank=True, null=True, verbose_name="Fecha de Compra")
    
    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"

    def __str__(self):
        # Muestra el tipo y la marca para una mejor identificación
        return f"{self.tipo} {self.marca} - {self.modelo} (SN/IMEI: {self.serie_imei})"

    @property
    def en_garantia(self):
        if self.fecha_compra:
            from datetime import date, timedelta
            return self.fecha_compra + timedelta(days=365) >= date.today()
        return False

    

class Cliente(TimeStampedModel): # Hereda la auditoría
    # ClientesCod (ID) es automático
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    # ¡IMPORTANTE! clave debe ser UNIQUE para usarla en la búsqueda
    clave = models.CharField(max_length=50, unique=True, verbose_name="DNI/Identificación") 

    def __str__(self):
        return self.nombre

class Tecnico(TimeStampedModel): # Hereda la auditoría
    # TecnicosCod (ID) es automático
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo del Técnico")
    # Sugerencia: Añadir campo user = models.OneToOneField(User, on_delete=models.CASCADE) para la seguridad

    def __str__(self):
        return self.nombre
        
        
class Repuesto(TimeStampedModel): # Hereda la auditoría
    # RepuestosCc (ID) es automático
    descripcion = models.CharField(max_length=255)
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código Interno", blank=True, null=True)
    stock_actual = models.IntegerField(default=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2) 
    
    # Campo pendiente: proveedor = models.ForeignKey('Proveedor', ...)

    def __str__(self):
        return self.descripcion

# ----------------------------------------------------------------------
# 2. ENTIDADES INTERMEDIAS (Modelo, Equipo)
# ----------------------------------------------------------------------

class Modelo(TimeStampedModel): # Hereda la auditoría
   # Clave de Filtrado Unificada
    serie_imei = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Nro. Serie / IMEI",
        help_text="Clave única para identificar el equipo."
    )
    
    # Nuevas Claves Foráneas de Catálogo
    tipo = models.ForeignKey(TipoEquipo, on_delete=models.SET_NULL, null=True, verbose_name="Tipo de Equipo")
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, verbose_name="Marca")
    modelo = models.CharField(max_length=100, verbose_name="Modelo", help_text="Ej. iPhone 12, XPS 13") # Mantenemos modelo como texto libre para descripciones específicas
    
    # Nuevos campos de Descripción y Estado (no obligatorios)
    accesorios = models.TextField(blank=True, verbose_name="Accesorios Entregados")
    estado_general = models.TextField(blank=True, verbose_name="Estado General y Estético")
    
    # Campo de Garantía
    fecha_compra = models.DateField(blank=True, null=True, verbose_name="Fecha de Compra")
    
    # El campo imei anterior ahora está unificado en serie_imei, lo quitamos si existía.
    
    def __str__(self):
        # Muestra el tipo y la marca para una mejor identificación
        return f"{self.tipo} {self.marca} - {self.modelo} (SN/IMEI: {self.serie_imei})"

    # Nuevo método para comprobar si está en garantía (ejemplo de 1 año)
    @property
    def en_garantia(self):
        if self.fecha_compra:
            from datetime import date, timedelta
            return self.fecha_compra + timedelta(days=365) >= date.today()
        return False
    
# ----------------------------------------------------------------------
# 3. TRANSACCIONES (Reparacion y Detalle)
# ----------------------------------------------------------------------

class Reparacion(TimeStampedModel): # Hereda la auditoría
    # ReparacioneCod (ID) es automático
    ESTADO_CHOICES = [
        ('INGRESADO', 'Ingresado (Pendiente de Asignar)'),
        ('PRESUPUESTADO', 'Presupuesto Enviado'),
        ('EN_ESPERA_REP', 'En Espera de Repuestos'),
        ('EN_REPARACION', 'En Reparación'),
        ('TERMINADA', 'Reparación Terminada (Listo para Entregar)'),
        ('NO_REPARABLE', 'No Reparable'),
        ('ENTREGADA', 'Entregado al Cliente'),
    ]

    # --- 1. Relaciones (Foreign Keys) ---
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reparaciones_cliente')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='reparaciones_equipo')
    tecnico_asignado = models.ForeignKey(Tecnico, on_delete=models.SET_NULL, null=True, blank=True, related_name='servicios_asignados')

    # --- 2. Datos de la Orden y Estado ---
    fecha_ingreso = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Ingreso") # Ya existe en TimeStampedModel, pero lo mantenemos si lo necesitas
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Entrega")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='INGRESADO', verbose_name="Estado Actual")
    
    # --- 3. Datos de Diagnóstico y Presupuesto ---
    falla_reportada = models.TextField(verbose_name="Falla Reportada por el Cliente")
    informe_tecnico = models.TextField(blank=True, verbose_name="Diagnóstico e Informe Técnico")
    mano_de_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Costo de Mano de Obra")
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Saldo a Cobrar")

    class Meta:
        verbose_name = "Orden de Servicio"
        verbose_name_plural = "Órdenes de Servicio"
        ordering = ['-fecha_ingreso'] 

    def __str__(self):
        return f"Orden #{self.pk} - {self.equipo.numero_serie} ({self.estado})"
        
        
class DetalleRepuestoReparacion(models.Model):
    # Clave compuesta (no necesita heredar TimeStampedModel necesariamente, es un detalle transaccional)
    reparacion = models.ForeignKey(Reparacion, on_delete=models.CASCADE, related_name='detalles_repuestos')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name='usos_en_reparaciones')

    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad Utilizada")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de Venta Unitario")
    
    class Meta:
        unique_together = ('reparacion', 'repuesto')
        verbose_name = "Repuesto en Reparación"
        verbose_name_plural = "Repuestos en Reparaciones"

    def __str__(self):
        return f"{self.cantidad} x {self.repuesto.descripcion} en Rep. #{self.reparacion.id}"
    



