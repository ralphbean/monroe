# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from tg.i18n import ugettext as _, lazy_ugettext as l_
from repoze.what import predicates

from tg2app.lib.base import BaseController
from tg2app.model import DBSession, metadata
from tg2app import model

from tg2app.scrapers.propertyinfo import date_range  # A nice utility.
from tg2app.widgets import (
    ForeclosureGrid, ForeclosurePie, ForeclosureArea, ForeclosureMap
)
import tw2.jit

from sqlalchemy import and_

import datetime
import geojson
import simplejson

from tg2app.scrapers.propertyinfo import ForeclosureScraper
from tgscheduler.scheduler import add_single_task

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the tg2app application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """

    @expose('')
    def make_wayback_happen(self):
        add_single_task(
            action=ForeclosureScraper().go_way_back,
            taskname="gowayback_unscheduled",
            initialdelay=0,
        )

    @expose('')
    def make_scrape_happen(self):
        ForeclosureScraper().scrape_data()


    @expose('tg2app.templates.index')
    def index(self):
        """Handle the front-page."""
        redirect('/graph')

    @expose('json')
    def foreclosure_map_data(self):
        json = geojson.FeatureCollection(
            features=[
                geojson.Feature(
                    geometry=geojson.Point([fc.longitude, fc.latitude])
                ) for fc in model.Foreclosure.query.all() if fc.map_ready
            ]
        )
        return simplejson.loads(geojson.dumps(json))

    @expose('tg2app.templates.widget')
    def map(self):
        return dict(widget=ForeclosureMap)


    @expose(content_type='text/csv')
    def export(self):
        header = '|'.join(model.Foreclosure.query.first().csv_headers()) + '\n'
        closures = model.Foreclosure.query.all()
        return header + '\n'.join([closure.to_csv() for closure in closures])

    @expose('tg2app.templates.widget')
    def graph(self, *args, **kwargs):

        bucket = {}
        step = datetime.timedelta(days=365)
        for date in date_range(
            datetime.datetime(1989, 1, 1),
            datetime.datetime.now(),
            step=365,
        ):
            query = model.Foreclosure.query.filter(
                and_(
                    model.Foreclosure.filing_date >= date,
                    model.Foreclosure.filing_date < date + step
                ))
            bucket[(date+step).strftime("%Y")] = query.count()

        items = bucket.items()
        items.sort(lambda a, b: cmp(a[0], b[0]))

        data = {
            'labels' : ['Foreclosures'],
            'values' : [
                {
                    'label': key,
                    'values': [value],
                } for key, value in items
            ]
        }

        graph = ForeclosureArea(data=data)

        return dict(widget=graph)

    @expose('json')
    def jqgrid(self, *args, **kwargs):
        return ForeclosureGrid.request(request).body

    @expose('tg2app.templates.widget')
    def grid(self):
        return dict(widget=ForeclosureGrid)

    @expose('tg2app.templates.widget')
    def grantor(self, top=5):
        return self._granted('grantor', top)

    @expose('tg2app.templates.widget')
    def grantee(self, top=5):
        return self._granted('grantee', top)

    @expose('tg2app.templates.widget')
    def day(self):
        return self._time('day')

    @expose('tg2app.templates.widget')
    def month(self):
        return self._time('month')

    @expose('tg2app.templates.widget')
    def year(self):
        return self._time('year')

    @expose('tg2app.templates.widget')
    def dayofweek(self):
        return self._time('dayofweek')

    def _granted(self, attr, top):
        if not attr in ['grantor', 'grantee']:
            redirect('/')

        try:
            top = int(top)
        except TypeError:
            redirect('/' + attr)

        closures = model.Foreclosure.query.all()

        bucket = {}
        for c in closures:
            bucket[getattr(c, attr)] = bucket.get(getattr(c, attr), 0) + 1

        items = bucket.items()
        items.sort(lambda a, b: cmp(b[1], a[1]))
        items = [(item[0] + "(%i)" % item[1], item[1]) for item in items]

        bucket = dict(items[:top])
        other_count = sum([item[1] for item in items[top:]])
        bucket['OTHER (%i)' % other_count] = other_count

        data = {
            'labels' : ['Foreclosures'],
            'values' : [
                {
                    'label': key,
                    'values': [value],
                } for key, value in bucket.iteritems()
            ]
        }

        pie = ForeclosurePie(data=data)

        return dict(widget=pie)

    def _time(self, attr):
        lookup = {
            'day': '%d',
            'month': '%b',
            'year': '%Y',
            'dayofweek': '%a',
        }

        if attr not in lookup.keys():
            redirect('/')

        closures = model.Foreclosure.query.all()

        fmt = lookup[attr]
        bucket = {}
        for c in closures:
            bucket[c.filing_date.strftime(fmt)] = \
                    bucket.get(c.filing_date.strftime(fmt), 0) + 1

        items = bucket.items()
        items = [(item[0] + "(%i)" % item[1], item[1]) for item in items]

        bucket = dict(items)

        data = {
            'labels' : ['Foreclosures'],
            'values' : [
                {
                    'label': key,
                    'values': [value],
                } for key, value in bucket.iteritems()
            ]
        }

        pie = ForeclosurePie(data=data)

        return dict(widget=pie)
