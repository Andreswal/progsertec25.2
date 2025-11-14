from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, UpdateView
from django.views import View
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse 


# Importaciones específicas de la app
from .models import Cliente, Equipo, Reparacion
from .forms import ClienteForm, EquipoForm, ReparacionForm, ReparacionUpdateForm
from django.views.decorators.http import require_GET
from .models import TipoEquipo # Asegúrate de importar tu modelo TipoEquipo
from .forms import TipoEquipoForm # Asegúrate de importar el formulario
from .models import Marca
from .forms import MarcaForm 
from .models import Modelo
from .forms import ModeloForm
from .models import Tecnico
from .forms import TecnicoForm


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
        return {
            'cliente_form': cliente_form or ClienteForm(),
            'equipo_form': equipo_form or EquipoForm(),
            'reparacion_form': reparacion_form or ReparacionForm(),
        }

    def get(self, request):
        return render(request, self.template_name, self.get_context_data())

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # DEBUG POST
        print("=" * 60)
        print("📥 Datos POST recibidos:")
        for k, v in request.POST.items():
            if k != 'csrfmiddlewaretoken':
                print(f"  {k}: {v}")
        print("=" * 60)

        # 0) Detectar existencia previa para bindear formularios con instance
        clave_val = request.POST.get('clave', '').strip()
        serie_val = request.POST.get('serie_imei', '').strip()

        cliente_exist = Cliente.objects.filter(clave=clave_val).first() if clave_val else None
        equipo_exist = Equipo.objects.filter(serie_imei=serie_val).first() if serie_val else None

        # 1) Instanciar formularios con instance si corresponde (evita errores de unique)
        cliente_form = ClienteForm(request.POST, instance=cliente_exist) if cliente_exist else ClienteForm(request.POST)
        equipo_form = EquipoForm(request.POST, instance=equipo_exist) if equipo_exist else EquipoForm(request.POST)
        reparacion_form = ReparacionForm(request.POST)

        # 2) Validación
        if cliente_form.is_valid() and equipo_form.is_valid() and reparacion_form.is_valid():
            # 3) Guardar/actualizar cliente
            cliente = cliente_form.save()  # si había instance, actualiza; si no, crea
            print(f"✅ Cliente {'actualizado' if cliente_exist else 'nuevo creado'}: {cliente.nombre}")

            # 4) Guardar/recuperar equipo con get_or_create (por seguridad adicional)
            serie_imei = equipo_form.cleaned_data.get('serie_imei')
            equipo, equipo_created = Equipo.objects.get_or_create(
                serie_imei=serie_imei,
                defaults={
                    'tipo': equipo_form.cleaned_data.get('tipo'),
                    'marca': equipo_form.cleaned_data.get('marca'),
                    'modelo': equipo_form.cleaned_data.get('modelo'),
                    'accesorios': equipo_form.cleaned_data.get('accesorios'),
                    'estado_general': equipo_form.cleaned_data.get('estado_general'),
                    'fecha_compra': equipo_form.cleaned_data.get('fecha_compra'),
                }
            )
            if equipo_created:
                print(f"✅ Equipo nuevo creado: {equipo.serie_imei}")
            else:
                print(f"✅ Equipo existente encontrado: {equipo.serie_imei}")
                # Opcional: refrescar datos con lo ingresado
                equipo.tipo = equipo_form.cleaned_data.get('tipo') or equipo.tipo
                equipo.marca = equipo_form.cleaned_data.get('marca') or equipo.marca
                equipo.modelo = equipo_form.cleaned_data.get('modelo') or equipo.modelo
                equipo.accesorios = equipo_form.cleaned_data.get('accesorios') or equipo.accesorios
                equipo.estado_general = equipo_form.cleaned_data.get('estado_general') or equipo.estado_general
                equipo.fecha_compra = equipo_form.cleaned_data.get('fecha_compra') or equipo.fecha_compra
                equipo.save()

            # 5) Crear la reparación
            reparacion = reparacion_form.save(commit=False)
            reparacion.cliente = cliente
            reparacion.equipo = equipo
            reparacion.save()

            messages.success(request, f"✅ Orden de Servicio #{reparacion.pk} generada con éxito.")
            return redirect('lista_servicios')

        # 6) Si hay errores, mostrarlos
        print("❌ ERRORES DE VALIDACIÓN:")
        if not cliente_form.is_valid():
            print("  Cliente Form Errors:", cliente_form.errors)
        if not equipo_form.is_valid():
            print("  Equipo Form Errors:", equipo_form.errors)
        if not reparacion_form.is_valid():
            print("  Reparación Form Errors:", reparacion_form.errors)
        print("=" * 60)

        context = self.get_context_data(cliente_form, equipo_form, reparacion_form)
        messages.error(request, "❌ Error de validación: Por favor, revise los campos marcados en rojo.")
        return render(request, self.template_name, context)


class ReparacionUpdateView(UpdateView):
    model = Reparacion
    form_class = ReparacionUpdateForm
    template_name = 'gestion_servicios/modificar_servicio.html'
    success_url = reverse_lazy('lista_servicios') 

    # 🌟🌟 INICIO DE LA MODIFICACIÓN 🌟🌟
    # Esta función añade el formulario del modal de Técnico al contexto
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'tecnico_form' not in context:
            # Pasa el TecnicoForm para que el modal '#modalNuevoTecnico' lo pueda usar
            context['tecnico_form'] = TecnicoForm()
        return context
    # 🌟🌟 FIN DE LA MODIFICACIÓN 🌟🌟
    
    # 💡 Tu lógica 'form_valid' existente permanece exactamente igual.
    # El 'clean_tecnico_asignado' de forms.py ya hizo la conversión.
    def form_valid(self, form):
        reparacion = form.instance
        
        # 1. Asignación del Técnico (Si no estaba asignado y el usuario está logueado como Técnico)
        if not reparacion.tecnico_asignado and self.request.user.is_authenticated:
            pass

        # 2. Lógica del cambio de Estado (Ejemplo: Al pasar a TERMINADA)
        nuevo_estado = form.cleaned_data.get('estado')
        if nuevo_estado == 'TERMINADA' and not reparacion.informe_tecnico:
            form.add_error('informe_tecnico', 'Debe completar el informe para terminar la reparación.')
            return self.form_invalid(form)

        # 3. Guardar los cambios
        return super().form_valid(form)
    

def crear_servicio(request):
    """
    Renderiza el formulario principal y pasa las instancias de los formularios 
    secundarios para los modales, asegurando la entrega del contexto.
    """
    
    # Creamos un diccionario de contexto directamente
    contexto_final = {
        # Formularios principales
        'cliente_form': ClienteForm(),
        'equipo_form': EquipoForm(),
        
        # 🌟 FORMULARIOS PARA LOS MODALES (Punto Crítico) 🌟
        'modelo_form': ModeloForm(), 
        'marca_form': MarcaForm(), 
        'tipo_equipo_form': TipoEquipoForm(),
    }
    
    if request.method == 'POST':
        # Aquí iría tu lógica POST (guardado de la Orden de Servicio)
        pass
        
    # La variable context se llama contexto_final, asegurando que no haya conflictos
    return render(request, 'gestion_servicios/crear_servicio.html', contexto_final)

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

# ----------------------------------------------------------------------
# FUNCIÓN 1: GUARDAR TIPO DE EQUIPO (Modal)
# ----------------------------------------------------------------------

@require_POST
def guardar_tipo_equipo(request):
    """Recibe la petición del modal, valida y guarda el nuevo tipo."""
    form = TipoEquipoForm(request.POST)
    
    if form.is_valid():
        try:
            tipo = form.save()
            return JsonResponse({
                'success': True,
                'id': tipo.pk,
                'nombre': tipo.nombre
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'nombre': [str(e)]}
            }, status=400)
    else:
        # Extraer errores del formulario
        cleaned_errors = {}
        for field, errors in form.errors.as_data().items():
            cleaned_errors[field] = [str(e.message) for e in errors]
        
        return JsonResponse({
            'success': False,
            'errors': cleaned_errors
        }, status=400)

# ----------------------------------------------------------------------
# FUNCIÓN 4: BUSCAR TIPO DE EQUIPO (Autocompletado)
# ----------------------------------------------------------------------

@require_GET
def buscar_tipo_equipo(request):
    """Busca tipos de equipo que coincidan con la entrada del usuario."""
    term = request.GET.get('term', '')
    
    if term:
        tipos = TipoEquipo.objects.filter(nombre__icontains=term).values('id', 'nombre')[:10]
        resultados = [{'id': tipo['id'], 'text': tipo['nombre']} for tipo in tipos]
        return JsonResponse(resultados, safe=False)
    
    return JsonResponse([], safe=False)

# ----------------------------------------------------------------------
# FUNCIÓN 5: BUSCAR MARCA (Autocompletado)
# ----------------------------------------------------------------------
@require_GET
def buscar_marca(request):
    """Busca marcas que coincidan con la entrada del usuario."""
    term = request.GET.get('term', '')
    
    if term:
        marcas = Marca.objects.filter(nombre__icontains=term).values('id', 'nombre')[:10]
        resultados = [{'id': marca['id'], 'text': marca['nombre']} for marca in marcas]
        return JsonResponse(resultados, safe=False)
    
    return JsonResponse([], safe=False)


# ----------------------------------------------------------------------
# FUNCIÓN 2: GUARDAR MARCA (Modal)
# ----------------------------------------------------------------------

@require_POST
def guardar_marca(request):
    """Recibe la petición del modal de marca por AJAX y guarda la nueva Marca."""
    form = MarcaForm(request.POST)
    
    if form.is_valid():
        try:
            marca = form.save()
            return JsonResponse({
                'success': True,
                'id': marca.pk,
                'nombre': marca.nombre
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': {'nombre': [str(e)]}
            }, status=400)
    else:
        # Extraer errores del formulario
        cleaned_errors = {}
        for field, errors in form.errors.as_data().items():
            cleaned_errors[field] = [str(e.message) for e in errors]
        
        return JsonResponse({
            'success': False,
            'errors': cleaned_errors
        }, status=400)

        
        
# ----------------------------------------------------------------------
# FUNCIÓN 3: GUARDAR MODELO (Modal) - CORREGIDA 🔥
# ----------------------------------------------------------------------

@require_POST
def guardar_modelo(request):
    """
    Crea un nuevo Modelo asociado a una Marca.
    Recibe el ID de la Marca desde el formulario principal.
    """
    
    # 🔍 DEBUG: Ver todos los datos POST recibidos
    print("=" * 60)
    print("📥 Datos POST recibidos en guardar_modelo:")
    for key, value in request.POST.items():
        print(f"  {key}: {value}")
    print("=" * 60)
    
    # 🌟 PASO 1: Obtener el ID de la Marca
    marca_id = request.POST.get('marca')
    
    if not marca_id:
        return JsonResponse({
            'success': False,
            'errors': {
                '__all__': ["⚠️ Error: No se recibió el ID de la Marca. Asegúrate de seleccionar una Marca primero."]
            }
        }, status=400)
    
    # 🌟 PASO 2: Verificar que la Marca existe
    try:
        marca_objeto = Marca.objects.get(pk=marca_id)
        print(f"✅ Marca encontrada: {marca_objeto.nombre} (ID: {marca_id})")
    except Marca.DoesNotExist:
        return JsonResponse({
            'success': False,
            'errors': {
                '__all__': [f"❌ Error: La Marca con ID {marca_id} no existe en la base de datos."]
            }
        }, status=400)
    except ValueError:
        return JsonResponse({
            'success': False,
            'errors': {
                '__all__': [f"❌ Error: El ID de Marca '{marca_id}' no es válido."]
            }
        }, status=400)
    
    # 🌟 PASO 3: Validar el formulario del Modelo
    form = ModeloForm(request.POST)
    
    if form.is_valid():
        try:
            # 🌟 PASO 4: Guardar el Modelo asociándolo a la Marca
            modelo = form.save(commit=False)
            modelo.marca = marca_objeto
            modelo.save()
            
            print(f"✅ Modelo creado exitosamente: {modelo.modelo} (ID: {modelo.pk})")
            
            # 🌟 PASO 5: Devolver respuesta exitosa
            return JsonResponse({
                'success': True,
                'id': modelo.pk,
                'nombre': modelo.modelo,
                'marca_id': marca_objeto.pk,
                'marca_nombre': marca_objeto.nombre
            })
        
        except Exception as e:
            print(f"❌ Error al guardar el modelo: {str(e)}")
            return JsonResponse({
                'success': False,
                'errors': {
                    '__all__': [f"Error al guardar el modelo: {str(e)}"]
                }
            }, status=400)
    
    else:
        # 🌟 PASO 6: Manejar errores de validación del formulario
        print("❌ Errores de validación del formulario:")
        print(form.errors)
        
        cleaned_errors = {}
        for field, errors in form.errors.as_data().items():
            cleaned_errors[field] = [str(e.message) for e in errors]
        
        return JsonResponse({
            'success': False,
            'errors': cleaned_errors
        }, status=400)


# ----------------------------------------------------------------------
# FUNCIÓN 6: BUSCAR MODELO (Autocompletado)
# ----------------------------------------------------------------------
@require_GET
def buscar_modelo(request):
    """Busca modelos por nombre para autocompletado."""
    term = request.GET.get('term', '')

    if term:
        # Opcional: Filtrar por marca si ya está seleccionada
        # marca_id = request.GET.get('marca_id')
        # if marca_id:
        #     modelos = Modelo.objects.filter(nombre__icontains=term, marca_id=marca_id)
        
        modelos = Modelo.objects.filter(modelo__icontains=term).values('id', 'modelo')[:10]
        resultados = [{'id': modelo['id'], 'text': modelo['modelo']} for modelo in modelos]
        return JsonResponse(resultados, safe=False)

    return JsonResponse([], safe=False)



# ----------------------------------------------------------------------
# FUNCIÓN 7: BUSCAR EQUIPO EXISTENTE (Autocompletado)
# ----------------------------------------------------------------------
@require_GET
def buscar_equipo_existente(request):
    """Busca equipos existentes por número de serie/IMEI."""
    term = request.GET.get('term', '')

    if term:
        equipos = Equipo.objects.filter(serie_imei__icontains=term).values('serie_imei')[:10]
        resultados = [{'value': equipo['serie_imei']} for equipo in equipos]
        return JsonResponse(resultados, safe=False)

    return JsonResponse([], safe=False)



@require_GET
def buscar_equipo_por_imei(request):
    imei = request.GET.get('imei')
    try:
        equipo = Equipo.objects.get(serie_imei=imei)
        data = {
            'tipo': equipo.tipo.nombre if equipo.tipo else '',
            'marca': equipo.marca.nombre if equipo.marca else '',
            'modelo': equipo.modelo.modelo if equipo.modelo else '',
            'accesorios': equipo.accesorios,
            'estado_general': equipo.estado_general,
            'fecha_compra': equipo.fecha_compra.strftime('%Y-%m-%d') if equipo.fecha_compra else '',
        }
        return JsonResponse(data)
    except Equipo.DoesNotExist:
        return JsonResponse({'error': 'No encontrado'}, status=404)


# -------------------------------------------------
# VISTAS AJAX PARA TÉCNICOS
# -------------------------------------------------

@require_POST
def guardar_tecnico(request):
    """Guarda un nuevo técnico desde el modal."""
    form = TecnicoForm(request.POST)
    if form.is_valid():
        tecnico = form.save()
        # Devolvemos el nombre en mayúsculas como lo guarda el clean_
        nombre_tecnico = tecnico.nombre 
        return JsonResponse({'success': True, 'id': tecnico.pk, 'nombre': nombre_tecnico})
    else:
        # Limpiar errores para enviarlos como JSON
        cleaned_errors = {}
        for field, errors in form.errors.as_data().items():
            cleaned_errors[field] = [str(e.message) for e in errors]
        return JsonResponse({'success': False, 'errors': cleaned_errors}, status=400)

def buscar_tecnico(request):
    """Busca técnicos para el autocompletado."""
    term = request.GET.get('term', '').strip()
    
    # Asumiendo que el modelo Tecnico tiene un campo 'nombre'
    if term:
        tecnicos = Tecnico.objects.filter(nombre__icontains=term).values('id', 'nombre')[:10]
        resultados = [{'id': tec.get('id'), 'text': tec.get('nombre')} for tec in tecnicos]
        return JsonResponse(resultados, safe=False)
        
    return JsonResponse([], safe=False)