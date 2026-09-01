from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(AdminUserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            "username": "Nombre de usuario",
            "email": "correo@ejemplo.com",
            "password1": "Contraseña",
            "password2": "Repite la contraseña",
        }
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "input w-full"
            if name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[name]


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email")
