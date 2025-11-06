
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
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'clave': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_clave'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class EquipoForm(forms.ModelForm):
    """
    Formulario para crear equipos con autocompletado.
    Los campos tipo, marca y modelo se envían como IDs y se convierten a objetos.
    """
    
    # 🌟 Redefinir campos como CharField para aceptar tanto IDs como texto
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
    
    # 🌟 Métodos clean para convertir IDs a objetos
    def clean_tipo(self):
        """Convierte el ID del tipo en un objeto TipoEquipo."""
        tipo_id = self.cleaned_data.get('tipo')
        if tipo_id:
            try:
                return TipoEquipo.objects.get(pk=tipo_id)
            except TipoEquipo.DoesNotExist:
                raise forms.ValidationError("El tipo de equipo seleccionado no es válido.")
        return None
    
    def clean_marca(self):
        """Convierte el ID de la marca en un objeto Marca."""
        marca_id = self.cleaned_data.get('marca')
        if marca_id:
            try:
                return Marca.objects.get(pk=marca_id)
            except Marca.DoesNotExist:
                raise forms.ValidationError("La marca seleccionada no es válida.")
        return None
    
    def clean_modelo(self):
        """Convierte el ID del modelo en un objeto Modelo."""
        modelo_id = self.cleaned_data.get('modelo')
        if modelo_id:
            try:
                return Modelo.objects.get(pk=modelo_id)
            except Modelo.DoesNotExist:
                raise forms.ValidationError("El modelo seleccionado no es válido.")
        return None


class ReparacionForm(forms.ModelForm):
    """Formulario para crear reparaciones (Orden de Servicio)."""
    class Meta:
        model = Reparacion
        fields = ['tecnico_asignado', 'falla_reportada']
        widgets = {
            'falla_reportada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tecnico_asignado': forms.Select(attrs={'class': 'form-control'}),
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