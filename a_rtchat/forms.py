from django.forms import ModelForm
from django import forms
from .models import ChatGroup, GroupMessage


class ChatMessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body']
        widgets = {
            'body': forms.TextInput(attrs={
                'placeholder': 'Type your message here...',
                'maxlength': '300',
                'autofocus': True
            }),
        }


class NewGroupForm(ModelForm):
    max_members = forms.IntegerField(
        required=False,
        min_value=3,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max members (min 3, blank = unlimited)',
        }),
        label='Max Members'
    )

    class Meta:
        model = ChatGroup
        fields = ['groupchat_name', 'max_members']
        widgets = {
            'groupchat_name': forms.TextInput(attrs={
                'placeholder': 'Guild name...',
                'maxlength': '100',
                'autofocus': True
            }),
        }


class ChatRoomEditForm(ModelForm):
    max_members = forms.IntegerField(
        required=False,
        min_value=3,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max members (min 3, blank = unlimited)',
        }),
        label='Max Members'
    )

    class Meta:
        model = ChatGroup
        fields = ['groupchat_name', 'max_members']
        widgets = {
            'groupchat_name': forms.TextInput(attrs={
                'placeholder': 'Guild name...',
                'maxlength': '100',
            }),
        }