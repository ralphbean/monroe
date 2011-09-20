Monroe County Foreclosures App
==============================

This web-application scrapes public data on foreclosures in Monroe county, NY.

It was built for activists trying to defend their neighborhoods from evictions.

With it, you can view foreclosures in Monroe County as a `grid
<http://monroe-threebean.rhcloud.com/grid>`_, on a `map
<http://monroe-threebean.rhcloud.com/map>`_, or you can view the top
'foreclosures' or `grantors <http://monroe-threebean.rhcloud.com/grantors>`_.

Paul Krugman `writes in the NYT
<http://www.nytimes.com/2010/10/15/opinion/15krugman.html>`_::

  An epic housing bust and sustained high unemployment have led to an epidemic of
  default, with millions of homeowners falling behind on mortgage payments. So
  servicers - the companies that collect payments on behalf of mortgage owners
  - have been foreclosing on many mortgages, seizing many homes.

  But do they actually have the right to seize these homes? Horror stories have
  been proliferating, like the case of the Florida man whose home was taken even
  though he had no mortgage. More significantly, certain players have been
  ignoring the law. Courts have been approving foreclosures without requiring
  that mortgage servicers produce appropriate documentation; instead, they have
  relied on affidavits asserting that the papers are in order. And these
  affidavits were often produced by "robo-signers," or low-level employees
  who had no idea whether their assertions were true.

  Now an awful truth is becoming apparent: In many cases, the documentation
  doesn't exist. In the frenzy of the bubble, much home lending was undertaken
  by fly-by-night companies trying to generate as much volume as possible.
  These loans were sold off to mortgage "trusts," which, in turn, sliced and
  diced them into mortgage-backed securities. The trusts were legally required
  to obtain and hold the mortgage notes that specified the borrowers'
  obligations. But it's now apparent that such niceties were frequently
  neglected. And this means that many of the foreclosures now taking place
  are, in fact, illegal.

  This is very, very bad. For one thing, it's a near certainty that
  significant numbers of borrowers are being defrauded - charged fees they
  don't actually owe, declared in default when, by the terms of their loan
  agreements, they aren't.

  Beyond that, if trusts can't produce proof that they actually own the
  mortgages against which they have been selling claims, the sponsors of
  these trusts will face lawsuits from investors who bought these claims -
  claims that are now, in many cases, worth only a small fraction of their
  face value.

  And who are these sponsors? Major financial institutions - the same
  institutions supposedly rescued by government programs last year. So
  the mortgage mess threatens to produce another financial crisis.

Bugs and Feature Requests
-------------------------

Please submit bug notifications and feature requests at on the project's `github
page <http://github.com/ralphbean/monroe/issues>`_.

TODO
----

Select a timespan for any view. i.e., view only the top 5 grantors between 1994
and 1998.


Authors
-------

 - Ralph Bean <ralph.bean@gmail.com>

   - Member, `International Socialist Organization
     <http://internationalsocialist.org>`_
   - Without struggle, there is no progress.

.. Add your name, email, associations, and quote here!

License
-------

This software is licensed under the `AGPL
<http://www.gnu.org/licenses/agpl-3.0.txt>`_.

Instructions for Developers
---------------------------

This app is written in `Python <http://python.org>`_ using `Turbogears 2
<http://turbogears.org>`_ and `Toscawidgets 2
<http://toscawidgets.org/documentation/tw2.core/>`_.  It makes use of code
originally written for and borrowed from `civx.us
<https://fedorahosted.org/civx/>`_.

To install it and develop on it, you'll need a working copy of `python
<http://python.org>`_ and `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_.  With those, the app can install its
own dependencies.

Get the source from `github <http://github.com/ralphbean/monroe>`_.

    - Create a `github account <http://github.com>`_.
    - Fork the `upstream repository <http://github.com/ralphbean/monroe>`_.
    - Clone your forked repo.

      - $ git clone git@github.com:YOUR_USERNAME/monroe.git

    - Create a virtualenv (virtual environment)

      - $ virtualenv --no-site-packages ~/tg2env
      - $ source ~/tg2env/bin/activate

    - Have the application set itself up.

      - $ cd monroe/wsgi/tg2app
      - $ python setup.py develop

    - Give it a test run

      - $ paster serve --reload development.ini

    - Point your browser at http://localhost:8080/

Hosting
-------

This app is hosted on redhat's openshift cloudliness.  Specifically at
http://monroe-threebean.rhcloud.com/.
