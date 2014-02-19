'use strict';

angular.module('predict',
    [
    'ngResource',
    'angularTreeview',
    'ui.bootstrap',
    'fundoo.services',
    'ngGrid',
    'angularFileUpload',
    
    'predict.services',
    'predict.factories',
    'predict.directives',
    'predict.controllers',
    'predict.transformers',
    'predict.decorators',
    'predict.filters',
  ]
)

/* Configuration */
    /* Version */
    .constant('APP_NAME','predict')
    .constant('APP_VERSION','0.1')
      
;

