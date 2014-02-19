'use strict';

angular.module('predict.transformers', [])

.factory('predict.transformers.IdentityTransformer',
    function(){
        return function(data){
            return JSON.parse(data);
        };
    })

.factory('predict.transformers.TreeTransformer',
    function(){
        return function(rawData){                  
            var data = JSON.parse(rawData);
            var result = data.result;
            var treeAdjustedResult = new Array();
            for(var index=0; index < result.length; index++){
                var tuple = new Array();
                var treeview = toTreeViewModel(result[index][0], result[index][1]);
                tuple[0] = treeview.tree;
                tuple[1] = result[index][1];
                tuple[2] = treeview.lookup;
                treeAdjustedResult.push(tuple);
            }
            data.result = treeAdjustedResult;
            return data;
        };
    })

;

function toTreeViewModel(oasTree, accounts, parent){
    var treeViewModel = new Array();
    var lookup = new Object();
    for(var accountCode in oasTree){
        var node = new Object();
        node.label = function() { return this.id + ' - ' + this.name; }
        node.id = accountCode;
        node.name = accounts[accountCode];
        var recurse = toTreeViewModel(oasTree[accountCode], accounts, accountCode);
        node.children = recurse.tree;
        node.parent = parent;
        treeViewModel.push(node);
        lookup[node.id] = node;
        for (var key in recurse.lookup) {
            lookup[key] = recurse.lookup[key];
        }
    }
    return {'tree': treeViewModel, 'lookup': lookup};
}

