from django import forms


class BootstrapFormMixin:
    """Adds Bootstrap 5 classes to every widget and a hidden honeypot field against bots."""

    honeypot_name = "website_url"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.honeypot_name] = forms.CharField(required=False, widget=forms.TextInput(
            attrs={"autocomplete": "off", "tabindex": "-1", "class": "hp-field"}), label="Leave empty")
        for name, field in self.fields.items():
            if name == self.honeypot_name:
                continue
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                continue
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")
            if field.required and not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("required", "required")

    def clean(self):
        data = super().clean()
        if data.get(self.honeypot_name):
            raise forms.ValidationError("Submission rejected.")
        return data


class SearchForm(forms.Form):
    q = forms.CharField(max_length=100, required=False)
