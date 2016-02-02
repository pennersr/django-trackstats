import json

from django.conf.urls import url
from django.contrib import admin

from django.template.response import TemplateResponse

from trackstats.models import Domain, Metric, Statistic
from trackstats.admin.forms import GraphForm


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = (
        'ref',
        'name')


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    search_fields = (
        'ref',
        'name')
    list_display = (
        'ref',
        'name')
    list_filter = (
        'domain',)


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    change_list_template = 'trackstats/admin/change_list.html'

    ordering = (
        '-date',)
    list_display = (
        'date',
        'metric',
        'subject_type',
        'subject',
        'value'
    )
    date_hierarchy = 'date'
    list_filter = (
        'date',
        'period',
        'metric__domain',
        'metric')

    def get_urls(self):
        urls = super(StatisticAdmin, self).get_urls()
        custom_urls = [
            url('^graphs/$', self.graphs, name='trackstats_graphs')
        ]
        return custom_urls + urls

    def graphs(self, request):
        data = {}
        context = dict(
            self.admin_site.each_context(request))
        if 'to_date' in request.GET:
            form = GraphForm(request.GET)
            if form.is_valid():
                stats = form.get_statistics()
                data = {
                    'labels': [
                        s.date.isoformat()
                        for s in stats
                    ],
                    'series': [[
                        s.value
                        for s in stats
                    ]]
                }
                context['graph_data'] = json.dumps(data)
        else:
            stat = Statistic.objects.last()
            initial = {}
            if stat:
                initial['metric'] = stat.metric
                initial['subject_type'] = stat.subject_type
            form = GraphForm(initial=initial)
        context['form'] = form
        return TemplateResponse(
            request,
            "trackstats/admin/graphs.html",
            context)
