=============================
Bienvenido/a a django-trackstats!
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

Mantén un registro de tus estadísticas.

Código fuente
  http://github.com/pennersr/django-trackstats


Casos de uso
========

- Necesitas una solución elegante para almacenar estadísticas de una manera genérica y estructural.

- Necesitas desnormalizar los resultados de varias consultas agregadas (aggregation).

- Necesitas tener acceso a las estadísticas almacenadas a nivel de aplicación.

Entonces, el foco es puramente en almacenar estadísticas para utilizar más tarde en
su aplicación. Otras funciones, cómo crear gráficos, reportes, OLAP, constructores de
consultas (query builders), slicing y dicing, integración con ``Datadog`` y similares
están todas más allá del alcance de ``django-trackstats``.


Conceptos
========

Los siguientes conceptos son utilizados:

Métrica (Metric)
  Una pieza de información de la cual hacer un registro. Por ejemplo, 
  "Cantidad de órdenes", o "Cantidad de usuarios registrados".

Dominio (Domain)
  Las métricas están organizadas en grupos, y cada grupo es un Dominio.
  Por ejemplo, puedes tener un dominio "shopping" con métricas como "Cantidad de
  órdenes", "Productos vendidos", "Productos vistos", y un dominio "usuarios"
  con métricas "Cantidad de inicios de sesión", "Cantidad de registros". O, en caso
  de que estés haciendo estadísticas externas de redes sociales, puedes introducir un
  dominio "Twitter", con una métrica "Cantidad de seguidores".

Estadística (Statistic)
  Usado para almacenar los valores por fecha, para una métrica en específico.

Periodo (Period)
  El período de tiempo que contiene el valor. Por ejemplo, 
  puedes seguir números acumulativos para siempre (``Period.LIFETIME``), 
  guardar valores incrementales diariamente (``Period.DAY``), o guardar 
  registro de un número cambiante en los últimos 7 días (``Period.DAY``).

IDs de referencia
  Los dominios y las métricas deben ser asignados un ID único (de tipo
  ``string``). Razón (Rationale): Tener una referencia legible por humanos
  y no basada en IDs es esencial tan pronto como vayas a exportar tus 
  estadísticas.


Instalación
============

Utilizando pip:

.. code:: bash
   
    pip install git+https://github.com/pennersr/django-trackstats.git

Utilizando poetry:

.. code:: bash

    poetry add git+https://github.com/pennersr/django-trackstats.git

Then add ``trackstats`` to your ``INSTALLED_APPS`` setting

.. code:: python

    INSTALLED_APPS = [
        'trackstats',
    ]

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
