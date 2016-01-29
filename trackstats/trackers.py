from datetime import date, timedelta, datetime

from django.db import models

from .models import Period, Statistic


class ObjectsByDateTracker(object):
    date_field = 'date'
    aggr_op = models.Count
    aggr_field = 'pk'
    metric = None
    period = None
    subject = None
    subject_model = None
    subject_field = None


    def __init__(self, **kwargs):
        for prop, val in kwargs.items():
            setattr(self, prop, val)
        assert self.subject is None or self.subject_field is None
        if self.subject_field is None:
            self.subject = Statistic.objects.any_subject(
                self.metric,
                self.subject)
        else:
            assert self.subject_model

    def get_start_date(self, qs):
        most_recent_kwargs = {
            'metric': self.metric,
            'period': self.period}
        if self.subject_model:
            most_recent_kwargs[
                'subject_type'] = ContentType.objects.get_for_model(
                    self.subject_model)
        else:
            most_recent_kwargs['subject'] = self.subject
        last_stat = Statistic.objects.most_recent(**most_recent_kwargs)
        if last_stat:
            start_date = last_stat.date
        else:
            first_instance = qs.order_by(self.date_field).first()
            if first_instance is None:
                # No data
                return
            start_date = getattr(first_instance, self.date_field)
        if start_date and isinstance(start_date, datetime):
            start_date = start_date.date()
        return start_date

    def track(self, qs):
        to_date = date.today()
        start_date = self.get_start_date(qs)
        if not start_date:
            return
        if self.period == Period.LIFETIME:
            # Intentionally recompute last stat, as we may have computed
            # that the last time when the day was not over yet.
            upto_date = start_date
            while upto_date != to_date:
                filter_kwargs = {
                    self.date_field + '__year__lte': upto_date.year,
                    self.date_field + '__month__lte': upto_date.month,
                    self.date_field + '__day__lte': upto_date.day
                }
                n = qs.filter(**filter_kwargs).count()
                Statistic.objects.record(
                    metric=self.metric,
                    value=n,
                    subject=self.subject,
                    period=self.period,
                    date=upto_date)
                upto_date += timedelta(days=1)
        elif self.period == Period.DAY:
            values_fields = ['ts_date']
            if self.subject_model:
                values_fields.append(self.subject_field)
            vals = qs.extra({"ts_date": "DATE({})".format(
                self.date_field)}).values(
                *values_fields).order_by().annotate(ts_n=self.aggr_op(
                    self.aggr_field))
            # TODO: Bulk create
            for val in vals:
                if self.subject_model:
                    subject = self.subject_model(pk=val[suject_field])
                else:
                    subject = self.subject
                Statistic.objects.record(
                    metric=self.metric,
                    value=val['ts_n'],
                    date=val['ts_date'],
                    subject=subject,
                    period=self.period)
        else:
            raise NotImplementedError



class CountObjectsByDateTracker(ObjectsByDateTracker):
    aggr_op = models.Count
    aggr_field = 'pk'
