'use strict';

angular.module('predict.decorators', [])

;

/* USAGE EXAMPLE */
/*
var upstream = angular.module('upstream', []);
upstream.value('name', 'Alexander');

var app = angular.module('plunker', ['upstream']);

app.constant('age', 356 + 1900 + new Date().getYear());
app.controller('MainCtrl', function($scope, name, age) {
  $scope.name = name;
  $scope.age = age;
});
app.config(function($provide) {
  $provide.decorator('name', function($delegate) {
    return $delegate + ' the Great';
  });
  $provide.decorator('age', function($delegate) {
    return ++$delegate;
  });
});
*/
