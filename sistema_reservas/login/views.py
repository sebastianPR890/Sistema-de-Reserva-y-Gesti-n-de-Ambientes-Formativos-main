from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.urls import reverse

from usuarios.models import Usuario
from .forms import CustomLoginForm, CustomRegistroForm


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
            messages.success(request, f'Bienvenido {user.nombre_completo()}')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('/')
        else:
            messages.error(request, 'Documento o contraseña incorrectos')
    
    form = CustomLoginForm()
    return render(request, 'login/login.html', {'form': form})


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
def logout_view(request):
    """Maneja el cierre de sesión."""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login:login')


# --- Vistas de Recuperación de Contraseña ---

def recu_contra(request):
    """Maneja la recuperación de contraseña vía email."""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = Usuario.objects.get(email=email)
            
            recovery_email = user.email
            signer = TimestampSigner()
            token = signer.sign(str(user.pk))
            reset_url = request.build_absolute_uri(reverse('login:cambia_con', args=[token]))
            
            html_message = render_to_string('login/msg_correo.html', {
                'username': user.documento,
                'reset_url': reset_url,
                'site_name': 'Sistema de Reservas SENA',
            })
            
            subject = "Recuperación de contraseña"
            text_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recovery_email]
            )
            
            email.attach_alternative(html_message, "text/html")
            email.encoding = 'utf-8'
            email.send()
            
            messages.success(request, "Se ha enviado un enlace a tu correo de recuperación para cambiar la contraseña.")
            return redirect("login:login")
            
        except Usuario.DoesNotExist:
            messages.error(request, "El correo ingresado no está registrado.")
            return render(request, 'login/recuperar_contraseña.html')
        except Exception as e:
            messages.error(request, f"Error al enviar el correo: {str(e)}")
            return render(request, 'login/recuperar_contraseña.html')
        
    return render(request, 'login/recuperar_contraseña.html')


def cambia_con(request, token):
    """Permite cambiar la contraseña usando un token de recuperación."""
    signer = TimestampSigner()
    try:
        user_id = signer.unsign(token, max_age=3600)
        usuario = get_object_or_404(Usuario, pk=user_id)
    except (BadSignature, SignatureExpired):
        messages.error(request, "El enlace de recuperación es inválido o ha expirado.")
        return redirect("login:recu_contra")
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'login/cambia_contraseña.html')
        
        usuario.password = make_password(new_password)
        usuario.save()
        
        messages.success(request, "La contraseña se ha cambiado correctamente.")
        return redirect("login:login")
    
    return render(request, 'login/cambia_contraseña.html')