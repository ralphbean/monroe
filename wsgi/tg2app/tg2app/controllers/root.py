# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from tg.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController
from repoze.what import predicates

from tg2app.lib.base import BaseController
from tg2app.model import DBSession, metadata
from tg2app import model
from tg2app.controllers.secure import SecureController

from tg2app.controllers.error import ErrorController

from tg2app.widgets import ForeclosureGrid
import tw2.jit

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
    secc = SecureController()

    admin = AdminController(model, DBSession, config_type=TGAdminConfig)

    error = ErrorController()

    @expose('tg2app.templates.index')
    def index(self):
        """Handle the front-page."""
        redirect('/grid')

    @expose('json')
    def jqgrid(self, *args, **kwargs):
        return ForeclosureGrid.request(request).body

    @expose('tg2app.templates.widget')
    def grid(self):
        return dict(widget=ForeclosureGrid)

    @expose('tg2app.templates.widget')
    def grantor(self, top=5):
        try:
            top = int(top)
        except TypeError:
            redirect('/grantor')

        closures = model.Foreclosure.query.all()

        bucket = {}
        for c in closures:
            bucket[c.grantor] = bucket.get(c.grantor, 0) + 1

        items = bucket.items()
        items.sort(lambda a, b: cmp(b[1], a[1]))

        bucket = dict(items[:top])
        bucket['OTHER'] = sum([item[1] for item in items[top:]])

        p_data = {
            'labels' : ['Foreclosures'],
            'values' : [
                {
                    'label': key,
                    'values': [value],
                } for key, value in bucket.iteritems()
            ]
        }

        class pie(tw2.jit.PieChart):
            id = 'foreclosure_pie'
            data = p_data
            sliceOffset = 5

        return dict(widget=pie)
