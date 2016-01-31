import random
from collections import Counter
from datetime import date, timedelta, datetime, time

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from trackstats.models import Domain, Metric, Statistic, Period
from trackstats.trackers import CountObjectsByDateTracker

from trackstats.tests.models import Comment


class TrackersTestCase(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.users_domain = Domain.objects.register(ref='users')
        self.user_count = Metric.objects.register(
            domain=self.users_domain,
            ref='user_count')
        self.expected_signups = {}
        dt = date.today() - timedelta(days=7)
        signups_lifetime = 0
        while dt != date.today():
            signups_on_day = random.randint(1, 5)
            signups_lifetime += signups_on_day
            date_joined = timezone.make_aware(
                datetime.combine(
                    dt,
                    time()))
            self.expected_signups[dt] = {
                'lifetime': signups_lifetime,
                'day': signups_on_day
            }
            for i in range(signups_on_day):
                self.User.objects.create(
                    username='user{}_{}'.format(dt, i),
                    date_joined=date_joined)
            dt += timedelta(days=1)
        self.expected_signups[date.today()] = self.expected_signups[
            date.today() - timedelta(days=1)]

    def test_count_lifetime(self):
        CountObjectsByDateTracker(
            period=Period.LIFETIME,
            metric=self.user_count,
            date_field='date_joined').track(self.User.objects.all())
        stats = Statistic.objects.narrow(
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
        stats = Statistic.objects.narrow(
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


class SubjectTrackersTestCase(TestCase):

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
        while dt.date() <= date.today():
            for user in users:
                comment_count = random.randint(1, 5)
                for i in range(comment_count):
                    Comment.objects.create(
                        timestamp=dt,
                        user=user)
                self.expected_lifetime[
                    (dt.date(), user.pk)] = self.expected_lifetime[(
                        dt.date() - timedelta(days=1),
                        user.pk)] + comment_count
                self.expected_daily[(dt.date(), user.pk)] = comment_count
            dt += timedelta(days=1)

    def test_count_lifetime(self):
        CountObjectsByDateTracker(
            period=Period.LIFETIME,
            metric=self.comment_count,
            subject_model=self.User,
            subject_field='user',
            date_field='timestamp').track(Comment.objects.all())
        stats = Statistic.objects.narrow(
            metrics=[self.comment_count],
            period=Period.LIFETIME)
        for stat in stats:
            self.assertEqual(
                self.expected_lifetime[
                    (stat.date, stat.subject.pk)],
                stat.value)
        self.assertEqual(
            stats.count(),
            len(self.users) * (7 + 1))

    def test_count_daily(self):
        CountObjectsByDateTracker(
            period=Period.DAY,
            metric=self.comment_count,
            subject_model=self.User,
            subject_field='user',
            date_field='timestamp').track(Comment.objects.all())
        stats = Statistic.objects.narrow(
            metric=self.comment_count,
            period=Period.DAY)
        for stat in stats:
            self.assertEqual(
                self.expected_daily[(stat.date, stat.subject.pk)],
                stat.value)
        self.assertEqual(
            stats.count(),
            len(self.users) * (7 + 1))
