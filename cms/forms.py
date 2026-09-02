from django import forms
from wagtail.admin.forms import WagtailAdminPageForm

# Constantes
TAG_CHOICES = [
    ("Cuento", "Cuento"),
    ("Ensayo", "Ensayo"),
    ("Música", "Música"),
    ("Poesía", "Poesía"),
    ("Reseña", "Reseña"),
]


class ArticlePageForm(WagtailAdminPageForm):
    tags = forms.MultipleChoiceField(
        choices=TAG_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Tags",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["tags"].initial = list(
                self.instance.tags.values_list("name", flat=True)
            )

    def save(self, commit=True):
        page = super().save(commit=commit)
        page.tags.set(self.cleaned_data.get("tags") or [])
        if commit:
            page.save()
        return page
