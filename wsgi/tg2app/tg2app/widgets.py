import tg2app.model as model
import tw2.core as twc
from tw2.jqplugins.jqgrid import SQLAjqGridWidget
from tw2.slideymenu import MenuWidget

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
    datetime_format = "%x %X"

    prmFilter = {'stringResult': True, 'searchOnEnter': False}

    options = {
        'pager': 'foreclosure-loggrid_pager',
        'url': '/jqgrid/',
        'rowNum':15,
        'rowList':[15,150, 1500],
        'viewrecords':True,
        'imgpath': 'scripts/jqGrid/themes/green/images',
        'shrinkToFit': True,
        'height': 'auto',
    }

def loading_dialog(href):
    return "javascript:loadingDialog('%s');" % href

modal_js = twc.JSLink(modname=__name__,
                      filename='public/js/modal.js')

class MainMenu(MenuWidget):
    resources = MenuWidget.resources + [modal_js]
    id='foreclosure-menu'
    items=[
        {
            'label' : 'Grid',
            'href' : loading_dialog('/grid'),
        },{
            'label' : 'By Time',
            'href' : loading_dialog('/time'),
        },{
            'label' : 'By Grantor/Grantee',
            'href' : loading_dialog('/grantor'),
        },{
            'label' : 'Graph',
            'href' : loading_dialog('/graph'),
        }, {
            'label' : 'Map',
            'href' : loading_dialog('/map'),
        },{
            'label' : 'Export (.csv)',
            'href' : loading_dialog('/export'),
        }
    ]
