from django.conf.urls import url
from django.contrib import admin

from django.template.response import TemplateResponse

from trackstats.models import (
    Domain,
    Metric,
    StatisticByDate,
    StatisticByDateAndObject)
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


@admin.register(StatisticByDate)
class StatisticByDateAdmin(admin.ModelAdmin):
    change_list_template = 'trackstats/admin/change_list.html'

    ordering = (
        '-date',)
    list_display = (
        'date',
        'metric',
        'value'
    )
    date_hierarchy = 'date'
    list_filter = (
        'date',
        'period',
        'metric__domain',
        'metric')

    def get_urls(self):
        urls = super(StatisticByDateAdmin, self).get_urls()
        custom_urls = [
            url('^graph/$', self.graph, name='trackstats_graph_by_date')
        ]
        return custom_urls + urls

    def graph(self, request):
        context = dict(
            self.admin_site.each_context(request))
        if 'to_date' in request.GET:
            form = GraphForm(request.GET)
            if form.is_valid():
                stats = []
                for stat in form.get_statistics():
                    stats.append(
                        dict(
                            js_date='new Date({}, {}, {})'.format(
                                stat.date.year,
                                stat.date.month-1,
                                stat.date.day),
                            value=stat.value))
                context['statistics'] = stats
        else:
            stat = StatisticByDate.objects.last()
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


@admin.register(StatisticByDateAndObject)
class StatisticByDateAndObjectAdmin(admin.ModelAdmin):
    change_list_template = 'trackstats/admin/change_list.html'

    ordering = (
        '-date',)
    list_display = (
        'date',
        'metric',
        'object_type',
        'object_id',
        'value'
    )
    date_hierarchy = 'date'
    list_filter = (
        'date',
        'period',
        'metric__domain',
        'metric')

    def get_urls(self):
        urls = super(StatisticByDateAndObjectAdmin, self).get_urls()
        custom_urls = [
            url('^graph/$', self.graph,
                name='trackstats_graph_by_date_and_object')
        ]
        return custom_urls + urls

    def graph(self, request):
        context = dict(
            self.admin_site.each_context(request))
        if 'to_date' in request.GET:
            form = GraphForm(request.GET)
            if form.is_valid():
                stats = []
                for stat in form.get_statistics():
                    stats.append(
                        dict(
                            js_date='new Date({}, {}, {})'.format(
                                stat.date.year,
                                stat.date.month-1,
                                stat.date.day),
                            value=stat.value))
                context['statistics'] = stats
        else:
            stat = StatisticByDate.objects.last()
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
