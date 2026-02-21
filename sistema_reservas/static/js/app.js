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

// Efecto parallax suave en el scroll
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        heroSection.style.transform = `translateY(${scrolled * 0.1}px)`;
    }
});


