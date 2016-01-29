from django.contrib import admin

from .models import Domain, Metric, Statistic


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
