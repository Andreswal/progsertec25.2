
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
        
class Marca(TimeStampedModel): # Hereda la auditoría
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Marca")

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
    # ModelosCod (ID) es automático
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='modelos')
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Modelo")

    class Meta:
        # Asegura que un modelo solo exista una vez por marca
        unique_together = ('marca', 'nombre') 

    def __str__(self):
        return f"{self.marca.nombre} - {self.nombre}"
        
class Equipo(TimeStampedModel): # Hereda la auditoría
    # EquiposCod (ID) es automático
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='equipos') 
    # VINCULACIÓN: ¡Importante! Usar la clase Modelo ya definida arriba
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos_modelo') 
    
    # Datos propios del equipo (con tus ajustes)
    numero_serie = models.CharField(max_length=100, unique=True, verbose_name="Número de Serie")
    # Nuevo campo para celulares
    imei = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="IMEI")
    # Nuevo campo para garantía
    fecha_compra = models.DateField(null=True, blank=True, verbose_name="Fecha de Compra") 

    def __str__(self):
        return f"{self.numero_serie} ({self.cliente.nombre})"

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