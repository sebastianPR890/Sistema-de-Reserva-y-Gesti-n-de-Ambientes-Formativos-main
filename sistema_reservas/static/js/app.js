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

function createParticles() {
    /**Crea partículas flotantes de fondo para efectos visuales.**/
    const particles = document.getElementById('particles');
    if (!particles) return;
    
    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('particle');
        
        const size = Math.random() * 4 + 2;
        const startPosition = Math.random() * 100;
        const animationDuration = Math.random() * 10 + 10;
        const animationDelay = Math.random() * 5;
        
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.left = startPosition + '%';
        particle.style.animationDuration = animationDuration + 's';
        particle.style.animationDelay = animationDelay + 's';
        
        particles.appendChild(particle);
    }
}

function typeWriter(element, text, speed = 100) {
    /**Crea un efecto de escritura animada en el elemento especificado.**/
    if (!element) return;
    let i = 0;
    element.innerHTML = '';
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Inicializar efectos
document.addEventListener('DOMContentLoaded', function() {
    createParticles();
    
    // Agregar efecto de hover a los botones
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-3px) scale(1.05)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

// Efecto parallax suave en el scroll
window.addEventListener('scroll', function() {
    const scrolled = window.pageYOffset;
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        heroSection.style.transform = `translateY(${scrolled * 0.1}px)`;
    }
});


/* =========================================
    WIDGET DE ACCESIBILIDAD V2 - CORREGIDO
   ========================================== */
document.addEventListener('DOMContentLoaded', () => {
    const fab = document.getElementById('accessibility-fab');
    const panel = document.getElementById('accessibility-panel');
    const closeBtn = document.getElementById('close-accessibility-panel');
    const gridButtons = document.querySelectorAll('.panel-grid button');
    const body = document.body;

    // Helper para convertir kebab-case a camelCase
    const toCamelCase = str => str.replace(/-([a-z])/g, g => g[1].toUpperCase());

    const settings = {
        fontSize: 0, // 0: normal, 1, 2, 3
        highContrast: false,
        grayscale: false,
        highlightLinks: false,
        highlightHeaders: false,
        bigCursor: false,
    };

    const FONT_CLASSES = ['', 'font-size-1', 'font-size-2', 'font-size-3'];

    function loadSettings() {
        const savedSettings = JSON.parse(localStorage.getItem('accessibilitySettings'));
        if (savedSettings) {
            Object.assign(settings, savedSettings);
        }
        applySettings();
    }

    function saveSettings() {
        localStorage.setItem('accessibilitySettings', JSON.stringify(settings));
    }

    function applySettings() {
        // Limpiar clases del body
        body.className = body.className.split(' ').filter(c => !c.startsWith('font-size-') && !Object.keys(settings).map(k => k.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`)).includes(c)).join(' ');
        
        // Aplicar clases de fuente
        if (settings.fontSize > 0) {
            body.classList.add(FONT_CLASSES[settings.fontSize]);
        }

        // Aplicar clases booleanas
        for (const key in settings) {
            if (key !== 'fontSize' && settings[key] === true) {
                const kebabCaseKey = key.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`);
                body.classList.add(kebabCaseKey);
            }
        }
        updateButtonsState();
    }

    function updateButtonsState() {
        gridButtons.forEach(button => {
            const action = button.dataset.action;
            if (action === 'increase-text' || action === 'decrease-text' || action === 'reset') return;

            const camelCaseAction = toCamelCase(action);
            if (settings[camelCaseAction]) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }

    fab.addEventListener('click', () => panel.classList.add('active'));
    closeBtn.addEventListener('click', () => panel.classList.remove('active'));

    gridButtons.forEach(button => {
        button.addEventListener('click', () => {
            const action = button.dataset.action;
            const camelCaseAction = toCamelCase(action);

            switch (action) {
                case 'increase-text':
                    if (settings.fontSize < FONT_CLASSES.length - 1) settings.fontSize++;
                    break;
                case 'decrease-text':
                    if (settings.fontSize > 0) settings.fontSize--;
                    break;
                case 'reset':
                    for (const key in settings) {
                        settings[key] = typeof settings[key] === 'boolean' ? false : 0;
                    }
                    break;
                default:
                    if (typeof settings[camelCaseAction] === 'boolean') {
                        settings[camelCaseAction] = !settings[camelCaseAction];
                    }
                    break;
            }
            applySettings();
            saveSettings();
        });
    });

    loadSettings();
});
