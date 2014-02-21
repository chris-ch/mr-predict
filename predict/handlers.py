import logging
import httplib2

import webapp2
from webapp2_extras.appengine.users import login_required

from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

from oauth2client import appengine
from oauth2client import client
import jsonrpc
import settings

from predict import models

_LOG = logging.getLogger('predict.handlers')

decorator = appengine.oauth2decorator_from_clientsecrets(
    settings.CLIENT_SECRETS,
    scope='https://www.googleapis.com/auth/drive.readonly',
    message=settings.MISSING_CLIENT_SECRETS_MESSAGE)

class RpcHandler(jsonrpc.basehandler.BaseHandler):
    
    @decorator.oauth_required
    def post(self):
        self.__http = decorator.http()
        server = jsonrpc.Server(self)
        server.handle(self.request, self.response)

    @property
    def http(self):
        return self.__http
        
class BlobImportWorker(webapp2.RequestHandler):
    
    def post(self):
        _LOG.info('--------- started blob import')
        import csv
        user_id = self.request.get('user_id')
        blob_key = self.request.get('blob_key')
        item = blobstore.BlobInfo.get(blobstore.BlobKey(blob_key))
        content = item.open()
        new_name = models.TrainingContext.find_new_name(user_id)
        new_context = models.TrainingContext(name=new_name, user_id=user_id)
        new_context.source_filename = item.filename
        new_context_key = new_context.put()
        reader = csv.reader(content, delimiter=',')   
        dimensions = new_context.csv_import_header(reader)
        new_context.csv_import(reader, dimensions)
        content.close()
        
class DecisionTreeFactoryWorker(webapp2.RequestHandler):
    
    def post(self):
        _LOG.info('--------- started tree factory')
        user_id = self.request.get('user_id')
        context_name = self.request.get('context_name')
        context = models.TrainingContext.query(
            models.TrainingContext.user_id == user_id, 
            models.TrainingContext.name == context_name).get()
        _LOG.info('--------- tree factory completed')
    
class MainHandler(webapp2.RequestHandler):
    
    @decorator.oauth_aware
    def get(self):
        user = users.get_current_user()
        if user:
            if decorator.has_credentials():
                self.redirect('/predict')
                
            else:
                self.redirect('/grant')
                
        else:
            self.redirect(users.create_login_url(self.request.uri))
    
class GrantHandler(webapp2.RequestHandler):
    
    @decorator.oauth_aware
    def get(self):
        user = users.get_current_user()
        variables = {
            'user': user.nickname(),
            'logout': users.create_logout_url('/'),
            'url': decorator.authorize_url(),
            'has_credentials': decorator.has_credentials(),
            }
        template = settings.JINJA_ENVIRONMENT.get_template('grant.html')
        self.response.write(template.render(variables))
    
class PredictHandler(webapp2.RequestHandler):
    
    @decorator.oauth_required
    def get(self):
        try:
            template = settings.JINJA_ENVIRONMENT.get_template('predict.html')
            self.response.write(template.render())
            
        except client.AccessTokenRefreshError:
            self.redirect('/')
            
class BlobUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    
    def post(self):
        self.get_uploads('file')  # 'file' is file upload field in the form
        
