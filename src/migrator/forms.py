# myapp/forms.py
from django import forms


class SyncForm(forms.Form):
    source = forms.CharField(
        label="source",
        widget=forms.TextInput(
            attrs={"class": "form-control text-center w-50 mx-auto"}
        ),
    )
    destination = forms.CharField(
        label="destination",
        widget=forms.TextInput(
            attrs={"class": "form-control text-center w-50 mx-auto"}
        ),
    )
    additional_arguments = forms.CharField(
        label="additional_arguments",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    dry_run = forms.BooleanField(
        label="dry_run",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    input_text = forms.CharField(
        label="input_text",
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 5, "autocomplete": "off"}
        ),
    )
