from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils.functional import SimpleLazyObject, empty


class Period(object):
    DAY = 86400  # seconds
    WEEK = DAY * 7
    DAYS_28 = DAY * 28
    MONTH = DAY * 30
    LIFETIME = 0


PERIOD_CHOICES = (
    (Period.DAY, 'Day'),
    (Period.WEEK, 'Week'),
    (Period.DAYS_28, '28 days'),
    (Period.MONTH, 'Month'),
    (Period.LIFETIME, 'Lifetime'))


class RegisterLazilyManagerMixin(object):
    _lazy_entries = []

    def _register(self, defaults=None, **kwargs):
        """Fetch (update or create)  an instance, lazily.

        We're doing this lazily, so that it becomes possible to define
        custom enums in your code, even before the Django ORM is fully
        initialized.

        Domain.objects.SHOPPING = Domain.objects.register(
            ref='shopping',
            name='Webshop')
        Domain.objects.USERS = Domain.objects.register(
            ref='users',
            name='User Accounts')
        """
        f = lambda: self.update_or_create(defaults=defaults, **kwargs)[0]
        ret = SimpleLazyObject(f)
        self._lazy_entries.append(ret)
        return ret

    def clear_cache(self):
        """For testability"""
        for entry in self._lazy_entries:
            entry._wrapped = empty


class DomainManager(RegisterLazilyManagerMixin, models.Manager):

    def register(self, ref, name=''):
        return super(DomainManager, self)._register(
            defaults={'name': name},
            ref=ref)

    def get_by_natural_key(self, ref):
        return self.get(ref=ref)


class Domain(models.Model):
    objects = DomainManager()

    ref = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique reference ID for this domain")
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Short descriptive name")

    def __str__(self):
        return self.name or self.ref

    def natural_key(self):
        return [self.ref]


class MetricManager(RegisterLazilyManagerMixin, models.Manager):

    def register(self, domain, ref, name='', description=''):
        return super(MetricManager, self)._register(
            defaults={'name': name,
                      'description': description},
            domain=domain,
            ref=ref)

    def get_by_natural_key(self, domain, ref):
        return self.get(source=domain,
                        ref=ref)


class Metric(models.Model):
    objects = MetricManager()

    domain = models.ForeignKey(Domain, on_delete=models.PROTECT)
    ref = models.CharField(
        max_length=100,
        help_text="Unique reference ID for this metric within the domain")
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Short descriptive name")
    description = models.TextField(
        blank=True,
        help_text="Description")

    class Meta:
        unique_together = ('domain', 'ref')

    def __str__(self):
        return self.name or self.ref

    def natural_key(self):
        return [self.source, self.ref]


class AbstractStatisticQuerySet(models.QuerySet):

    def narrow(self, subject_type=None, subject=None, subjects=None,
                   metric=None, metrics=None, period=None):
        qs = self
        assert subject is None or subjects is None
        if subject is not None:
            subjects = [subject]
        assert metric is None or metrics is None
        if metric is not None:
            metrics = [metric]
        if metrics is not None:
            qs = qs.filter(metric__in=metrics)
        if period:
            qs = qs.filter(period=period)
        if subject_type:
            qs = qs.filter(subject_type=subject_type)
        if type(subjects) in (list, tuple, set):
            if not subjects:
                qs = self.none()
            else:
                # Assumption: all subjects are of same type
                ct = ContentType.objects.get_for_model(subjects[0])
                qs = qs.filter(
                    subject_type=ct,
                    subject_id__in=[s.pk for s in subjects])
        elif isinstance(subjects, models.QuerySet):
            ct = ContentType.objects.get_for_model(subjects.model)
            qs = qs.filter(
                subject_type=ct,
                subject_id__in=subjects.values_list(
                    'id', flat=True))
        elif subjects is None:
            pass
        elif isinstance(subjects, models.query.EmptyQuerySet):
            qs = self.none()
        else:
            raise NotImplementedError
        return qs

    def any_subject(self, metric, subject):
        return metric.domain if subject is None else subject

    def record(self, metric, value, period, subject=None, **kwargs):
        subject = self.any_subject(metric, subject)
        ct = ContentType.objects.get_for_model(subject)
        instance, _ = self.update_or_create(
            subject_id=subject.pk,
            subject_type=ct,
            period=period,
            metric=metric,
            defaults={'value': value},
            **kwargs)
        return instance


class AbstractStatistic(models.Model):
    metric = models.ForeignKey(Metric, on_delete=models.PROTECT)
    subject_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    subject_id = models.PositiveIntegerField()
    subject = GenericForeignKey(
        'subject_type',
        'subject_id')
    value = models.BigIntegerField(
        # To support storing that no data is available, use: NULL
        null=True)
    period = models.IntegerField(choices=PERIOD_CHOICES)

    class Meta:
        abstract = True


class StatisticQuerySet(AbstractStatisticQuerySet):

    def narrow(self, from_date=None, to_date=None, **kwargs):
        """Up-to including"""
        qs = self
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)
        return super(StatisticQuerySet, qs).narrow(**kwargs)

    def record(self, **kwargs):
        dt = kwargs.pop('date', date.today())
        return super(StatisticQuerySet, self).record(
            date=dt,
            **kwargs)

    def most_recent(self, metric, period, subject_type=None, subject=None):
        subject = self.any_subject(metric, subject)
        return self.narrow(
            metrics=[metric],
            period=period,
            subject_type=subject_type,
            subject=subject).order_by('-date').first()


class Statistic(AbstractStatistic):
    objects = StatisticQuerySet.as_manager()

    date = models.DateField(db_index=True)

    class Meta:
        unique_together = [
            'date',
            'metric',
            'subject_type',
            'subject_id',
            'period']

    def __str__(self):
        return '{date}: {value}'.format(
            date=self.date,
            value=self.value)
