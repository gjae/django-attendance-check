document.addEventListener('DOMContentLoaded', function () {
    const nameSelect = document.getElementById('id_names');
    const lastnamesInput = document.getElementById('id_lastnames');

    if (!nameSelect || !lastnamesInput) return;

    // Guardar el consecutivo original (viene precargado del backend)
    const originalConsecutive = lastnamesInput.value;

    function updateConsecutiveCode() {
        const mesa = nameSelect.value;
        if (mesa && originalConsecutive) {
            lastnamesInput.value = mesa + '-' + originalConsecutive;
        }
    }

    // Actualizar al cambiar la mesa
    nameSelect.addEventListener('change', updateConsecutiveCode);

    // Ejecutar al cargar si ya hay una mesa seleccionada
    updateConsecutiveCode();
});
