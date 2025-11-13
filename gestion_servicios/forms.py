# gestion_servicios/forms.py

from django import forms
from .models import Cliente, Equipo, Reparacion, TipoEquipo, Marca, Modelo

# ======================================================================
# 1. FORMULARIOS DE CREACIÓN (RECEPCIÓN)
# ======================================================================

class ClienteForm(forms.ModelForm):
    """Formulario para crear/editar clientes."""

    class Meta:
        model = Cliente
        fields = ['clave', 'nombre', 'direccion', 'telefono', 'celular', 'email']
        widgets = {
            'clave': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_clave'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_clave(self):
        clave = self.cleaned_data.get('clave')
        if not clave:
            raise forms.ValidationError("Este campo es obligatorio.")

        # Si estamos editando un cliente existente, no validar unicidad
        if self.instance and self.instance.pk:
            return clave

        # Validar que no exista otro cliente con la misma clave
        if Cliente.objects.filter(clave=clave).exists():
            raise forms.ValidationError("Ya existe un cliente con esta clave.")
        
        return clave

class EquipoForm(forms.ModelForm):
    """
    Formulario para crear equipos con autocompletado.
    Los campos tipo, marca y modelo aceptan IDs (si se seleccionan de la lista)
    o texto (si el usuario escribe directamente), y se crean automáticamente.
    """
    
    # 🌟 Redefinir campos como CharField con HiddenInput
    tipo = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_tipo'})
    )
    marca = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_marca'})
    )
    modelo = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_modelo'})
    )
    
    class Meta:
        model = Equipo
        fields = ['serie_imei', 'tipo', 'marca', 'modelo', 'accesorios', 'estado_general', 'fecha_compra']
        widgets = {
            'serie_imei': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_serie_imei'}),
            'accesorios': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estado_general': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    # ======================================================================
    # MÉTODOS CLEAN - CONVERSIÓN INTELIGENTE DE IDs/TEXTO A OBJETOS
    # ======================================================================
    
    def clean_tipo(self):
        """
        Convierte el ID o crea un nuevo TipoEquipo si es texto.
        - Si recibe un número: busca el registro existente
        - Si recibe texto: crea o busca el tipo (case-insensitive)
        """
        tipo_valor = self.cleaned_data.get('tipo')
        
        # Si está vacío, retornar None
        if not tipo_valor or tipo_valor == '':
            return None
        
        # Convertir a string y limpiar espacios
        tipo_valor = str(tipo_valor).strip()
        
        # CASO 1: Es un número (ID) → Buscar registro existente
        if tipo_valor.isdigit():
            try:
                return TipoEquipo.objects.get(pk=int(tipo_valor))
            except TipoEquipo.DoesNotExist:
                raise forms.ValidationError("El tipo de equipo seleccionado no es válido.")
        
        # CASO 2: Es texto → Buscar o crear (case-insensitive)
        try:
            # Intentar encontrar existente
            tipo_obj = TipoEquipo.objects.get(nombre__iexact=tipo_valor)
            print(f"✅ Tipo de equipo encontrado: {tipo_obj.nombre}")
            return tipo_obj
        except TipoEquipo.DoesNotExist:
            # Si no existe, crear nuevo
            tipo_obj = TipoEquipo.objects.create(nombre=tipo_valor.upper())
            print(f"✅ Tipo de equipo creado automáticamente: {tipo_obj.nombre}")
            return tipo_obj
    
    def clean_marca(self):
        """
        Convierte el ID o crea una nueva Marca si es texto.
        - Si recibe un número: busca el registro existente
        - Si recibe texto: crea o busca la marca (case-insensitive)
        """
        marca_valor = self.cleaned_data.get('marca')
        
        # Si está vacío, retornar None
        if not marca_valor or marca_valor == '':
            return None
        
        # Convertir a string y limpiar espacios
        marca_valor = str(marca_valor).strip()
        
        # CASO 1: Es un número (ID) → Buscar registro existente
        if marca_valor.isdigit():
            try:
                return Marca.objects.get(pk=int(marca_valor))
            except Marca.DoesNotExist:
                raise forms.ValidationError("La marca seleccionada no es válida.")
        
        # CASO 2: Es texto → Buscar o crear (case-insensitive)
        try:
            # Intentar encontrar existente
            marca_obj = Marca.objects.get(nombre__iexact=marca_valor)
            print(f"✅ Marca encontrada: {marca_obj.nombre}")
            return marca_obj
        except Marca.DoesNotExist:
            # Si no existe, crear nueva
            marca_obj = Marca.objects.create(nombre=marca_valor.upper())
            print(f"✅ Marca creada automáticamente: {marca_obj.nombre}")
            return marca_obj
    
    def clean_modelo(self):
        """
        Convierte el ID o crea un nuevo Modelo si es texto.
        - Si recibe un número: busca el registro existente
        - Si recibe texto: crea o busca el modelo asociado a la marca
        """
        modelo_valor = self.cleaned_data.get('modelo')
        
        # Si está vacío, retornar None
        if not modelo_valor or modelo_valor == '':
            return None
        
        # Convertir a string y limpiar espacios
        modelo_valor = str(modelo_valor).strip()
        
        # CASO 1: Es un número (ID) → Buscar registro existente
        if modelo_valor.isdigit():
            try:
                return Modelo.objects.get(pk=int(modelo_valor))
            except Modelo.DoesNotExist:
                raise forms.ValidationError("El modelo seleccionado no es válido.")
        
        # CASO 2: Es texto → Verificar que exista una marca primero
        marca = self.cleaned_data.get('marca')
        if not marca:
            raise forms.ValidationError("Debe seleccionar o escribir una marca antes de especificar el modelo.")
        
        # Intentar encontrar el modelo existente para esta marca (case-insensitive)
        try:
            modelo_obj = Modelo.objects.get(
                modelo__iexact=modelo_valor,
                marca=marca
            )
            print(f"✅ Modelo encontrado: {modelo_obj.modelo} (Marca: {marca.nombre})")
            return modelo_obj
        except Modelo.DoesNotExist:
            # Si no existe, crearlo asociado a la marca
            modelo_obj = Modelo.objects.create(
                modelo=modelo_valor.upper(),
                marca=marca
            )
            print(f"✅ Modelo creado automáticamente: {modelo_obj.modelo} (Marca: {marca.nombre})")
            return modelo_obj


class ReparacionForm(forms.ModelForm):
    """Formulario para crear reparaciones (Orden de Servicio)."""
    class Meta:
        model = Reparacion
        fields = ['tecnico_asignado', 'falla_reportada']
        widgets = {
            'falla_reportada': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ej: El equipo no enciende, la pantalla está rota, no carga la batería...'
            }),
            'tecnico_asignado': forms.Select(attrs={
                'class': 'form-control',
                'required': False
            }),
        }


# ======================================================================
# 2. FORMULARIOS DE MODIFICACIÓN (TALLER/SEGUIMIENTO)
# ======================================================================

class ReparacionUpdateForm(forms.ModelForm):
    """Formulario para actualizar el estado de la reparación."""
    class Meta:
        model = Reparacion
        fields = [
            'estado',
            'tecnico_asignado',
            'informe_tecnico',
            'mano_de_obra',
            'saldo_final'
        ]
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'tecnico_asignado': forms.Select(attrs={'class': 'form-control'}),
            'informe_tecnico': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'mano_de_obra': forms.NumberInput(attrs={'class': 'form-control'}),
            'saldo_final': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ======================================================================
# 3. FORMULARIOS PARA MODALES (CREACIÓN RÁPIDA)
# ======================================================================

class TipoEquipoForm(forms.ModelForm):
    """Formulario simple para crear TipoEquipo desde el modal."""
    class Meta:
        model = TipoEquipo
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Notebook, Smartphone, Tablet...'
            })
        }


class MarcaForm(forms.ModelForm):
    """Formulario simple para crear Marca desde el modal."""
    class Meta:
        model = Marca
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Samsung, Apple, HP...'
            })
        }


class ModeloForm(forms.ModelForm):
    """Formulario simple para crear Modelo desde el modal."""
    class Meta:
        model = Modelo
        fields = ['modelo']
        widgets = {
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Galaxy S21, iPhone 13, Pavilion...'
            })
        }