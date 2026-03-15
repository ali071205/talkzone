from django.forms import ModelForm
from django import forms
from django.contrib.auth.models import User
from .models import Profile
from allauth.account.forms import SignupForm


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'First Name',
            'class': 'auth-input',
        })
    )
    last_name = forms.CharField(
        max_length=30, required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last Name',
            'class': 'auth-input',
        })
    )
    age = forms.IntegerField(
        required=True, min_value=13, max_value=120,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Age (min 13)',
            'class': 'auth-input',
        })
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'auth-file-input',
            'accept': 'image/*',
        })
    )

    field_order = ['first_name', 'last_name', 'email', 'age', 'photo', 'password1', 'password2']

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()

        profile, created = Profile.objects.get_or_create(user=user)
        profile.age = self.cleaned_data.get('age')
        # displayname = first name
        profile.displayname = self.cleaned_data.get('first_name', '')

        photo = self.cleaned_data.get('photo')
        if photo:
            profile.image = photo

        profile.save()
        return user


class ProfileForm(ModelForm):
    first_name = forms.CharField(max_length=30, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    class Meta:
        model = Profile
        fields = ['image', 'displayname', 'age', 'info']
        widgets = {
            'image': forms.FileInput(),
            'displayname': forms.TextInput(attrs={'placeholder': 'Display name'}),
            'age': forms.NumberInput(attrs={'placeholder': 'Age', 'min': 13}),
            'info': forms.Textarea(attrs={'rows': 3, 'placeholder': 'About you...'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.save()
        if commit:
            profile.save()
        return profile


class EmailForm(ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ['email']


class UsernameForm(ModelForm):
    class Meta:
        model = User
        fields = ['username']