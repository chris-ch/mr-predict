'use strict';

angular.module('predict.factories', [])

.factory('predict.factories.BlobManager',
    [ 'predict.services.PredictRPCService',  
function(predictService){
                  
    var _availableFiles = [];
    
    var instance = {
        availableFiles: _availableFiles,
        updateFilesList: function () {
            var update = predictService.listAvailableFiles()
            .then(
                function (files) {
                    _availableFiles.length = 0;
                    _availableFiles.push.apply(_availableFiles, files);
                }
                );
            return update;
        },
        uploadUrl: function () {
            return predictService.blobStoreUploadUrl();
        },
    };    
    instance.updateFilesList();
    
    return instance;
}
])

.factory('predict.factories.GoogleDriveManager',
    [ 'predict.services.PredictRPCService',  
function(predictService){
                  
    var _driveFiles = [];
    
    var instance = {
        files: _driveFiles,
        importFile: function (file) {
            return predictService.driveImport(file.title, file.downloadUrl);
        },
        loadAll: function () {
            var update = predictService.loadFileNames()
            .then(function(gDriveFiles){
                console.log('loaded google drive files', gDriveFiles);
                _driveFiles.length = 0;
                _driveFiles.push.apply(_driveFiles, gDriveFiles);
            }
            );
            return update;
        },
    };    
    instance.loadAll();
    
    return instance;
}
])

.factory('predict.factories.ContextManager',
    [ 'predict.services.PredictRPCService',
function(predictService){
                  
    var _availableContexts = [];
    
    var instance = {
        availableContexts: _availableContexts,
        loadAll: function () {
            var update = predictService.loadContexts()
            .then(
                function (contexts) {
                    _availableContexts.length = 0;
                    _availableContexts.push.apply(_availableContexts, contexts);
                    console.log('available contexts refreshed', _availableContexts);
                }
                );
            return update;
        },
        create: function (file) {
            var update = predictService.createContext(file.key)
            .then(
                function (contexts) {
                    console.log('server currently importing context');
                }
                );
            return update;
        },
        remove: function (index) {
            var context = _availableContexts[index]
            var name = context.name;
            var update = predictService.deleteContext(name)
            .then(function(status){
                console.log('finished deleting context', name);
                _availableContexts.splice(index, 1);
            });
            return update;
        },
    };    
    instance.loadAll();
    
    return instance;
}
])

;
