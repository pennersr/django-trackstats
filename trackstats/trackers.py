from datetime import date, timedelta, datetime, time

from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.db import connections
from django.utils import timezone

from .models import Period, StatisticByDate, StatisticByDateAndObject


class ObjectsByDateTracker(object):
    date_field = 'date'
    aggr_op = None
    metric = None
    period = None
    statistic_model = StatisticByDate

    def __init__(self, **kwargs):
        for prop, val in kwargs.items():
            setattr(self, prop, val)

    def get_most_recent_kwargs(self):
        most_recent_kwargs = {
            'metric': self.metric,
            'period': self.period}
        return most_recent_kwargs

    def get_start_date(self, qs):
        most_recent_kwargs = self.get_most_recent_kwargs()
        last_stat = self.statistic_model.objects.most_recent(
            **most_recent_kwargs)
        if last_stat:
            start_date = last_stat.date
        else:
            first_instance = qs.order_by(self.date_field).first()
            if first_instance is None:
                # No data
                return
            start_date = getattr(first_instance, self.date_field)
        if start_date and isinstance(start_date, datetime):
            if timezone.is_aware(start_date):
                start_date = timezone.make_naive(start_date).date()
            else:
                start_date = start_date.date()
        return start_date

    def track_lifetime_upto(self, qs, upto_date):
        filter_kwargs = {
            self.date_field + '__date__lte': upto_date
        }
        n = qs.filter(**filter_kwargs).count()
        self.statistic_model.objects.record(
            metric=self.metric,
            value=n,
            period=self.period,
            date=upto_date)

    def get_track_values(self):
        return []

    def get_record_kwargs(self, val):
        return {}

    def track(self, qs):
        to_date = date.today()
        start_date = self.get_start_date(qs)
        if not start_date:
            return
        if self.period == Period.LIFETIME:
            # Intentionally recompute last stat, as we may have computed
            # that the last time when the day was not over yet.
            upto_date = start_date
            while upto_date <= to_date:
                self.track_lifetime_upto(qs, upto_date)
                upto_date += timedelta(days=1)
        elif self.period == Period.DAY:
            values_fields = ['ts_date'] + self.get_track_values()
            connection = connections[qs.db]
            tzname = (
                timezone.get_current_timezone_name()
                if settings.USE_TZ else None)

            is_datetime = isinstance(qs.model._meta.get_field(
                self.date_field), models.DateTimeField)
            if is_datetime:
                date_sql = connection.ops.datetime_cast_date_sql(
                    self.date_field,
                    tzname)
                # before django 2.0 it returns a tuple
                if isinstance(date_sql, tuple):
                    vals = qs.extra(
                        select={"ts_date": date_sql[0]},
                        select_params=date_sql[1])
                else:
                    vals = qs.extra(select={"ts_date": date_sql})
                start_dt = datetime.combine(
                    start_date, time()) - timedelta(days=1)
                if tzname:
                    start_dt = timezone.make_aware(
                        start_dt,
                        timezone.get_current_timezone())
            else:
                vals = qs.extra(select={"ts_date": self.date_field})
                start_dt = start_date
            vals = vals.filter(
                **{self.date_field + '__gte': start_dt}).values(
                *values_fields).order_by().annotate(ts_n=self.aggr_op)
            # TODO: Bulk create
            for val in vals:
                self.statistic_model.objects.record(
                    metric=self.metric,
                    value=val['ts_n'],
                    date=val['ts_date'],
                    period=self.period,
                    **self.get_record_kwargs(val))
        else:
            raise NotImplementedError


class ObjectsByDateAndObjectTracker(ObjectsByDateTracker):
    object = None
    object_model = None
    object_field = None
    statistic_model = StatisticByDateAndObject

    def __init__(self, **kwargs):
        super(ObjectsByDateAndObjectTracker, self).__init__(**kwargs)
        assert self.object is None or self.object_field is None
        assert self.object or self.object_field

    def get_most_recent_kwargs(self):
        kwargs = super(
            ObjectsByDateAndObjectTracker, self).get_most_recent_kwargs()
        if self.object_model:
            kwargs['object_type'] = ContentType.objects.get_for_model(
                self.object_model)
        else:
            kwargs['object'] = self.object
        return kwargs

    def track_lifetime_upto(self, qs, upto_date):
        filter_kwargs = {
            self.date_field + '__date__lte': upto_date
        }
        if self.object_model:
            vals = qs.filter(**filter_kwargs).values(
                self.object_field).annotate(ts_n=self.aggr_op)
            for val in vals:
                object = self.object_model(
                    pk=val[self.object_field])
                # TODO: Bulk create
                StatisticByDateAndObject.objects.record(
                    metric=self.metric,
                    value=val['ts_n'],
                    date=upto_date,
                    object=object,
                    period=self.period)
        else:
            n = qs.filter(**filter_kwargs).count()
            StatisticByDateAndObject.objects.record(
                metric=self.metric,
                value=n,
                object=self.object,
                period=self.period,
                date=upto_date)

    def get_track_values(self):
        ret = super(ObjectsByDateAndObjectTracker, self).get_track_values()
        if self.object_model:
            ret.append(self.object_field)
        return ret

    def get_record_kwargs(self, val):
        if self.object_model:
            object = self.object_model(pk=val[self.object_field])
        else:
            object = self.object
        return {'object': object}


class CountObjectsByDateTracker(ObjectsByDateTracker):
    aggr_op = models.Count('pk', distinct=True)


class CountObjectsByDateAndObjectTracker(ObjectsByDateAndObjectTracker):
    aggr_op = models.Count('pk', distinct=True)
