=============================
Welcome to django-trackstats!
=============================

.. image:: https://badge.fury.io/py/django-trackstats.svg
   :target: http://badge.fury.io/py/django-trackstats

.. image:: https://travis-ci.org/pennersr/django-trackstats.svg
   :target: http://travis-ci.org/pennersr/django-trackstats

.. image:: https://img.shields.io/pypi/v/django-trackstats.svg
   :target: https://pypi.python.org/pypi/django-trackstats

.. image:: https://coveralls.io/repos/pennersr/django-trackstats/badge.svg?branch=master
   :alt: Coverage Status
   :target: https://coveralls.io/r/pennersr/django-trackstats

.. image:: https://pennersr.github.io/img/bitcoin-badge.svg
   :target: https://blockchain.info/address/1AJXuBMPHkaDCNX2rwAy34bGgs7hmrePEr

Keep track of your statistics.

Source code
  http://github.com/pennersr/django-trackstats


Use Case
========

- You need an elegant solution for storing statistics in a generic and structural fashion.

- You need to denormalize the results of various aggregated queries.

- You require access to the stored statistics within your application layer.

So, the focus is purely on storing statistics for use within your application later
on. Other features, such as charting, reports, OLAP, query builders, slicing &
dicing, integration with ``Datadog`` and the likes are all beyond scope.


Concepts
========

The following concepts are used:

Metric
  A piece of information to keep track of. For example, "Order count",
  or "Number of users signed up".

Domain
  Metrics are organized in groups, each group is called a domain. For
  example you can have a "shopping" domain with metrics such as "Order
  count", "Items sold", "Products viewed", and a "users" domain with
  "Login count", "Signup count". Or, in case you are tracking external
  statistics from social networks, you may introduce a "Twitter"
  domain, and metrics "Followers count".

Statistic
  Used to store the actual values by date, for a specific metric.

Period
  The time period for which the stored value holds. For example, you
  can keep track of cumulative, all-time, numbers (`Period.LIFETIME`),
  store incremental values on a daily basis (`Period.DAY`), or keep
  track of a rolling count for the last 7 days (`Period.WEEK`).

Reference IDs
  Domains and metrics must be assigned unique reference IDs (of type
  string). Rationale: Having a human readable, non PK based, reference
  is esential as soon as you are going to export statistics.


Usage
=====

First, setup your domains:

.. code:: python

    from trackstats.models import Domain

    Domain.objects.SHOPPING = Domain.objects.register(
        ref='shopping',
        name='Shopping')
    Domain.objects.USERS = Domain.objects.register(
        ref='users',
        name='Users')
    Domain.objects.TWITTER = Domain.objects.register(
        ref='twitter',
        name='Twitter')

Define a few metrics:

.. code:: python

    from trackstats.models import Domain, Metric

    Metric.objects.SHOPPING_ORDER_COUNT = Metric.objects.register(
        domain=Domain.objects.SHOPPING,
        ref='order_count',
        name='Number of orders sold')
    Metric.objects.USERS_USER_COUNT = Metric.objects.register(
        domain=Domain.objects.USERS,
        ref='user_count',
        name='Number of users signed up')
    Metric.objects.TWITTER_FOLLOWER = Metric.objects.register(
        # Matches Twitter API
        ref='followers_count',
        domain=Domain.objects.TWITTER)

Now, let's store some one-off statistics:

.. code:: python

    from trackstats.models import StatisticByDate, Domain, Metric, Period

    # All-time, cumulative, statistic
    n = Order.objects.all().count()
    StatisticByDate.objects.record(
        metric=Metric.objects.SHOPPING_ORDER_COUNT,
        value=n,
        period=Period.LIFETIME)

    # Users signed up, at a specific date
    dt = date.today()
    n = User.objects.filter(
        date_joined__day=dt.day,
        date_joined__month=dt.month,
        date_joined__year=dt.year).count()
    StatisticByDate.objects.record(
        metric=Metric.objects.USERS_USER_COUNT,
        value=n,
        period=Period.DAY)

Creating code to store statistics yourself can be a tedious job.
Luckily, a few shortcuts are available to track statistics without
having to write any code yourself.

Consider you want to keep track of the number of comments created on a
daily basis:

.. code:: python

    from trackstats.trackers import CountObjectsByDateTracker

    CountObjectsByDateTracker(
        period=Period.DAY,
        metric=Metric.objects.COMMENT_COUNT,
        date_field='timestamp').track(Comment.objects.all())

Or, in case you want to track the number of comments, per user, on a daily
basis:

.. code:: python

    CountObjectsByDateAndObjectTracker(
        period=Period.DAY,
        metric=Metric.objects.COMMENT_COUNT,
        # comment.user points to a User
        object_model=User,
        object_field='user',
        # Comment.timestamp is used for grouping
        date_field='timestamp').track(Comment.objects.all())


Models
======

The ``StatisticByDate`` model represents statistics grouped by date --
the most common use case.

Another common use case is to group by both date and some other object
(e.g. a user, category, site).  For this, use
``StatisticByDateAndObject``. It uses a generic foreign key.

If you need to group in a different manner, e.g. by country, province
and date, you can use the ``AbstractStatistic`` base class to build just
that.


Cross-Selling
=============

If you like this, you may also like:

- django-allauth: https://github.com/pennersr/django-allauth
- netwell: https://github.com/pennersr/netwell
