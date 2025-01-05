from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=Profile.Role.choices, initial=Profile.Role.STUDENT
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "role"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.role = self.cleaned_data["role"]
            user.profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }
