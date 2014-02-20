'use strict';

angular.module('predict.controllers', [])

.controller('TrainingPhaseController',
    ['$scope', 'predict.services.PredictRPCService',
        'predict.factories.BlobManager',
    function($scope, predictService, blobManager) {
        
        $scope.uploadedFiles = blobManager.availableFiles;
                
        function init(){
            $scope.loadingGDriveFiles = true;
            predictService.loadFileNames()
            .then(function(gDriveFiles){
                console.log('loaded gDrive files', gDriveFiles);
                $scope.loadingGDriveFiles = false;
                $scope.gDriveFiles = gDriveFiles;
            }
            );
            $scope.loadingContexts = true;
            predictService.loadContexts()
            .then(function(contexts){
                console.log('loaded contexts', contexts);
                $scope.loadingContexts = false;
                $scope.contexts = contexts;
            }
            );
        }
        init();
        
        $scope.train = function(contextName){
            predictService.train(contextName)
            .then(function(status){
                console.log('running...');
                $scope.trainingStatus = 'Processing data...';
            });
        }
        
        $scope.createContext = function(file){
            predictService.createContext(file.key)
            .then(function(status){
                console.log('created context for file', file.key);
                }
                );
            console.log('creating context for file', file.key);
        };
        
        $scope.deleteContext = function(index){
            predictService.deleteContext($scope.contexts[index].name)
            .then(function(status){
                console.log('finished deleting context', $scope.contexts[index].name);
                $scope.contexts.splice(index, 1);
            });
        }
        
        $scope.driveImport = function(file){
            console.log('importing', file);
            $scope.gDriveActivityMessage = 'Processing data...';
            predictService.driveImport(file.title, file.downloadUrl)
            .then(function(status){
                console.log('finished training set', file);
            });
        }
    }
])

.controller('BlobStoreUploadController',
[ '$scope', '$upload', '$window', 'predict.factories.BlobManager',
function($scope, $upload, $window, blobManager) {
    $scope.onFileSelect = function($files) {
        // uses a file manager service
        
        //$files: an array of files selected, each file has name, size, and type.
        blobManager.uploadUrl()
        .then(function(blobStoreUploadUrl){
            for (var i = 0; i < $files.length; i++) {
              var file = $files[i];
              $scope.upload = $upload.upload({
                url: blobStoreUploadUrl,
                // method: POST or PUT,
                // headers: {'headerKey': 'headerValue'},
                // withCredentials: true,
                data: {'myObj': $scope.myModelObj},
                file: file,
              }).progress(function(evt) {
                  var progressionPct = parseInt(100.0 * evt.loaded / evt.total)
                  $scope.progressionPct = progressionPct;
              }).success(function(data, status, headers, config) {
                // file is uploaded successfully
                console.log('uploaded with status:', status);
                console.log('file list', blobManager.availableFiles);
                blobManager.updateFilesList().then(
                    function () {
                        console.log('file list after', blobManager.availableFiles);
                    }
                );
                console.log('file list before', blobManager.availableFiles);
              });
              //.error(...)
              //.then(success, error, progress); 
            }
        });
    };
}
])

;

