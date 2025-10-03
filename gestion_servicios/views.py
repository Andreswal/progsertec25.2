from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone

# Importaciones específicas de la app
from .models import Cliente, Equipo, Reparacion
from .forms import ClienteForm, EquipoForm, ReparacionForm, ReparacionUpdateForm
from django.http import JsonResponse 
from django.views.decorators.http import require_GET


class ReparacionListView(ListView):
    model = Reparacion
    template_name = 'gestion_servicios/lista_servicios.html'
    context_object_name = 'reparaciones'

    def get_queryset(self):
        # 1. Obtener el filtro de la URL (ej: ?estado=TERMINADA)
        filtro_estado = self.request.GET.get('estado', 'TALLER') 

        queryset = Reparacion.objects.all()

        # 2. Aplicar el filtro según el parámetro
        if filtro_estado == 'TERMINADAS':
            queryset = queryset.filter(estado__in=['TERMINADA', 'NO_REPARABLE'])
        elif filtro_estado == 'ENTREGADAS':
            queryset = queryset.filter(estado='ENTREGADA')
        else: # Por defecto: 'TALLER' (ingresado, presupuestado, en reparación)
            queryset = queryset.exclude(estado__in=['TERMINADA', 'NO_REPARABLE', 'ENTREGADA'])

        return queryset.order_by('-fecha_ingreso')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 3. Pasar el filtro actual al template para resaltar el botón correcto
        context['filtro_activo'] = self.request.GET.get('estado', 'TALLER')
        return context


class ReparacionCreateView(View):
    template_name = 'gestion_servicios/crear_servicio.html'

    def get_context_data(self, cliente_form=None, equipo_form=None, reparacion_form=None):
        # Función auxiliar para generar el contexto (formularios)
        return {
            'cliente_form': cliente_form or ClienteForm(),
            'equipo_form': equipo_form or EquipoForm(),
            'reparacion_form': reparacion_form or ReparacionForm(),
        }

    def get(self, request):
        # Muestra los formularios vacíos
        return render(request, self.template_name, self.get_context_data())

    @transaction.atomic # Asegura la integridad de los 3 pasos (Cliente, Equipo, Reparación)
    def post(self, request):
        cliente_form = ClienteForm(request.POST)
        equipo_form = EquipoForm(request.POST)
        reparacion_form = ReparacionForm(request.POST)

        # 1. Búsqueda de Cliente por 'clave' (DNI/RUC)
        cliente_clave = request.POST.get('clave')
        cliente_existente = None
        
        if cliente_clave:
            try:
                # Intenta encontrar un cliente con esa clave
                cliente_existente = Cliente.objects.get(clave=cliente_clave)
            except Cliente.DoesNotExist:
                pass # Si no existe, cliente_existente sigue siendo None

        
        # 2. VALIDACIÓN Y CREACIÓN
        
        # Caso A: Cliente EXISTE. Solo validamos Equipo y Reparación.
        if cliente_existente and equipo_form.is_valid() and reparacion_form.is_valid():
            
            # 2a. Crear el Equipo
            nuevo_equipo = equipo_form.save(commit=False)
            nuevo_equipo.cliente = cliente_existente # Asignamos el cliente encontrado
            nuevo_equipo.save()

            # 2b. Crear la Reparación
            nueva_reparacion = reparacion_form.save(commit=False)
            nueva_reparacion.cliente = cliente_existente
            nueva_reparacion.equipo = nuevo_equipo
            nueva_reparacion.save()

            return redirect('lista_servicios') # Éxito

        # Caso B: Cliente NO EXISTE (o no se encontró la clave). Validamos TODO.
        elif cliente_existente is None and cliente_form.is_valid() and equipo_form.is_valid() and reparacion_form.is_valid():
            
            # 2c. Crear el Cliente nuevo (la clave es válida)
            nuevo_cliente = cliente_form.save()

            # 2d. Crear el Equipo
            nuevo_equipo = equipo_form.save(commit=False)
            nuevo_equipo.cliente = nuevo_cliente
            nuevo_equipo.save()

            # 2e. Crear la Reparación
            nueva_reparacion = reparacion_form.save(commit=False)
            nueva_reparacion.cliente = nuevo_cliente
            nueva_reparacion.equipo = nuevo_equipo
            nueva_reparacion.save()

            return redirect('lista_servicios') # Éxito
        
        # Caso C: FALLA EN LA VALIDACIÓN (Error en algún campo)
        else:
            # Si hay error, se re-renderiza con los datos POST y errores.
            # Aquí podrías agregar lógica para precargar los datos del cliente
            # si el único error es que el equipo/reparacion falló.
            return render(request, self.template_name, self.get_context_data(cliente_form, equipo_form, reparacion_form))



class ReparacionUpdateView(UpdateView):
    model = Reparacion
    form_class = ReparacionUpdateForm
    template_name = 'gestion_servicios/modificar_servicio.html'
    # Redirige a la lista principal después de guardar
    success_url = reverse_lazy('lista_servicios') 
    
    # 💡 Lógica para manejar la asignación automática y el cambio de estado
    def form_valid(self, form):
        reparacion = form.instance
        
        # 1. Asignación del Técnico (Si no estaba asignado y el usuario está logueado como Técnico)
        # Esto asume que tienes un mecanismo para mapear el 'request.user' a un 'Tecnico'
        if not reparacion.tecnico_asignado and self.request.user.is_authenticated:
            # Lógica: Asignar el técnico si es la primera vez que se modifica
            # Ejemplo: reparacion.tecnico_asignado = Tecnico.objects.get(user=self.request.user)
            pass

        # 2. Lógica del cambio de Estado (Ejemplo: Al pasar a TERMINADA)
        # Esto evita que un estado se cambie sin cumplir condiciones
        nuevo_estado = form.cleaned_data.get('estado')
        if nuevo_estado == 'TERMINADA' and not reparacion.informe_tecnico:
            # Si el técnico intenta terminar sin informe, podrías forzar un error
            form.add_error('informe_tecnico', 'Debe completar el informe para terminar la reparación.')
            return self.form_invalid(form)

        # 3. Guardar los cambios
        return super().form_valid(form)
    
    


@require_POST
def cerrar_servicio_view(request, pk):
    """Procesa el cierre (entrega) de la Orden de Servicio."""
    reparacion = get_object_or_404(Reparacion, pk=pk)

    # 1. Validación de Pre-cierre (Lógica de Negocio)
    # Ejemplo: No permitir cerrar si el estado es INGRESADO
    if reparacion.estado not in ['TERMINADA', 'NO_REPARABLE']:
        messages.error(request, "No se puede cerrar la orden si no está Terminada o No Reparable.")
        return redirect('modificar_servicio', pk=pk)
        
    # **Aquí iría la lógica de verificación de SALDO PENDIENTE (si tuvieras)**
    # if reparacion.saldo_final > 0:
    #     messages.error(request, "Existe un saldo pendiente. ¡No se puede entregar!")
    #     return redirect('modificar_servicio', pk=pk)

    # 2. Actualización Final de la Orden
    reparacion.estado = 'ENTREGADA'
    reparacion.fecha_entrega = timezone.now() # Registra la hora actual de entrega
    reparacion.save()

    messages.success(request, f"Orden #{pk} cerrada y entregada con éxito.")
    return redirect('lista_servicios') # Vuelve al listado principal


@require_GET
def buscar_cliente_por_clave(request):
    """
    Busca un cliente por su 'clave' (DNI/RUC) y devuelve los datos en JSON.
    """
    # Obtenemos el valor de la clave (DNI/RUC) desde la URL (parámetro 'clave')
    clave_buscada = request.GET.get('clave', None)

    if clave_buscada:
        try:
            # Intentamos encontrar el cliente
            cliente = Cliente.objects.get(clave__iexact=clave_buscada)
            
            # Si el cliente existe, devolvemos sus datos en formato JSON
            datos_cliente = {
                'existe': True,
                'nombre': cliente.nombre,
                'direccion': cliente.direccion if cliente.direccion else '',
                'telefono': cliente.telefono if cliente.telefono else '',
                'celular': cliente.celular if cliente.celular else '',
                'email': cliente.email if cliente.email else '',
                'pk': cliente.pk # Retornamos la clave primaria por si la necesitas
            }
        except Cliente.DoesNotExist:
            # Si el cliente NO existe
            datos_cliente = {'existe': False}
    else:
        # Si no se envió ninguna clave
        datos_cliente = {'existe': False}
        
    return JsonResponse(datos_cliente)