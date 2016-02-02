from datetime import timedelta, date

from django import forms
from django.contrib.contenttypes.models import ContentType

from trackstats.models import Metric, Statistic


class GraphForm(forms.Form):

    metric = forms.ModelChoiceField(queryset=None)
    from_date = forms.DateField(initial=date.today() - timedelta(days=7))
    to_date = forms.DateField(initial=date.today())
    subject_type = forms.ModelChoiceField(queryset=None, required=False)
    subject_id = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super(GraphForm, self).__init__(*args, **kwargs)
        self.fields['metric'].queryset = Metric.objects.all()
        self.fields['subject_type'].queryset = ContentType.objects.all()

    def get_statistics(self):
        assert self.is_valid()
        stats = Statistic.objects.narrow(
            from_date=self.cleaned_data['from_date'],
            to_date=self.cleaned_data['to_date'],
            metric=self.cleaned_data['metric'],
            subject_type=self.cleaned_data['subject_type'])
        subject_id = self.cleaned_data['subject_id']
        if subject_id:
            stats = stats.filter(subject_id=subject_id)
        return stats.order_by('date')
