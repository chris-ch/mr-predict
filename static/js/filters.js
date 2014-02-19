'use strict';

angular.module('predict.filters', [])

/* Custom filters */

.filter('filesize', function () {
		return function (size) {
			if (isNaN(size))
				size = 0;
 
			if (size < 1024)
				return size + ' Bytes';
 
			size /= 1024;
 
			if (size < 1024)
				return size.toFixed(2) + ' k';
 
			size /= 1024;
 
			if (size < 1024)
				return size.toFixed(2) + ' M';
 
			size /= 1024;
 
			if (size < 1024)
				return size.toFixed(2) + ' G';
 
			size /= 1024;
 
			return size.toFixed(2) + ' T';
		};
	})
  
;
