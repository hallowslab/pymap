# myapp/forms.py
from django import forms


class SyncForm(forms.Form):
    credentials_placeholder = "Source@Account Password Destination@Account Password\ntest@email.com Password123 test@email.com Password123"
    source = forms.CharField(
        label="source",
        widget=forms.TextInput(attrs={"class": "form-control text-center w-25 mx-3"}),
    )
    destination = forms.CharField(
        label="destination",
        widget=forms.TextInput(attrs={"class": "form-control text-center w-25 mx-3"}),
    )
    input_text = forms.CharField(
        label="input_text",
        widget=forms.Textarea(
            attrs={
                "class": "form-control w-75 mx-auto",
                "rows": 5,
                "autocomplete": "off",
                "placeholder": credentials_placeholder,
            }
        ),
    )
    additional_arguments = forms.CharField(
        label="additional_arguments",
        required=False,
        initial="",
        widget=forms.TextInput(
            attrs={
                "class": "form-control mx-2",
                "style": "max-width: 300px;",
                "placeholder": "--nossl1 --timeout 300 --office2  .....",
            }
        ),
    )
    dry_run = forms.BooleanField(
        label="dry_run",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input mx-2"}),
    )
