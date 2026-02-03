import re
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Compilar las expresiones regulares una sola vez
        self.exempt_urls = [re.compile(url) for url in settings.LOGIN_EXEMPT_URLS]

    def __call__(self, request):
        # Verificar autenticación
        if not request.user.is_authenticated:
            path = request.path_info.lstrip('/')
            
            # Verificar si la URL actual está exenta
            if not any(url.match(path) for url in self.exempt_urls):
                messages.warning(request, 'Por favor inicia sesión para acceder a esta página.')
                return redirect(f"{settings.LOGIN_URL}?next={request.path}")
            
        # Verificar si el usuario está activo
        elif request.user.is_authenticated and not request.user.is_active:
            messages.error(request, 'Tu cuenta está desactivada.')
            return redirect('login:logout')

        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Llamado justo antes de que Django llame a la vista.
        Retorna None para continuar el procesamiento o una HttpResponse para terminar.
        """
        # Aquí puedes agregar lógica adicional antes de que se ejecute la vista
        return None

    def process_template_response(self, request, response):
        """
        Llamado justo después de que la vista haya terminado de ejecutarse,
        si la respuesta contiene un método .render()
        """
        return response

    def process_exception(self, request, exception):
        """
        Llamado cuando una vista lanza una excepción
        """
        # Aquí puedes manejar excepciones específicas
        return None
