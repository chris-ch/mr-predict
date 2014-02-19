from webapp2_extras.routes import RedirectRoute
from webapp2_extras.routes import PathPrefixRoute
from webapp2_extras.routes import DomainRoute

import predict.handlers
import predict.services

_routes = [
    # Background tasks
    (r'/import/blob', predict.handlers.BlobImportWorker),
    (r'/factory/', predict.handlers.DecisionTreeFactoryWorker),
    
    # Blob uploads
    (r'/blobupload', predict.handlers.BlobUploadHandler),
    
    (predict.handlers.decorator.callback_path, predict.handlers.decorator.callback_handler()),

    # Main
    RedirectRoute(r'/', predict.handlers.MainHandler, name='home', strict_slash=True),
    
    # Grant
    RedirectRoute(r'/grant', predict.handlers.GrantHandler, name='grant', strict_slash=True),
    
    # Predict
    RedirectRoute(r'/predict', predict.handlers.PredictHandler, name='predict', strict_slash=True),
    
    # JSON-RPC
    RedirectRoute(r'/jsonrpc/', predict.services.ApiHandler, name='jsonrpc', strict_slash=True),
]

def get_routes():
    return _routes
