// gestion_servicios/static/gestion_servicios/js/autocomplete.js

// Usamos el ID del campo 'clave' (DNI/RUC). Asumimos 'id_clave' es el ID.
// Si tu ID real es 'id_cliente_form-clave', ajusta aquí.
const claveInput = document.getElementById('id_clave'); 

// Lista de campos del formulario de cliente a autocompletar
const fields = {
    'nombre': document.getElementById('id_nombre'),
    'direccion': document.getElementById('id_direccion'),
    'telefono': document.getElementById('id_telefono'),
    'celular': document.getElementById('id_celular'),
    'email': document.getElementById('id_email'),
};

// Función para limpiar todos los campos del cliente
function clearClientFields() {
    for (let key in fields) {
        if (fields[key]) {
            fields[key].value = '';
            fields[key].readOnly = false; // Habilitamos la edición
        }
    }
}

// Función que realiza la búsqueda AJAX
if (claveInput) {
    claveInput.addEventListener('blur', function() {
        const clave = claveInput.value.trim();

        if (clave.length > 0) {
            // URL de la API. Usamos 'servicios/' porque es el namespace de la app
            const apiUrl = `/servicios/api/buscar_cliente/?clave=${clave}`; 
            
            fetch(apiUrl)
                .then(response => response.json())
                .then(data => {
                    if (data.existe) {
                        // Cliente encontrado: autocompletar y deshabilitar edición
                        alert(`Cliente ${data.nombre} encontrado. Autocompletando datos.`);
                        
                        fields.nombre.value = data.nombre;
                        fields.direccion.value = data.direccion;
                        fields.telefono.value = data.telefono;
                        fields.celular.value = data.celular;
                        fields.email.value = data.email;

                        // Deshabilitar los campos para evitar la creación duplicada
                        for (let key in fields) {
                             if (fields[key]) {
                                fields[key].readOnly = true; 
                            }
                        }

                    } else {
                        // Cliente NO encontrado: limpiar y habilitar edición
                        alert("Cliente no encontrado. Por favor, ingrese sus datos completos.");
                        clearClientFields(); 
                        // Volvemos a poner la clave ingresada
                        claveInput.value = clave; 
                    }
                })
                .catch(error => {
                    console.error('Error al buscar cliente:', error);
                    alert("Ocurrió un error al intentar la búsqueda.");
                    clearClientFields();
                    claveInput.value = clave;
                });
        } else {
            clearClientFields();
        }
    });
}