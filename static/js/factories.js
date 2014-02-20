'use strict';

angular.module('predict.factories', [])

.factory('predict.factories.BlobManager',
    [
        'predict.services.PredictRPCService',
          
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
                    console.log('available files remotely', files);
                    console.log('available files locally', _availableFiles);
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

;
