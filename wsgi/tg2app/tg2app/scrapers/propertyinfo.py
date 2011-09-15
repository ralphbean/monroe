# This file is part of CIVX.
#
# CIVX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CIVX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CIVX.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2008-2010, CIVX, Inc.
"""
:mod:`civx.scrapers.propertyinfo` -- The PropertyInfo Scraper
================================================================

This scraper pulls down the latest data from propertyinfo.com
and passes it off for work.

..moduleauthor:: Ralph Bean <ralph.bean@gmail.com>
"""

import cookielib
import datetime
import logging
import mechanize
import os
import re

from BeautifulSoup import BeautifulSoup

import civx

from civx.utils import get_civx_config
from civx.utils import geocode
from civx.model import PropertyInfoForeclosure
from civx.scrapers import Scraper

log = logging.getLogger('moksha.hub')
config = get_civx_config()


class ForeclosureScraper(Scraper):
    """Property Info Mortgage Foreclosure Scraper """
    topics = ['Economy', 'Foreclosures', 'PropertyInfo']
    models = [PropertyInfoForeclosure]
    git_repo = 'propertyinfoforeclosure'
    frequency = datetime.timedelta(days=1)
    now = True
    base = 'https://gov.propertyinfo.com'
    headers = [
            'Index Detail',
            'View Image',
            'Filing Date',
            'Instrument Type',
            'Property Address',
            'Book',
            'Book Page',
            'Grantor',
            'Grantee',
            'Reference 1',
            'Reference 2',
            'Land Description',
            'Control No',
            # These are pulled during scrape from Google Maps
            'Map Ready',
            'Formatted Address',
            'Latitude',
            'Longitude',
    ]

    def scrape_data(self, beg_date=None, end_date=None):
        # Some initialization
        data = []
        fmt = '%m/%d/%Y'

        # Default if not otherwise specified
        if not end_date:
            end_date = datetime.datetime.today()
        if not beg_date:
            beg_date = end_date - datetime.timedelta(days=3)

        # Sanity
        if (end_date <= beg_date):
            raise ValueError("end date must come after begin date")
        if (end_date - beg_date) > datetime.timedelta(days=15):
            raise ValueError("Cannot scrape tdelta > 15 days.  Source hangs.")

        # Setting up our mechanize browser
        self.init_browser()

        # Start workin'
        log.info("Scraping foreclosures from %s to %s." %
                  (beg_date.strftime(fmt), end_date.strftime(fmt)))
        self.load_results_page(beg_date.strftime(fmt), end_date.strftime(fmt))
        for i in range(1, self.get_total_pages() + 1):
            self.load_page_number(i)
            rows = self.parse_results_page()
            data.extend(rows)
        log.info("Found %i rows of foreclosure data." % len(data))
        self.browser.close()
        self.browser = None

        # Is this the right move?  Maybe CIVX won't notice me.
        if len(data) == 0:
            log.warn("Skipping out early.  No rows found.")
            return

        # Geocode each row
        log.info("Geocoding each foreclosure address (may take a while).")
        georows = [self.make_geocoded_row(row) for row in data]
        for i in range(len(data)):
            for header in self.headers[-4:]:
                data[i][header] = georows[i][header]
        # TODO -- a more pythonic way to do what the above nested loops do?
        #data = [data[i] + georows[i] for i in range(len(data))]

        # Checks for now to see how well geocoding works.
        success = sum([1 for grow in georows if grow['Map Ready']])
        fail = sum([1 for grow in georows if not grow['Map Ready']])
        log.info("Of %i rows.  %i were geocoded and %i failed." % \
                 (len(georows), success, fail))

        # Format the lines.  Comma-separate and enclose in double-quotes.
        lines = [",".join(["\"%s\"" % h for h in self.headers]) + '\n']
        lines.extend(
            [",".join(["\"%s\"" % row[h] for h in self.headers]) + '\n'
                                                        for row in data])
        # Save this data out to a .csv
        f = os.path.join(self.get_repo_dir(), PropertyInfoForeclosure.__csv__)
        log.debug("Saving to: %s" % f)
        file = open(f, 'w')
        file.writelines(lines)
        file.close()

        # Seal the deal
        self.git_add_and_commit("Updated Property Foreclosures")
        log.debug("Totally done with foreclosure scraping.")

    def go_way_back(self):
        fdate = datetime.datetime(1989, 1, 1)
        tdate = datetime.datetime.today()
        step = 7  # in days

        def date_range(from_date, to_date, step):
            while from_date < to_date:
                yield from_date
                from_date = from_date + datetime.timedelta(days=step)

        for date in date_range(fdate, tdate, step):
            self.scrape_data(
                beg_date=date,
                end_date=date + datetime.timedelta(days=(step - 1)))

    def init_browser(self):
        # TODO -- convert this to use civx.scrapers.get_browser
        # That will require converting the whole of this module
        # to use Twill.
        self.browser = mechanize.Browser()
        self.browser.set_cookiejar(cookielib.LWPCookieJar())
        self.browser.set_handle_equiv(True)
        self.browser.set_handle_redirect(True)
        self.browser.set_handle_referer(True)
        self.browser.set_handle_robots(False)

    # Ugly.
    def geodict_from_row(self, row):
        return {
            self.headers[-4]: row[-4],
            self.headers[-3]: row[-3],
            self.headers[-2]: row[-2],
            self.headers[-1]: row[-1],
        }

    def make_geocoded_row(self, row):
        r = self.geodict_from_row

        # Constant
        bplate = "an address from propertyinfo.com.  Check this out in the DB."

        # Entry is the pythonified json obj returned by Google's geocoding serv
        addr = row['Property Address']
        entry = geocode(addr)
        status, results = entry['status'], entry['results']

        # The return value is a dict with the last four header entries
        if status != "OK":
            log.warn("Geocode: %s, failed '%s'." % (status, addr))
            return r([False, "(status=%s.  failed to geocode)" % status, 0, 0])

        # TODO -- is there anyway to just resolve this now and pick one?
        if len(results) != 1:
            log.warn("Geocode: more than one match, failed '%s'." % addr)
            return r([False, "(found more than one match)", 0, 0])

        result = results[0]
        if not 'street_address' in result['types']:
            log.warn("Geocode: ambiguity in resolving '%s'." % addr)
            return r([False, "(no street_address)", 0, 0])

        # A check for weirdness
        for component in result['address_components']:
            if "administrative_area_level_1" in component['types']:
                # Watch out for this new-york catch in the long run
                if not 'NY' == component['short_name']:
                    log.warn("Geocode: not in New York, failed '%s'." % addr)
                    return r([False, "(not in NY)", 0, 0])

        # We all good.
        loc = result['geometry']['location']
        return r([True, result['formatted_address'], loc['lat'], loc['lng']])

    def parse_results_page(self):
        html = self.browser.response().read()
        soup = BeautifulSoup(html)
        rows = soup.findAll('table')[3].findAll('tr')[1:]
        rows = [[cell.findAll(text=True)
                 for cell in row.findAll('td')] for row in rows]
        rows = [dict([(self.headers[i], " ".join(row[i]).strip())
                      for i in range(len(row))]) for row in rows]
        return rows

    def set_hidden_form_value(self, name, value):
        # A handy util.
        self.browser.form.find_control(name).readonly = False
        self.browser.form[name] = value
        self.browser.form.find_control(name).readonly = True

    def get_total_pages(self):
        try:
            self.browser.select_form(name='frmResult')
        except mechanize._mechanize.FormNotFoundError:
            log.debug(" * Form not found.  No results?")
            return 0
        return int(self.browser.form['totalPages'])

    def load_page_number(self, next_page):
        if next_page == 1:
            return
        self.browser.select_form(name='frmResult')
        total_pages = self.get_total_pages()
        log.debug("Going to page %i of %i" % (next_page, total_pages))
        if next_page > total_pages:
            log.debug(" ran out of pages:  %i > %i" % (next_page, total_pages))
            return None
        self.browser.form['currentPage'] = str(next_page)
        self.browser.form.action = '%s/wam3/SearchResults.asp' % self.base
        self.browser.submit()

    def load_results_page(self, beg_date, end_date):
        log.debug("Trying to load page 1 of ??")

        # Login page
        # TODO -- there are about 6 other counties we can scrape here.
        url = '%s/NY-Monroe/' % self.base
        self.browser.open(url)
        self.browser.follow_link(url_regex=re.compile('.*loginForm.*'))
        self.browser.select_form(nr=0)
        self.browser.form['txtUserName'] = config.get('propertyinfo.username')
        self.browser.form['txtPassword'] = config.get('propertyinfo.password')
        self.browser.submit()

        # Load search page and input criteria
        self.browser.follow_link(url_regex=re.compile('.*=2004.*'))
        self.browser.select_form(name='frmSavedCriteria')
        self.set_hidden_form_value('SearchbyDateFrom', beg_date)
        self.set_hidden_form_value('SearchbyDateTo', end_date)
        # TODO -- there are lots of other doc types we can get here.
        self.set_hidden_form_value('SearchDocType',
                              "NOTICE OF PENDENCY MORTGAGE FORECLOSURE")
        self.browser.form.action = '%s/wam3/SearchSummary.asp' % self.base
        self.browser.submit()

        # Follow an implicit redirect
        try:
            # which, however, will shit the bed if there are no results
            self.browser.select_form(name='frmResult')
            self.browser.submit()
        except mechanize._mechanize.FormNotFoundError:
            log.debug("No results found for %s to %s" % (beg_date, end_date))
            return None