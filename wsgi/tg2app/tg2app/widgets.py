import tg2app.model as model
import tw2.core as twc
from tw2.jqplugins.jqgrid import SQLAjqGridWidget
from tw2.jqplugins.ui import DialogWidget, DatePickerWidget
from tw2.slideymenu import MenuWidget
from tw2.polymaps import PolyMap
from tw2.jit import PieChart, AreaChart

import docutils.examples
import urllib

query_js = twc.JSLink(modname=__name__,
                      filename='public/js/jquery.query-2.1.7.js')
modal_js = twc.JSLink(modname=__name__,
                      filename='public/js/modal.js')


class CustomizedDatePicker(DatePickerWidget):
    resources = DatePickerWidget.resources + [query_js]

onselect_tmpl = """function(d, i){
    window.location = 'http://' + location.host + location.pathname + \
        $.query.set('%s', d).toString();
}"""


class FromDateWidget(CustomizedDatePicker):
    id = 'from_date'
    options = {
        'showAnim': 'slideDown',
        'autoSize': True,
        'yearRange': '1989:2011',
        'changeYear': True,
        'onSelect': twc.JSSymbol(onselect_tmpl % 'from_date'),
    }


class ToDateWidget(CustomizedDatePicker):
    id = 'to_date'
    options = {
        'showAnim': 'slideDown',
        'autoSize': True,
        'yearRange': '1989:2011',
        'changeYear': True,
        'onSelect': twc.JSSymbol(onselect_tmpl % 'to_date'),
    }


def foreclosure_readme():
    """ Ridiculous """
    root = '/'.join(__file__.split('/')[:-2])
    fname = root + '/README.rst'
    with open(fname, 'r') as f:
        readme = f.read()
        return docutils.examples.html_body(unicode(readme))


class ReadmeDialog(DialogWidget):
    id = 'foreclosure_dialog'
    options = {
        'title': 'README.rst',
        'autoOpen': False,
        'width': 1000
    }
    value = foreclosure_readme()


class ForeclosureGrid(SQLAjqGridWidget):
    id = 'foreclosure-loggrid'
    entity = model.Foreclosure
    excluded_columns = [
        'index_detail',
        'book_page',
        'book',
        'instrument_type',
        'land_description',
        'latitude',
        'longitude',
        'map_ready',
        'reference_1',
        'reference_2',
        'view_image',
    ]
    datetime_format = "%x"

    prmFilter = {'stringResult': True, 'searchOnEnter': False}

    options = {
        'pager': 'foreclosure-loggrid_pager',
        'url': '/jqgrid/',
        'rowNum': 30,
        'rowList': [30, 100, 500, 1000, 2000, 5000],
        'viewrecords': True,
        'imgpath': 'scripts/jqGrid/themes/green/images',
        'shrinkToFit': True,
        'height': 'auto',
    }


def loading_dialog(href, pass_query_string=True):
    target = "'%s'" % href
    if pass_query_string:
        target = target + " + $.query.toString()"
    return "javascript:loadingDialog(%s);" % target


class MainMenu(MenuWidget):
    resources = MenuWidget.resources + [modal_js, query_js]
    id = 'foreclosure-menu'
    items = [
        {
            'label': 'Map',
            'href': loading_dialog('/map'),
        }, {
            'label': 'Grid',
            'href': loading_dialog('/grid', pass_query_string=False),
        }, {
            'label': 'By Grantor',
            'href': loading_dialog('/grantor'),
        }, {
            'label': 'By Grantee',
            'href': loading_dialog('/grantee'),
        }, {
            'label': 'By Weekday',
            'href': loading_dialog('/dayofweek'),
        }, {
            'label': 'By Day',
            'href': loading_dialog('/day'),
        }, {
            'label': 'By Month',
            'href': loading_dialog('/month'),
        }, {
            'label': 'By Year',
            'href': loading_dialog('/year'),
        }, {
            'label': 'Graph',
            'href': loading_dialog('/graph'),
        }, {
            'label': 'Export (.csv)',
            'href': loading_dialog('/export.csv', pass_query_string=False),
        }, {
            'label': 'RSS (atom)',
            'href': loading_dialog('/atom1', pass_query_string=False),
        }, {
            'label': 'About',
            'href': "javascript:(function(){$('#foreclosure_dialog').dialog('open');})();"
        }
    ]


class JitCustomized(object):
    id = 'foreclosure_widget'
    width = '1000'
    height = '600'
    backgroundcolor = '#f9f9f9'
    Label = {
        'size': 12,
        'color': '#3e3e3e',
    }


class ForeclosureArea(JitCustomized, AreaChart):
    pass


class ForeclosurePie(JitCustomized, PieChart):
    sliceOffset = 10


custom_polymaps_css = twc.CSSLink(
    modname=__name__,
    filename='public/css/custom-polymaps.css')


class ForeclosureMap(PolyMap):
    id = 'foreclosure_map'
    data_url = '/foreclosure_map_data/'

    # Both specify the css_class AND include your own custom css file that
    # specifies what it looks like.
    css_class = 'sample-tw2-polymaps-container-1'
    resources = PolyMap.resources + [custom_polymaps_css]

    # 10.00/43.1164/-437.5940
    zoom = 10.0
    center_latlon = {'lat': 43.1164, 'lon': -437.5940}

    # Let the user control the map
    interact = True

    # Deep-linking
    hash = True

    # You should get your own one of these at http://cloudmade.com/register
    cloudmade_api_key = "1a1b06b230af4efdbb989ea99e9841af"

    # To style the map tiles
    cloudmade_tileset = 'midnight-commander'

    properties_callback = """
    function (_layer) {
        _layer.on("load", org.polymaps.stylist()
            .title(function(d) {
                return "(" + d.properties.filing_date + ")  " + d.properties.formatted_address;
            }));
        return _layer
    }"""

    from_date = twc.Param()
    to_date = twc.Param()

    def prepare(self):
        self.data_url = '/foreclosure_map_data?' + urllib.urlencode({
            'from_date':self.from_date,
            'to_date':self.to_date,
        })
        super(ForeclosureMap, self).prepare()

