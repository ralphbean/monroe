import tg2app.model as model
from tw2.jqplugins.jqgrid import SQLAjqGridWidget

class ForeclosureGrid(SQLAjqGridWidget):
    id = 'awesome-loggrid'
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
        'pager': 'awesome-loggrid_pager',
        'url': '/jqgrid/',
        'rowNum':15,
        'rowList':[15,150, 1500],
        'viewrecords':True,
        'imgpath': 'scripts/jqGrid/themes/green/images',
        'shrinkToFit': True,
        'height': 'auto',
    }

