# -*- coding: utf-8 -*-
"""Sample model module."""

import sqlalchemy as sa
from sqlalchemy import *
from sqlalchemy.orm import mapper, relation
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, Float, Boolean, DateTime

from tg2app.model import DeclarativeBase, metadata, DBSession

from datetime import datetime

import pprint
from ansi2html import Ansi2HTMLConverter
conv = Ansi2HTMLConverter()

class Foreclosure(DeclarativeBase):
    __tablename__ = 'foreclosure_table'

    def fancy_format(self):
        d = dict()
        for prop in sa.orm.class_mapper(Foreclosure).iterate_properties:
            d[prop.key] = str(getattr(self, prop.key))
        return conv.convert(pprint.pformat(d))

    control_no = Column(Unicode(255), nullable=False, primary_key=True)

    book = Column(Unicode(255), nullable=False)
    book_page = Column(Unicode(255), nullable=False)
    filing_date = Column(DateTime, nullable=False)
    formatted_address = Column(Unicode(255), nullable=False)
    grantee = Column(Unicode(255), nullable=False)
    grantor = Column(Unicode(255), nullable=False)
    index_detail = Column(Unicode(255), nullable=False)
    instrument_type = Column(Unicode(255), nullable=False)
    land_description = Column(Unicode(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    map_ready = Column(Boolean, nullable=False)
    property_address = Column(Unicode(255), nullable=False)
    reference_1 = Column(Unicode(255), nullable=False)
    reference_2 = Column(Unicode(255), nullable=False)
    view_image = Column(Unicode(255), nullable=False)

    # Pulled from geo.cityofrochester.gov
    xreffed_owner = Column(Unicode(255), nullable=False)
    xref_updated = Column(DateTime, nullable=False, default=datetime.now)

    # ridiculous details
    acreage = Column(Unicode(255), nullable=False)
    assessed_value = Column(Unicode(255), nullable=False)
    baths = Column(Unicode(255), nullable=False)
    bedrooms = Column(Unicode(255), nullable=False)
    depth = Column(Unicode(255), nullable=False)
    frontage = Column(Unicode(255), nullable=False)
    housing_units = Column(Unicode(255), nullable=False)
    improvements = Column(Unicode(255), nullable=False)
    land_value = Column(Unicode(255), nullable=False)
    landuse = Column(Unicode(255), nullable=False)
    lot_number = Column(Unicode(255), nullable=False)
    rooms = Column(Unicode(255), nullable=False)
    square_footage = Column(Unicode(255), nullable=False)
    stories = Column(Unicode(255), nullable=False)
    #subdivision = Column(Unicode(255), nullable=False)
    year_built = Column(Unicode(255), nullable=False)
    zoning = Column(Unicode(255), nullable=False)


    def csv_headers(self):
        return [
            key for key, value in Foreclosure.__dict__.iteritems()
            if type(getattr(Foreclosure, key)) == InstrumentedAttribute
        ]


    def to_csv(self):
        return "|".join([
            str(getattr(self, attr)) for attr in self.csv_headers()
        ])

    def to_dict(self):
        return dict([(attr, getattr(self, attr))
                     for attr in self.csv_headers()])

    def to_geojson(self):
        d = self.to_dict()
        d['filing_date'] = d['filing_date'].strftime('%m/%d/%Y')
        return d
