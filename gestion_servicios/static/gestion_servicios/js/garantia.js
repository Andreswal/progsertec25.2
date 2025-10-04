document.addEventListener('DOMContentLoaded', function() {
    const fechaCompraInput = document.getElementById('id_fecha_compra');
    const garantiaStatus = document.getElementById('garantia-status');

    function checkGarantia() {
        // Asegúrate de que los elementos existen antes de continuar
        if (!fechaCompraInput || !garantiaStatus) {
            return;
        }

        const fechaCompraStr = fechaCompraInput.value;
        if (!fechaCompraStr) {
            garantiaStatus.style.display = 'none';
            return;
        }

        const fechaCompra = new Date(fechaCompraStr + 'T00:00:00'); // Añadimos 'T00:00:00' para evitar problemas de zona horaria
        const hoy = new Date();
        
        // Asumimos una garantía estándar de 1 año (365 días)
        const fechaLimite = new Date(fechaCompra);
        fechaLimite.setFullYear(fechaLimite.getFullYear() + 1);

        // La garantía es válida si la fecha límite es mayor o igual a hoy
        const enGarantia = fechaLimite >= hoy;

        if (enGarantia) {
            garantiaStatus.style.display = 'inline-block';
        } else {
            garantiaStatus.style.display = 'none';
        }
    }
    
    // Ejecutar al cargar la página (útil si ya hay una fecha pre-cargada)
    checkGarantia();

    // Ejecutar la lógica al cambiar el campo
    if (fechaCompraInput) {
        fechaCompraInput.addEventListener('change', checkGarantia);
    }
});