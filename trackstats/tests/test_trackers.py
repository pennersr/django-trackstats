import random
from collections import Counter
from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from trackstats.models import (
    Domain,
    Metric,
    StatisticByDate,
    StatisticByDateAndObject,
    Period)
from trackstats.trackers import (
    CountObjectsByDateTracker,
    CountObjectsByDateAndObjectTracker)

from trackstats.tests.models import Comment


def to_date(dt):
    return timezone.make_naive(dt).date()


class TrackersTestCase(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.users_domain = Domain.objects.register(ref='users')
        self.user_count = Metric.objects.register(
            domain=self.users_domain,
            ref='user_count')
        self.expected_signups = {}
        dt = timezone.now() - timedelta(days=7)
        # TODO: Add timezone testing
        # dt.replace(hour=2)
        signups_lifetime = 0
        while to_date(dt) != date.today():
            signups_on_day = random.randint(1, 5)
            signups_lifetime += signups_on_day
            self.expected_signups[to_date(dt)] = {
                'lifetime': signups_lifetime,
                'day': signups_on_day
            }
            for i in range(signups_on_day):
                self.User.objects.create(
                    username='user{}_{}'.format(to_date(dt), i),
                    date_joined=dt)
            dt += timedelta(days=1)
        self.expected_signups[date.today()] = self.expected_signups[
            date.today() - timedelta(days=1)]

    def test_count_lifetime(self):
        CountObjectsByDateTracker(
            period=Period.LIFETIME,
            metric=self.user_count,
            date_field='date_joined').track(self.User.objects.all())
        stats = StatisticByDate.objects.narrow(
            metrics=[self.user_count],
            period=Period.LIFETIME)
        for stat in stats:
            self.assertEqual(
                stat.value,
                self.expected_signups[stat.date]['lifetime'])
        self.assertEqual(
            stats.count(),
            len(self.expected_signups))

    def test_count_daily(self):
        CountObjectsByDateTracker(
            period=Period.DAY,
            metric=self.user_count,
            date_field='date_joined').track(self.User.objects.all())
        stats = StatisticByDate.objects.narrow(
            metrics=[self.user_count],
            period=Period.DAY)
        for stat in stats:
            self.assertEqual(
                stat.value,
                self.expected_signups[stat.date]['day'])
        self.assertEqual(
            stats.count(),
            # Today is not in there due to group by.
            len(self.expected_signups) - 1)


class ObjectTrackersTestCase(TestCase):

    def setUp(self):
        self.User = get_user_model()
        domain = Domain.objects.register(ref='comments')
        self.comment_count = Metric.objects.register(
            domain=domain,
            ref='comment_count')
        users = self.users = [
            self.User.objects.create(username='user{}'.format(i))
            for i in range(5)]
        dt = timezone.now() - timedelta(days=7)
        self.expected_daily = {}
        self.expected_lifetime = Counter()
        while to_date(dt) <= date.today():
            for user in users:
                comment_count = random.randint(1, 5)
                for i in range(comment_count):
                    Comment.objects.create(
                        timestamp=dt,
                        user=user)
                self.expected_lifetime[
                    (to_date(dt), user.pk)] = self.expected_lifetime[(
                        to_date(dt) - timedelta(days=1),
                        user.pk)] + comment_count
                self.expected_daily[(to_date(dt), user.pk)] = comment_count
            dt += timedelta(days=1)

    def test_count_lifetime(self):
        CountObjectsByDateAndObjectTracker(
            period=Period.LIFETIME,
            metric=self.comment_count,
            object_model=self.User,
            object_field='user',
            date_field='timestamp').track(Comment.objects.all())
        stats = StatisticByDateAndObject.objects.narrow(
            metrics=[self.comment_count],
            period=Period.LIFETIME)
        for stat in stats:
            self.assertEqual(
                self.expected_lifetime[
                    (stat.date, stat.object.pk)],
                stat.value)
        self.assertEqual(
            stats.count(),
            len(self.expected_lifetime))

    def test_count_daily(self):
        CountObjectsByDateAndObjectTracker(
            period=Period.DAY,
            metric=self.comment_count,
            object_model=self.User,
            object_field='user',
            date_field='timestamp').track(Comment.objects.all())
        stats = StatisticByDateAndObject.objects.narrow(
            metric=self.comment_count,
            period=Period.DAY)
        for stat in stats:
            self.assertEqual(
                self.expected_daily[(stat.date, stat.object.pk)],
                stat.value)
        self.assertEqual(
            stats.count(),
            len(self.expected_daily))
