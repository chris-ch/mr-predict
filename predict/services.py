import logging
import httplib2

from google.appengine.api import users
from google.appengine.api import taskqueue
from google.appengine.ext import deferred
from google.appengine.ext import blobstore

from apiclient import discovery
from oauth2client import appengine

from predict import models
from predict.handlers import RpcHandler

_LOG = logging.getLogger('predict.services')

def task_clear(context_key):
    context = context_key.get()
    models.TrainingContext.clear(context)

class ApiHandler(RpcHandler):
    
    def hello(self, world='abcd', limit=1):
        _LOG.info('test service called')
        user = users.get_current_user()
        return [world + '/' + str(user.nickname()) for i in range(limit)]
    
    def blobstore_upload_url(self):
        """
        Returns an updated upload url
        GAE may renew it quite often so the client needs
        to make sure to call this command frequently enough
        """
        return blobstore.create_upload_url('/blobupload')
            
    def drive_import(self, filename, download_url):
        _LOG.info('importing file with id "%s"' % str(download_url))
        user_id = users.get_current_user().user_id()
        taskqueue.add(url='/import/gdrive/',
            queue_name='google-drive-import',
            params={
                'user_id': user_id,
                'filename': filename,
                'download_url': download_url,
            }
        )
        
    def load_file_names(self):
        _LOG.info('loading file names')   
        query = """ mimeType = 'text/csv' and trashed = false """
        drive = discovery.build('drive', 'v2', http=self.http)
        response = drive.files().list(q=query).execute()
        files = [{
                    'id': meta['id'],
                    'title': meta['title'],
                    'downloadUrl': meta['downloadUrl']
                    } for meta in response['items']]
        return files
        
    def list_available_files(self):
        """
        Returns a list of files available in the Blobstore
        """
        blobstore_items = blobstore.BlobInfo.all().run()
        metadata = list()
        for item in blobstore_items:
            metadata.append({
                    'title': item.filename,
                    'size': item.size,
                    'key': str(item.key()),
            })
        
        _LOG.info('available file: %s' % str(metadata))
            
        return metadata
            
    def create_context(self, blob_key):
        """
        Creates a context using the indicated Blob file.
        """
        _LOG.info('creating context for key %s' % str(blob_key))
        user_id = users.get_current_user().user_id()
        taskqueue.add(url='/import/blob/',
            queue_name='blob-import',
            params={
                'user_id': user_id,
                'blob_key': blob_key
            }
            )
    
    def delete_context(self, name):
        _LOG.info('deleting context %s' % name)
        user_id = users.get_current_user().user_id()
        context = models.TrainingContext.query(
            models.TrainingContext.user_id == user_id, 
            models.TrainingContext.name == name).get()
        deferred.defer(task_clear, context.key)
        
    def train(self, context_name):
        _LOG.info('training context %s' % context_name)
        user_id = users.get_current_user().user_id()
        taskqueue.add(url='/factory/',
            queue_name='decision-tree-factory',
            params={
                'user_id': user_id,
                'context_name': context_name,
            }
            )
        
    def load_contexts(self):
        _LOG.info('loading contexts')
        user_id = users.get_current_user().user_id()
        contexts = (models.TrainingContext
                .query(models.TrainingContext.user_id == user_id)
                )
        return [
            {
                'name': context.name,
                'source': context.source_filename,
                'measures_count': context.measures_count,
                'dimensions_count': context.dimensions_count,
            } for context in contexts]
        
        
    
