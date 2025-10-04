
# gestion_servicios/forms.py

from django import forms
from .models import Cliente, Equipo, Reparacion, TipoEquipo, Marca

# ----------------------------------------------------------------------
# 1. Formularios de Creación (Recepción)
# ----------------------------------------------------------------------

# Usado en ReparacionCreateView (Caso B: Cliente Nuevo)
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['clave', 'nombre', 'direccion', 'telefono', 'celular', 'email']
        # Puedes añadir widgets para mejorar la apariencia (Bootstrap, etc.)
        widgets = {
            
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'clave': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_clave'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'celular': forms.TextInput(attrs={'class': 'form-control'}), # Nuevo
            'email': forms.EmailInput(attrs={'class': 'form-control'}), # Nuevo
        }

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ['serie_imei', 'tipo', 'marca', 'modelo', 'accesorios', 'estado_general', 'fecha_compra']
        widgets = {
            'serie_imei': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_serie_imei'}),
            'tipo': forms.Select(attrs={'class': 'form-control', 'id': 'id_tipo'}), # ID importante para JS
            'marca': forms.Select(attrs={'class': 'form-control', 'id': 'id_marca'}), # ID importante para JS
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'accesorios': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estado_general': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), 
        }
        

# Usado en ReparacionCreateView
class ReparacionForm(forms.ModelForm):
    # NOTA: Cliente y Equipo NO se incluyen, se asignan en la vista
    # NOTA: Informe Técnico y Mano de Obra no se muestran en el ingreso inicial
    class Meta:
        model = Reparacion
        fields = ['tecnico_asignado', 'falla_reportada']
        widgets = {
            'falla_reportada': forms.Textarea(attrs={'rows': 3}),
        }

# ----------------------------------------------------------------------
# 2. Formularios de Modificación (Taller/Seguimiento)
# ----------------------------------------------------------------------

# Usado en ReparacionUpdateView
class ReparacionUpdateForm(forms.ModelForm):
    class Meta:
        model = Reparacion
        # Campos que el técnico puede modificar durante el proceso
        fields = [
            'estado', 
            'tecnico_asignado', 
            'informe_tecnico', 
            'mano_de_obra', 
            'saldo_final'
            # Los campos del cliente y equipo se muestran pero no se editan
        ]
        widgets = {
            'informe_tecnico': forms.Textarea(attrs={'rows': 5}),
        }
        

class TipoEquipoForm(forms.ModelForm):
    """Formulario simple para crear TipoEquipo desde el modal."""
    class Meta:
        model = TipoEquipo
        fields = ['nombre']
        widgets = {
             'nombre': forms.TextInput(attrs={'class': 'form-control'})
        }