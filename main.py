#!/usr/bin/env python
"""Starting template for Google App Engine applications.

Use this project as a starting point if you are just beginning to build a Google
App Engine project. Remember to download the OAuth 2.0 client secrets which can
be obtained from the Developer Console <https://code.google.com/apis/console/>
and save them as 'client_secrets.json' in the project directory.
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

import logging
import webapp2

from google.appengine.ext import ndb

from jsonrpc import basehandler
from jsonrpc import errors

import predict.routes
import config

app = webapp2.WSGIApplication(
        routes=predict.routes.get_routes(),
        config=config.webapp2_config,
        debug=True
        )

