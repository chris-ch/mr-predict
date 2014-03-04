'use strict';

angular.module('predict.services', [])

.service('predict.services.JsonRPCService',
    ['$q', '$http',
            'predict.transformers.IdentityTransformer',
            'predict.transformers.TreeTransformer',
        function($q, $http, identityTransformer, treeTransformer) {
            
    /* UUID generator for JSON-RPC requests */
    function s4() {
      return Math.floor((1 + Math.random()) * 0x10000)
                 .toString(16)
                 .substring(1);
    };
    
    function guid() {
      return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
             s4() + '-' + s4() + s4() + s4();
    }

    this.call = function (rpcName, params, responseTransformer) {
        var deferred = $q.defer();
        if(_.isUndefined(responseTransformer)){
            responseTransformer = identityTransformer;
        }
        $http(
            {
                method: 'POST',
                url: '/jsonrpc/',
                data: {
                    'jsonrpc': '2.0',
                    'method': rpcName,
                    'id': guid(),
                    'params': params,
                    },
                transformResponse: responseTransformer
            }
            ).
            success(function(data, status) {
                deferred.resolve(data.result);
            }).
            error(function(response, status) {
                console.log('response', response.error.message);
                deferred.reject(response.error.message);
            });
        return deferred.promise;
    };
    
    this.callTree = function (rpcName, params) {
        return this.call(rpcName, params, treeTransformer);
    }
    
}
])

.service('predict.services.PredictRPCService',
    [   'predict.services.JsonRPCService',
    
        function(jsonrpc) {
            
    self = this;
    
    self.displayHello = function (word, limit) {
        return jsonrpc.call('hello',
            {'world': word, 'limit': limit}
            );
    };
    
    self.loadFileNames = function () {
        console.log('loading file names');
        return jsonrpc.call('load_file_names');
    };
    
    self.listAvailableFiles = function () {
        console.log('listing available files in blobstore');
        return jsonrpc.call('list_available_files');
    };
    
    self.loadContexts = function () {
        console.log('loading contexts');
        return jsonrpc.call('load_contexts');
    };
    
    self.deleteContext = function (name) {
        console.log('deleting context', name);
        return jsonrpc.call('delete_context', [ name ]);
    };
    
    self.createContext = function (key) {
        console.log('creating context', key);
        return jsonrpc.call('create_context', [ key ]);
    };
    
    self.train = function (contextName) {
        console.log('training context', contextName);
        return jsonrpc.call('train', [ contextName ]);
    };
    
    self.blobStoreUploadUrl = function () {
        console.log('preparing upload url');
        return jsonrpc.call('blobstore_upload_url', []);
    };
    
    self.driveImport = function (filename, downloadUrl) {
        console.log('importing file id', downloadUrl);
        return jsonrpc.call('drive_import', [ filename, downloadUrl ]);
    };
    
}
])

;


