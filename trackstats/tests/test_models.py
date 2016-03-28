from datetime import date

from django.test import TestCase
from django.contrib.auth import get_user_model

from trackstats.models import (
    Domain,
    Metric,
    StatisticByDate,
    Period,
    StatisticByDateAndObject)

User = get_user_model()


class DomainsTestCase(TestCase):

    def tearDown(self):
        Domain.objects.clear_cache()

    def test_register(self):
        domain = Domain.objects.register(
            ref='shopping',
            name='Shopping')
        self.assertTrue(domain.pk > 0)
        # Otherwise, to make sure we're no longer dealing
        # with our lazy object
        domain = Domain.objects.get(pk=domain.pk)
        self.assertEqual(domain.name, 'Shopping')
        Domain.objects.clear_cache()
        updated_domain = Domain.objects.register(
            ref='shopping',
            name='Ecommerce')
        self.assertEqual(updated_domain.pk, domain.pk)
        domain = Domain.objects.get(pk=domain.pk)
        self.assertEqual(domain.name, 'Ecommerce')


class MetricsTestCase(TestCase):

    def setUp(self):
        self.domain = Domain.objects.register(ref='shopping')

    def tearDown(self):
        Domain.objects.clear_cache()
        Metric.objects.clear_cache()

    def test_register(self):
        metric = Metric.objects.register(
            domain=self.domain,
            ref='order_count',
            name='Order count')
        self.assertTrue(metric.pk > 0)
        # Otherwise, to make sure we're no longer dealing
        # with our lazy object
        metric = Metric.objects.get(pk=metric.pk)
        self.assertEqual(metric.name, 'Order count')
        Metric.objects.clear_cache()
        updated_metric = Metric.objects.register(
            domain=self.domain,
            ref='order_count',
            name='Number of orders')
        updated_metric.pk
        metric = Metric.objects.get(pk=metric.pk)
        self.assertEqual(metric.name, 'Number of orders')


class StatisticsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username='john')
        self.shopping_domain = Domain.objects.register(ref='shopping')
        self.users_domain = Domain.objects.register(ref='users')
        self.order_count = Metric.objects.register(
            domain=self.shopping_domain,
            ref='order_count')
        self.user_count = Metric.objects.register(
            domain=self.users_domain,
            ref='user_count')

    def test_record_today(self):
        record = StatisticByDate.objects.record(
            period=Period.DAY,
            metric=self.user_count,
            value=10)
        self.assertEqual(record.date, date.today())

    def test_record_at_date(self):
        dt = date(2016, 1, 1)
        record = StatisticByDate.objects.record(
            period=Period.DAY,
            metric=self.user_count,
            value=10,
            date=dt)
        self.assertEqual(record.date, dt)

    def test_record_by_date_and_object(self):
        dt = date(2016, 1, 1)
        record = StatisticByDateAndObject.objects.record(
            period=Period.DAY,
            metric=self.user_count,
            value=10,
            object=self.user,
            date=dt)
        self.assertEqual(record.date, dt)
