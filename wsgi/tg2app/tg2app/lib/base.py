# -*- coding: utf-8 -*-

"""The base Controller API."""

from tg import TGController, tmpl_context
from tg.render import render
from tg import request
from tg.i18n import ugettext as _, ungettext
import tg2app.model as model

from tw2.jqplugins.ui import set_ui_theme_name

from tg2app.widgets import MainMenu, ReadmeDialog, FromDateWidget, ToDateWidget

import urllib2

__all__ = ['BaseController']


class BaseController(TGController):
    """
    Base class for the controllers in the application.

    Your web application should have one of these. The root of
    your application is used to compute URLs used by your app.

    """

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # TGController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']

        request.identity = request.environ.get('repoze.who.identity')
        tmpl_context.identity = request.identity

        tmpl_context.menu_widget = MainMenu
        tmpl_context.dialog_widget = ReadmeDialog
        tmpl_context.from_date_widget = FromDateWidget
        tmpl_context.to_date_widget = ToDateWidget
        set_ui_theme_name('excite-bike')

        return TGController.__call__(self, environ, start_response)
