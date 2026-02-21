from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django_ratelimit.decorators import ratelimit

from usuarios.models import Usuario
from .forms import CustomLoginForm, CustomRegistroForm


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """Maneja el inicio de sesión de usuarios."""
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        documento = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=documento, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('/')
        else:
            messages.error(request, 'Documento o contraseña incorrectos')
    
    form = CustomLoginForm()
    return render(request, 'login/login.html', {'form': form})


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def registro_view(request):
    """Maneja el registro de nuevos usuarios."""
    if request.user.is_authenticated:
        return redirect('/')
        
    if request.method == 'POST':
        form = CustomRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro exitoso')
            return redirect('/')
    else:
        form = CustomRegistroForm()
    
    return render(request, 'login/registro.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    """Maneja el cierre de sesión."""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login:login')


# --- Vistas de Recuperación de Contraseña ---

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def recu_contra(request):
    """Maneja la recuperación de contraseña vía email."""
    generic_msg = "Si el correo está registrado, recibirás un enlace para cambiar tu contraseña."

    if request.method == 'POST':
        email_input = request.POST.get('email')

        try:
            user = Usuario.objects.get(email=email_input)

            signer = TimestampSigner()
            token = signer.sign(f"{user.pk}:{user.password[:8]}")
            reset_url = request.build_absolute_uri(reverse('login:cambia_con', args=[token]))

            html_message = render_to_string('login/msg_correo.html', {
                'username': user.documento,
                'reset_url': reset_url,
                'site_name': 'Sistema de Reservas SENA',
            })

            subject = "Recuperación de contraseña"
            text_message = strip_tags(html_message)

            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )

            email_msg.attach_alternative(html_message, "text/html")
            email_msg.encoding = 'utf-8'
            email_msg.send()

        except Usuario.DoesNotExist:
            pass
        except Exception:
            pass

        messages.success(request, generic_msg)
        return redirect("login:login")

    return render(request, 'login/recuperar_contraseña.html')


def cambia_con(request, token):
    """Permite cambiar la contraseña usando un token de recuperación."""
    signer = TimestampSigner()
    try:
        signed_data = signer.unsign(token, max_age=3600)
        user_id, password_hash_prefix = signed_data.split(':', 1)
        usuario = get_object_or_404(Usuario, pk=user_id)
        # Verificar que el token no haya sido usado (el password no cambió)
        if usuario.password[:8] != password_hash_prefix:
            messages.error(request, "Este enlace de recuperación ya fue utilizado.")
            return redirect("login:recu_contra")
    except (BadSignature, SignatureExpired):
        messages.error(request, "El enlace de recuperación es inválido o ha expirado.")
        return redirect("login:recu_contra")
    except (ValueError, IndexError):
        messages.error(request, "El enlace de recuperación es inválido.")
        return redirect("login:recu_contra")

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'login/cambia_contraseña.html')

        try:
            validate_password(new_password, usuario)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'login/cambia_contraseña.html')

        usuario.password = make_password(new_password)
        usuario.save()

        messages.success(request, "La contraseña se ha cambiado correctamente.")
        return redirect("login:login")

    return render(request, 'login/cambia_contraseña.html')


def ratelimited_view(request, exception):
    """Vista para mostrar cuando se excede el limite de peticiones."""
    messages.error(request, 'Has realizado demasiados intentos. Por favor espera un momento antes de intentar de nuevo.')
    return redirect('login:login')