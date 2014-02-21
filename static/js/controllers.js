'use strict';

angular.module('predict.controllers', [])

.controller('TrainingPhaseController',
    ['$scope', '$interval',
        'predict.factories.BlobManager',
        'predict.factories.ContextManager',
        'predict.factories.GoogleDriveManager',
        'predict.services.PredictRPCService',
    function($scope, $interval,
        blobManager,
        contextManager,
        driveManager,
        predictService
        ) {
        
        $scope.uploadedFiles = blobManager.availableFiles;
        $scope.contexts = contextManager.availableContexts;
        $scope.gDriveFiles = driveManager.files;
        
        /*var infoRefresher = $interval(function(){
                blobManager.updateFilesList();
            }, 60 * 1000);
        
        $scope.$on('$destroy', function(e) {
                $interval.cancel(infoRefresher);
        });*/
                
        $scope.createContext = function(file){
            contextManager.create(file);
        };
        
        $scope.deleteContext = function(index){
            contextManager.remove(index);
        }
        
        $scope.driveImport = function(file){
            console.log('importing', file);
            $scope.gDriveActivityMessage = 'Processing data...';
            driveManager.importFile(file)
            .then(function(status){
                console.log('launched gdrive import', file);
            });
        }
        
        $scope.train = function(contextName){
            predictService.train(contextName)
            .then(function(status){
                console.log('running...');
                $scope.trainingStatus = 'Processing data...';
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
              });
              //.error(...)
              //.then(success, error, progress); 
            }
        });
    };
}
])

;

