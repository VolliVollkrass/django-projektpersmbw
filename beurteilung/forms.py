from django import forms

class EvaluationForm(forms.Form):
    rating = forms.IntegerField(
        min_value=1,
        max_value=8,
        label="Bewertung (1-8)"
    )

    comment = forms.CharField(
        widget=forms.Textarea,
        label="Bitte Bewertung begründen"
    )