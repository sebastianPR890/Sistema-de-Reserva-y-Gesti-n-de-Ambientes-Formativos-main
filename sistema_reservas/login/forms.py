from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from usuarios.models import Usuario

class CustomLoginForm(AuthenticationForm):
    """Formulario personalizado para el inicio de sesión."""
    
    username = forms.CharField(
        label='Documento',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su documento de identidad',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña'
        })
    )

    def clean_username(self):
        """Valida el formato del documento sin revelar si existe."""
        documento = self.cleaned_data.get('username')
        if documento:
            if len(documento) < 5 or len(documento) > 20:
                raise forms.ValidationError('El documento debe tener entre 5 y 20 caracteres.')
        return documento

class CustomRegistroForm(UserCreationForm):
    """Formulario personalizado para el registro de usuarios."""
    
    class Meta:
        model = Usuario
        fields = ['documento', 'nombres', 'apellidos', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        """Inicializa el formulario con estilos y validaciones."""
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        self.fields['password1'].help_text = 'La contraseña debe tener al menos 8 caracteres'
        self.fields['password2'].help_text = 'Repite la contraseña'

        # Atributos iniciales para CC (por defecto)
        self.fields['documento'].widget.attrs.update({
            'maxlength': '10',
            'pattern': '[0-9]{6,10}',
            'inputmode': 'numeric',
            'placeholder': 'Cédula de Ciudadanía (6-10 dígitos)',
            'title': 'Ingresa entre 6 y 10 dígitos numéricos',
        })

    # Reglas de validación por tipo de documento
    REGLAS_DOCUMENTO = {
        'CC':  {'min': 6,  'max': 10, 'solo_numeros': True,  'label': 'Cédula de Ciudadanía (6-10 dígitos numéricos)'},
        'TI':  {'min': 10, 'max': 11, 'solo_numeros': True,  'label': 'Tarjeta de Identidad (10-11 dígitos numéricos)'},
        'CE':  {'min': 1,  'max': 12, 'solo_numeros': False, 'label': 'Cédula de Extranjería (máx. 12 caracteres alfanuméricos)'},
        'PEP': {'min': 1,  'max': 15, 'solo_numeros': False, 'label': 'PEP (máx. 15 caracteres alfanuméricos)'},
        'PPT': {'min': 1,  'max': 15, 'solo_numeros': False, 'label': 'Permiso por Protección Temporal (máx. 15 caracteres alfanuméricos)'},
    }

    def clean_email(self):
        """Valida que el correo electrónico no esté ya registrado."""
        email = self.cleaned_data.get('email')
        if email and Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado. Usa uno diferente.')
        return email

    def clean_documento(self):
        """Valida el documento según el tipo seleccionado."""
        documento = self.cleaned_data.get('documento')
        tipo = self.data.get('tipo_documento', 'CC')

        if not documento:
            raise forms.ValidationError('Este campo es obligatorio.')

        regla = self.REGLAS_DOCUMENTO.get(tipo, self.REGLAS_DOCUMENTO['CC'])

        if regla['solo_numeros'] and not documento.isdigit():
            raise forms.ValidationError(f'El campo debe contener únicamente dígitos numéricos para {regla["label"]}.')

        if not (regla['min'] <= len(documento) <= regla['max']):
            raise forms.ValidationError(f'Formato incorrecto. Se esperaba: {regla["label"]}.')

        return documento

    def save(self, commit=True):
        """Guarda el usuario configurando campos adicionales."""
        user = super().save(commit=False)
        user.username = user.documento
        user.rol = 'usuario'
        user.tipo_documento = self.data.get('tipo_documento', 'CC')
        if commit:
            user.save()
        return user
