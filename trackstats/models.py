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

    order_field = None

    def narrow(self, metric=None, metrics=None, period=None):
        qs = self
        assert metric is None or metrics is None
        if metric is not None:
            metrics = [metric]
        if metrics is not None:
            qs = qs.filter(metric__in=metrics)
        if period:
            qs = qs.filter(period=period)
        return qs

    def record(self, metric, value, period, **kwargs):
        instance, _ = self.update_or_create(
            period=period,
            metric=metric,
            defaults={'value': value},
            **kwargs)
        return instance

    def most_recent(self, **kwargs):
        return self.narrow(**kwargs).order_by('-' + self.order_field).first()


class AbstractStatistic(models.Model):
    metric = models.ForeignKey(Metric, on_delete=models.PROTECT)
    value = models.BigIntegerField(
        # To support storing that no data is available, use: NULL
        null=True)
    period = models.IntegerField(choices=PERIOD_CHOICES)

    class Meta:
        abstract = True


class ByObjectMixin(models.Model):
    object_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    object = GenericForeignKey(
        'object_type',
        'object_id')

    class Meta:
        abstract = True


class ByObjectQuerySetMixin(object):

    def record(self, **kwargs):
        object = kwargs.pop('object')
        ct = ContentType.objects.get_for_model(object)
        return super(ByObjectQuerySetMixin, self).record(
            object_id=object.pk,
            object_type=ct,
            **kwargs)

    def narrow(self, **kwargs):
        qs = self
        object = kwargs.pop('object', None)
        objects = kwargs.pop('objects', None)
        object_type = kwargs.pop('object_type', None)
        assert object is None or objects is None
        if object is not None:
            objects = [object]
        if object_type:
            qs = qs.filter(object_type=object_type)
        if type(objects) in (list, tuple, set):
            if not objects:
                qs = self.none()
            else:
                # Assumption: all objects are of same type
                ct = ContentType.objects.get_for_model(objects[0])
                qs = qs.filter(
                    object_type=ct,
                    object_id__in=[s.pk for s in objects])
        elif isinstance(objects, models.QuerySet):
            ct = ContentType.objects.get_for_model(objects.model)
            qs = qs.filter(
                object_type=ct,
                object_id__in=objects.values_list(
                    'id', flat=True))
        elif objects is None:
            pass
        elif isinstance(objects, models.query.EmptyQuerySet):
            qs = self.none()
        else:
            raise NotImplementedError
        return super(ByObjectQuerySetMixin, qs).narrow(**kwargs)


class ByDateMixin(models.Model):
    date = models.DateField(db_index=True)

    class Meta:
        abstract = True


class ByDateQuerySetMixin(object):

    order_field = 'date'

    def record(self, **kwargs):
        dt = kwargs.pop('date', date.today())
        return super(ByDateQuerySetMixin, self).record(date=dt, **kwargs)

    def narrow(self, **kwargs):
        """Up-to including"""
        from_date = kwargs.pop('from_date', None)
        to_date = kwargs.pop('to_date', None)
        date = kwargs.pop('date', None)
        qs = self
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)
        if date:
            qs = qs.filter(date=date)
        return super(ByDateQuerySetMixin, qs).narrow(**kwargs)


class StatisticByDateQuerySet(
        ByDateQuerySetMixin,
        AbstractStatisticQuerySet):
    pass


class StatisticByDateAndObjectQuerySet(
        ByDateQuerySetMixin,
        ByObjectQuerySetMixin,
        AbstractStatisticQuerySet):
    pass


class StatisticByDate(ByDateMixin, AbstractStatistic):
    objects = StatisticByDateQuerySet.as_manager()

    class Meta:
        unique_together = [
            'date',
            'metric',
            'period']
        verbose_name = 'Statistic by date'
        verbose_name_plural = 'Statistics by date'

    def __str__(self):
        return '{date}: {value}'.format(
            date=self.date,
            value=self.value)


class StatisticByDateAndObject(
        ByDateMixin,
        ByObjectMixin,
        AbstractStatistic):
    objects = StatisticByDateAndObjectQuerySet.as_manager()

    class Meta:
        unique_together = [
            'date',
            'metric',
            'object_type',
            'object_id',
            'period']
        verbose_name = 'Statistic by date and object'
        verbose_name_plural = 'Statistics by date and object'

    def __str__(self):
        return '{date}: {value}'.format(
            date=self.date,
            value=self.value)
