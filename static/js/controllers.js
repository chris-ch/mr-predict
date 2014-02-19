'use strict';

angular.module('predict.controllers', [])

.controller('TrainingPhaseController',
    ['$scope', 'predict.services.PredictRPCService',
    function($scope, predictService) {
        
        function init(){
            $scope.loadingUploadedFiles = true;
            predictService.listAvailableFiles()
            .then(function(uploadedFiles){
                console.log('uploadedFiles files', uploadedFiles);
                $scope.loadingUploadedFiles = false;
                $scope.uploadedFiles = uploadedFiles;
            }
            );
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
            });
            console.log('creating context for file', file.key);
        }
        
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
[ '$scope', '$upload', '$window', 'predict.services.PredictRPCService',
function($scope, $upload, $window, predictService) {
    $scope.onFileSelect = function($files) {
        //$files: an array of files selected, each file has name, size, and type.
        predictService.blobStoreUploadUrl()
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
                  });
                  //.error(...)
                  //.then(success, error, progress); 
                }
            });
    };
}
]);

;

