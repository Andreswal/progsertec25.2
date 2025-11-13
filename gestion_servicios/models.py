
from django.db import models

# ======================================================================
# 0. CLASE ABSTRACTA (AUDITORÍA)
# ======================================================================

class TimeStampedModel(models.Model):
    """
    Clase abstracta para añadir automáticamente campos de fecha de creación 
    y modificación a los modelos que hereden de ella.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación") 
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Modificación") 

    class Meta:
        abstract = True
        ordering = ['-created_at'] 


# ======================================================================
# 1. MODELOS DE CATÁLOGO (Tipo, Marca, Modelo)
# ======================================================================

class TipoEquipo(models.Model):
    """Catálogo de tipos de equipos (Notebook, Smartphone, Tablet, etc.)"""
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Tipo de Equipo")
    
    class Meta:
        verbose_name = "Tipo de Equipo"
        verbose_name_plural = "Tipos de Equipo"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    """Catálogo de marcas (Samsung, Apple, HP, etc.)"""
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Marca")

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    """
    Catálogo de modelos asociados a una marca.
    Ejemplo: Galaxy S21 (Samsung), iPhone 13 (Apple), Pavilion (HP)
    """
    modelo = models.CharField(max_length=100, verbose_name="Modelo")
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.CASCADE, 
        related_name='modelos',
        verbose_name="Marca"
    )

    class Meta:
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"
        unique_together = [['modelo', 'marca']]  # Un modelo único por marca
        ordering = ['marca', 'modelo']

    def __str__(self):
        return f"{self.modelo} ({self.marca.nombre})"


# ======================================================================
# 2. ENTIDADES BASE (Cliente, Técnico, Equipo, Repuesto)
# ======================================================================

class Cliente(TimeStampedModel):
    """Datos del cliente que trae el equipo"""
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    clave = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="DNI/Identificación"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nombre


class Tecnico(TimeStampedModel):
    """Técnicos que realizan las reparaciones"""
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo del Técnico")
    # Sugerencia: user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"

    def __str__(self):
        return self.nombre


class Equipo(TimeStampedModel):
    """
    Representa un equipo físico traído para reparación.
    El campo serie_imei es ÚNICO y es la clave para identificar el equipo.
    """
    # 🔑 CLAVE ÚNICA DEL EQUIPO
    serie_imei = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Nro. Serie / IMEI",
        help_text="Clave única para identificar el equipo (IMEI, S/N, etc.)"
    )
    
    # 📋 CATÁLOGO (OPCIONALES)
    tipo = models.ForeignKey(
        TipoEquipo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Tipo de Equipo"
    )
    marca = models.ForeignKey(
        Marca, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Marca"
    )
    modelo = models.ForeignKey(
        Modelo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Modelo"
    )
    
    # 📝 INFORMACIÓN ADICIONAL
    accesorios = models.TextField(
        blank=True, 
        verbose_name="Accesorios Entregados"
    )
    estado_general = models.TextField(
        blank=True, 
        verbose_name="Estado General y Estético"
    )
    
    # 📅 GARANTÍA
    fecha_compra = models.DateField(
        blank=True, 
        null=True, 
        verbose_name="Fecha de Compra"
    )
    
    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"

    def __str__(self):
        tipo_nombre = self.tipo.nombre if self.tipo else "Equipo"
        marca_nombre = self.marca.nombre if self.marca else ""
        modelo_nombre = self.modelo.modelo if self.modelo else ""
        return f"{tipo_nombre} {marca_nombre} {modelo_nombre} (SN: {self.serie_imei})".strip()

    @property
    def en_garantia(self):
        """Verifica si el equipo está en garantía (1 año desde la compra)"""
        if self.fecha_compra:
            from datetime import date, timedelta
            return self.fecha_compra + timedelta(days=365) >= date.today()
        return False


class Repuesto(TimeStampedModel):
    """Repuestos utilizados en las reparaciones"""
    descripcion = models.CharField(max_length=255)
    codigo = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Código Interno", 
        blank=True, 
        null=True
    )
    stock_actual = models.IntegerField(default=0)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2) 

    class Meta:
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"

    def __str__(self):
        return self.descripcion


# ======================================================================
# 3. TRANSACCIONES (Reparacion y Detalle)
# ======================================================================

class Reparacion(TimeStampedModel):
    """Orden de servicio de reparación"""
    ESTADO_CHOICES = [
        ('INGRESADO', 'Ingresado (Pendiente de Asignar)'),
        ('PRESUPUESTADO', 'Presupuesto Enviado'),
        ('EN_ESPERA_REP', 'En Espera de Repuestos'),
        ('EN_REPARACION', 'En Reparación'),
        ('TERMINADA', 'Reparación Terminada (Listo para Entregar)'),
        ('NO_REPARABLE', 'No Reparable'),
        ('ENTREGADA', 'Entregado al Cliente'),
    ]

    # RELACIONES
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='reparaciones_cliente'
    )
    equipo = models.ForeignKey(
        Equipo, 
        on_delete=models.CASCADE, 
        related_name='reparaciones_equipo'
    )
    tecnico_asignado = models.ForeignKey(
        Tecnico, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='servicios_asignados'
    )

    # FECHAS Y ESTADO
    fecha_ingreso = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de Ingreso"
    )
    fecha_entrega = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Fecha de Entrega"
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='INGRESADO', 
        verbose_name="Estado Actual"
    )
    
    # DIAGNÓSTICO Y PRESUPUESTO
    falla_reportada = models.TextField(
        verbose_name="Falla Reportada por el Cliente"
    )
    informe_tecnico = models.TextField(
        blank=True, 
        verbose_name="Diagnóstico e Informe Técnico"
    )
    mano_de_obra = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Costo de Mano de Obra"
    )
    saldo_final = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Saldo a Cobrar"
    )

    class Meta:
        verbose_name = "Orden de Servicio"
        verbose_name_plural = "Órdenes de Servicio"
        ordering = ['-fecha_ingreso'] 

    def __str__(self):
        return f"Orden #{self.pk} - {self.equipo.serie_imei} ({self.estado})"


class DetalleRepuestoReparacion(models.Model):
    """Relación entre reparaciones y repuestos utilizados"""
    reparacion = models.ForeignKey(
        Reparacion, 
        on_delete=models.CASCADE, 
        related_name='detalles_repuestos'
    )
    repuesto = models.ForeignKey(
        Repuesto, 
        on_delete=models.CASCADE, 
        related_name='usos_en_reparaciones'
    )
    cantidad = models.PositiveIntegerField(
        default=1, 
        verbose_name="Cantidad Utilizada"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Precio de Venta Unitario"
    )
    
    class Meta:
        unique_together = ('reparacion', 'repuesto')
        verbose_name = "Repuesto en Reparación"
        verbose_name_plural = "Repuestos en Reparaciones"

    def __str__(self):
        return f"{self.cantidad} x {self.repuesto.descripcion} en Orden #{self.reparacion.id}"