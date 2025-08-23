function mostrarNotificacion(mensaje, tipo) {
    const notificacion = document.createElement('div');
    notificacion.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white font-medium flex items-center z-50 ${
        tipo === 'success' ? 'bg-green-500' :
        tipo === 'error' ? 'bg-red-500' : 'bg-yellow-500'
    }`;
    notificacion.innerHTML = `
        <i class="fas ${
            tipo === 'success' ? 'fa-check-circle' :
            tipo === 'error' ? 'fa-times-circle' : 'fa-exclamation-triangle'
        } mr-2"></i>${mensaje}
    `;
    document.body.appendChild(notificacion);
    setTimeout(() => {
        notificacion.classList.add('opacity-0', 'transition-opacity', 'duration-500');
        setTimeout(() => notificacion.remove(), 500);
    }, 3000);
}
