# This file was once part of CIVX.
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
import random
import re
import simplejson
import time
import urllib

import tg2app.model as m

from BeautifulSoup import BeautifulSoup
from tg import config

logging.basicConfig()
log = logging.getLogger('fc-scrape')

the_really_ridiculous_details = [
        #'Subdivison',
    'Lot Number',
    'Landuse',
    'Zoning',
    'Frontage',
    'Depth',
    'Land Value',
    'Assessed Value',
    'Improvements',
    'Year Built',
    'Square Footage',
    'Stories',
    'Housing Units',
    'Rooms',
    'Bedrooms',
    'Baths',
    'Acreage',
]


def date_range(from_date, to_date, step):
    """ Utility to produce a date range """
    while from_date < to_date:
        yield from_date
        from_date = from_date + datetime.timedelta(days=step)

def cross_reference(address):
    try:
        first_two_words = ' '.join(address.split()[:2])
        base = 'http://geo.cityofrochester.gov/results.asp?'
        vals = {'qrytype': 'address', 'qrystr': first_two_words}
        qstr = urllib.urlencode(vals)
        reqstr = base + qstr
        html = urllib.urlopen(reqstr).read()

        soup = BeautifulSoup(html)
        text = soup.findAll('table')[0].findAll('tr')[3].findAll('td')[0].text
        name = ' '.join(text.split()[1:]).strip()
        return name
    except Exception as e:
        return "(error)"

def get_ridiculous_details(address):

    # Initialize details to a dict of key -> 'DNE'
    details = dict(zip(
        the_really_ridiculous_details,
        ['(no data)']*len(the_really_ridiculous_details)
    ))

    first_two_words = ' '.join(address.split()[:2])
    base = 'http://geo.cityofrochester.gov/'
    vals = {'qrytype': 'address', 'qrystr': first_two_words}
    qstr = urllib.urlencode(vals)
    reqstr = base + 'results.asp?' + qstr
    html = urllib.urlopen(reqstr).read()

    soup = BeautifulSoup(html)
    try:
        link = soup.findAll('table')[0].findAll('tr')[3].findAll('td')[4].findAll('a')[0]['href']
    except:
        return details

    reqstr = base + link
    html = urllib.urlopen(reqstr).read()
    soup = BeautifulSoup(html)

    # Fill in every detail that we can...
    for table in soup.findAll('table')[2:4]:
        for tr in table.findAll('tr'):
            try:
                key, value = [span.text for span in tr.findAll('span')]
                key = key.strip()[:-1]
                if key in the_really_ridiculous_details:
                    details[key] = value
            except:
                # Whatever.. the entry will remains 'DNE'
                pass

    return details

def geocode(address):
    # TODO -- a more open way of doing this.
    # Here we have to sleep 1 second to make sure google doesn't scold us.
    time.sleep(1)
    vals = {'address': address, 'sensor': 'false'}
    qstr = urllib.urlencode(vals)
    reqstr = "http://maps.google.com/maps/api/geocode/json?%s" % qstr
    return simplejson.loads(urllib.urlopen(reqstr).read())


class ForeclosureScraper(object):
    """Property Info Mortgage Foreclosure Scraper """
    base = 'https://gov.propertyinfo.com'
    apps_base = 'https://govapps1.propertyinfo.com'
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
            # This is pulled in from geo.cityofrochester.gov
            'XReffed Owner',
    ] + the_really_ridiculous_details + [
            # These are pulled during scrape from Google Maps
            'Map Ready',
            'Formatted Address',
            'Latitude',
            'Longitude',
    ]

    def update_xrefs(self):
        """ Run as a tg-scheduled thing.  Go through our
        whole DB and check to see who currently owns the house.
        """

        print "Running update_xrefs.  Checking our whole DB."
        import transaction

        for closure in m.Foreclosure.query.all():
            current_name = closure.xreffed_owner
            addr = closure.property_address
            print "(xrefs) Inspecting", addr, "(", current_name, ")"
            new_name = cross_reference(addr)
            if new_name != current_name:
                print "The cross referenced name changed from",
                print current_name, "to", new_name
                closure.xreffed_owner = new_name
                closure.xref_updated = datetime.datetime.now()

        transaction.commit()

    def scrape_data(self, beg_date=None, end_date=None, tries=0):
        """ Run as tg-scheduled thing.
        This function does everything.
        """

        if tries > 3:
            raise ValueError, "Tried 3 times already.. failing!"

        # Some initialization
        data = []
        fmt = '%m/%d/%Y'

        # Default if not otherwise specified
        if not end_date:
            end_date = datetime.datetime.today()
        if not beg_date:
            beg_date = end_date - datetime.timedelta(days=4)

        # Sanity
        if (end_date <= beg_date):
            raise ValueError("end date must come after begin date")
        if (end_date - beg_date) > datetime.timedelta(days=15):
            raise ValueError("Cannot scrape tdelta > 15 days.  Source hangs.")

        oldest_date = datetime.datetime(1998, 1, 1)
        if beg_date < oldest_date:
            log.warn("%r is before %r.  We don't care about data that old."
                     "Bailing." % (beg_date, oldest_date))
            return

        # Setting up our mechanize browser
        self.init_browser()

        # Start workin'
        log.warn("Scraping foreclosures from %s to %s." %
                  (beg_date.strftime(fmt), end_date.strftime(fmt)))
        try:
            self.load_results_page(beg_date.strftime(fmt),
                                   end_date.strftime(fmt))
        except Exception as e:
            log.warn("Failed unexpectedly loading initial results page.")
            log.warn(str(e))
            log.warn("Trying again.")
            return self.scrape_data(beg_date, end_date, tries+1)

        for i in range(1, self.get_total_pages() + 1):
            try:
                self.load_page_number(i)
                rows = self.parse_results_page()
                data.extend(rows)
            except Exception as e:
                log.warn("Failed unexpectedly on page %i" % i)
                log.warn(str(e))
        log.warn("Found %i rows of foreclosure data." % len(data))
        self.browser.close()
        self.browser = None

        def already_in_db(row):
            query = m.Foreclosure.query.filter(
                m.Foreclosure.control_no==row['Control No'])
            return query.count() == 1

        data = [row for row in data if not already_in_db(row)]
        log.warn("%i of those rows are not in the db." % len(data))

        # Is this the right move?  Maybe CIVX won't notice me.
        if len(data) == 0:
            log.warn("Skipping out early.  No rows found.")
            return

        # Cross reference each row
        log.warn("Cross-referencing each foreclosure address (who knows!).")
        data = [self.make_cross_referenced_row(row) for row in data]
        # Done.

        # Geocode each row
        log.warn("Geocoding each foreclosure address (may take a while).")
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

        db_data = [
            dict([
                (k.replace(' ', '_').lower(), v) for k, v in row.iteritems()
            ]) for row in data
        ]

        for i in range(len(db_data)):
            db_data[i]['filing_date'] = datetime.datetime.strptime(
                db_data[i]['filing_date'], '%m/%d/%Y')

        import transaction

        for row in db_data:
            query = m.Foreclosure.query.filter(
                m.Foreclosure.control_no==row['control_no'])

            if query.count() == 0:
                m.DBSession.add(m.Foreclosure(**row))
            else:
                log.warn("'%s' already in DB.  Skipping." % row['control_no'])

        transaction.commit()

        log.debug("Totally done with foreclosure scraping.")

    def go_way_back(self):
        fdate = datetime.datetime(1989, 4, 1)
        tdate = datetime.datetime.today()
        fmt = '%m/%d/%Y'
        step = 7  # in days
        log.info("Running the go_way_back robot from %s to %s." %
                  (fdate.strftime(fmt), tdate.strftime(fmt)))

        for date in reversed(list(date_range(fdate, tdate, step))):
            log.warn("Starting wayback scrape.")
            self.scrape_data(
                beg_date=date,
                end_date=date + datetime.timedelta(days=(step - 1)))
            log.warn("Done with wayback scrape.  Sleeping.")

            # Here we'll just sleep a little bit so we don't piss anyone off
            time.sleep(5 + (5 * (random.random() + 1)))
            log.warn("Waking up.")

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

    def make_cross_referenced_row(self, row):
        addr = row['Property Address']
        name = cross_reference(addr)
        row['XReffed Owner'] = name
        print "got", name, "for", addr
        details = get_ridiculous_details(addr)
        row.update(details)
        return row

    def make_geocoded_row(self, row):
        r = self.geodict_from_row

        # Entry is the pythonified json obj returned by Google's geocoding serv
        addr = row['Property Address']
        entry = geocode(addr)
        status, results = entry['status'], entry['results']

        # This is bad news.
        if status == 'OVER_QUERY_LIMIT':
            log.warn("Geocode: WHOAH.. over query limit.  Sleeping 24 hours.")
            time.sleep(86500)
            log.warn("Geocode: Okay.. resuming.")
            return self.make_geocoded_row(row)

        # The return value is a dict with the last four header entries
        if status != "OK":
            log.warn("Geocode: %s, failed '%s'." % (status, addr))
            return r([False, status, 0, 0])

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
        self.browser.form.action = '%s/wam3/SearchResults.asp' % self.apps_base
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
        self.browser.form.action = '%s/wam3/SearchSummary.asp' % self.apps_base
        self.browser.submit()

        # Follow an implicit redirect
        try:
            # which, however, will shit the bed if there are no results
            self.browser.select_form(name='frmResult')
            self.browser.submit()
        except mechanize._mechanize.FormNotFoundError:
            log.debug("No results found for %s to %s" % (beg_date, end_date))
            return None
