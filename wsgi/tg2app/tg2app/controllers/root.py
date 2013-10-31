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

from sqlalchemy import and_, desc

import datetime
import geojson
import simplejson
import urllib

from tg2app.scrapers.propertyinfo import ForeclosureScraper
from tgscheduler.scheduler import add_single_task

# Stuff for the atom feed
from tg.controllers import CUSTOM_CONTENT_TYPE
from webhelpers.feedgenerator import Atom1Feed
from pylons import response

__all__ = ['RootController']

fmt = '%m/%d/%Y'

def make_query(**kw):
    if not 'from_date' in kw:
        kw['from_date'] = datetime.datetime(1989, 1, 1).strftime(fmt)
        redirect(current_url() + '?' + urllib.urlencode(kw))

    if not 'to_date' in kw:
        kw['to_date'] = datetime.datetime.now().strftime(fmt)
        redirect(current_url() + '?' + urllib.urlencode(kw))

    from_date = datetime.datetime.strptime(kw['from_date'], fmt)
    to_date = datetime.datetime.strptime(kw['to_date'], fmt)

    return model.Foreclosure.query.filter(and_(
        model.Foreclosure.filing_date >= from_date,
        model.Foreclosure.filing_date <= to_date
    ))


def current_url():
    return request.application_url + request.environ['PATH_INFO']

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

    @expose(content_type=CUSTOM_CONTENT_TYPE)
    def atom1( self ):
        """Produce an atom-1.0 feed via feedgenerator module"""
        feed = Atom1Feed(
            title=u"Latest notices of pendency",
            link=current_url(),
            description=u"These are the latest foreclosures pulled together by the scraper",
            language=u"en",
        )

        latest = model.Foreclosure.query.order_by(
            desc(model.Foreclosure.filing_date)
        ).limit(40).all()

        for closure in latest:
            feed.add_item(title=closure.formatted_address,
                          link=u"http://monroe-threebean.rhcloud.com/",
                          description=closure.fancy_format())

        response.content_type = 'application/atom+xml'
        return feed.writeString('utf-8')

    @expose('')
    def make_xrefs_happen(self):
        add_single_task(
            action=ForeclosureScraper().update_xrefs,
            taskname="xrefs_for_life_unscheduled",
            initialdelay=0,
        )

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
    def foreclosure_map_data(self, **kw):
        json = geojson.FeatureCollection(
            features=[
                geojson.Feature(
                    geometry=geojson.Point([fc.longitude, fc.latitude]),
                    id=fc.control_no,
                    properties=fc.to_geojson(),
                ) for fc in make_query(**kw).all() if fc.map_ready
            ]
        )
        return simplejson.loads(geojson.dumps(json))

    @expose('tg2app.templates.widget')
    def map(self, **kw):
        make_query(**kw)
        return dict(widget=ForeclosureMap(**kw), title="Foreclosures")

    @expose(content_type='text/csv')
    def export(self):
        header = '|'.join(model.Foreclosure.query.first().csv_headers()) + '\n'
        closures = model.Foreclosure.query.all()
        return header + '\n'.join([closure.to_csv() for closure in closures])

    @expose('tg2app.templates.widget')
    def graph(self, **kw):

        base_query = make_query(**kw)
        bucket = {}
        step = datetime.timedelta(days=365)
        for date in date_range(
            datetime.datetime.strptime(kw['from_date'], fmt),
            datetime.datetime.strptime(kw['to_date'], fmt),
            step=365,
        ):
            query = base_query.filter(
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

        return dict(widget=graph, title="Number of foreclosures")

    @expose('json')
    def jqgrid(self, *args, **kwargs):
        return ForeclosureGrid.request(request).body

    @expose('tg2app.templates.widget_nodates')
    def grid(self):
        return dict(widget=ForeclosureGrid)

    @expose('tg2app.templates.widget')
    def grantor(self, **kw):
        return self._granted('grantor', **kw)

    @expose('tg2app.templates.widget')
    def grantee(self, **kw):
        return self._granted('grantee', **kw)

    @expose('tg2app.templates.widget')
    def day(self, **kw):
        return self._time('day', **kw)

    @expose('tg2app.templates.widget')
    def month(self, **kw):
        return self._time('month', **kw)

    @expose('tg2app.templates.widget')
    def year(self, **kw):
        return self._time('year', **kw)

    @expose('tg2app.templates.widget')
    def dayofweek(self, **kw):
        return self._time('dayofweek', **kw)

    @expose()
    def health(self, **kw):
        return "I am OK"

    def _granted(self, attr, **kw):
        if not attr in ['grantor', 'grantee']:
            redirect('/')

        if not 'top' in kw:
            kw['top'] = 5
            redirect(current_url() + '?' + urllib.urlencode(kw))

        try:
            top = int(kw['top'])
        except TypeError:
            redirect('/' + attr)

        closures = make_query(**kw).all()

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

        return dict(widget=pie, title="Top %i mortgage grantors" % top)

    def _time(self, attr, **kw):
        lookup = {
            'day': '%d',
            'month': '%b',
            'year': '%Y',
            'dayofweek': '%a',
        }

        if attr not in lookup.keys():
            redirect('/')

        closures = make_query(**kw).all()

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

        return dict(widget=pie, title="Number of foreclosures by %s" % attr)
