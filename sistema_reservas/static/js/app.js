// Controla el toggle del menú lateral
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const contentWrapper = document.querySelector('.content-wrapper');

function toggleMenu() {
    /**Alterna la visibilidad del menú lateral.**/
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
    menuToggle.classList.toggle('active');
    if (contentWrapper) {
        contentWrapper.classList.toggle('sidebar-open');
    }
}

if (menuToggle && sidebar && overlay) {
    menuToggle.addEventListener('click', toggleMenu);
    overlay.addEventListener('click', toggleMenu);
}

// Auto-dismiss para mensajes Django (desaparecen a los 4 segundos)
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('#django-messages .alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 4000);
    });
});

/**
 * Muestra un aviso emergente en la esquina superior derecha,
 * con el mismo estilo que los mensajes de Django del base.html.
 * @param {string} mensaje - Texto del aviso.
 * @param {string} tipo    - 'success' | 'danger' | 'warning' | 'info'
 */
function showToast(mensaje, tipo) {
    tipo = tipo || 'info';
    const iconos = {
        success: 'fas fa-check-circle',
        danger:  'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info:    'fas fa-info-circle',
    };
    let container = document.getElementById('django-messages');
    if (!container) {
        container = document.createElement('div');
        container.id = 'django-messages';
        container.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;width:min(360px,90vw);';
        document.body.appendChild(container);
    }
    const div = document.createElement('div');
    div.className = 'alert alert-' + tipo + ' alert-dismissible fade show shadow-sm';
    div.style.marginBottom = '0.5rem';
    div.setAttribute('role', 'alert');
    div.innerHTML =
        '<i class="' + (iconos[tipo] || iconos.info) + ' me-2"></i>' +
        mensaje +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>';
    container.appendChild(div);
    setTimeout(function () {
        if (div.parentElement) {
            bootstrap.Alert.getOrCreateInstance(div).close();
        }
    }, 4000);
}

// Efecto parallax suave en el scroll
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        heroSection.style.transform = `translateY(${scrolled * 0.1}px)`;
    }
});


