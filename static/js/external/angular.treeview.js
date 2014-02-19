/*
        @license Angular Treeview version 0.1.6
        ⓒ 2013 AHN JAE-HA http://github.com/eu81273/angular.treeview
        License: MIT


        [TREE attribute]
        angular-treeview: the treeview directive
        tree-id : each tree's unique id.
        tree-model : the tree model on $scope.
        node-id : each node's id
        node-label : each node's label
        node-children: each node's children

        <div
                data-angular-treeview="true"
                data-tree-id="tree"
                data-tree-model="roleList"
                data-node-id="roleId"
                data-node-label="roleName"
                data-node-children="children" >
        </div>
*/

(function ( angular ) {
'use strict';

angular.module( 'angularTreeview', [] )
    .directive( 'treeModel',
        ['$compile', function( $compile ) {
        
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            // tree id
            var treeId = attrs.treeId;
            
            // tree model
            var treeModel = attrs.treeModel;
            
            // node id
            var nodeId = attrs.nodeId || 'id';
            
            // node label
            var nodeLabel = attrs.nodeLabel || 'label';
            
            // node badge
            var nodeBadge = attrs.nodeBadge || 'badge';
            
            // children
            var nodeChildren = attrs.nodeChildren || 'children';
            
            // dropdown items
            var nodeItems = attrs.nodeItems || 'items';
            
            // tree template
            var template =
            '<ul>' +
            '<li data-ng-repeat="node in ' +  treeModel + ' | orderBy:' + treeId + '.sortByLabel ">' +
			    '<i class="collapsed" data-ng-show="node.' + nodeChildren + '.length && !node.expanded" data-ng-click="' + treeId + '.selectNodeHead(node)"></i>' +
			    '<i class="expanded" data-ng-show="node.' + nodeChildren + '.length && node.expanded" data-ng-click="' + treeId + '.selectNodeHead(node)"></i>' +
			    '<i class="normal" data-ng-hide="node.' + nodeChildren + '.length"></i> ' +
                '<div class="btn-group">' + 
                '<button type="button" class="btn btn-default btn-sm" data-ng-click="' + treeId + '.selectNodeHead(node)">' +
                        '{{node.' + nodeLabel + '()}}'+
                '</button>'+
                '<button type="button" class="btn btn-default btn-sm dropdown-toggle" data-toggle="dropdown">' +
                '<span class="caret"></span>'+
                '<span class="sr-only">Toggle Dropdown</span>'+
                '</button>' +
                '<ul class="dropdown-menu">' +
                    '<li data-ng-repeat="(index, item) in node.' + nodeItems + ' track by $index" data-ng-class="{divider: !item[0], disabled: !item[1]}">' +
                    '<a ng-if="item[0]" data-ng-click="item[1] && item[2]()">{{item[0]}}</a>' +
                    '</li>' +
                '</ul>' +
                '</div>' +
                '&nbsp;<span data-ng-if="node.' + nodeBadge + '" class="badge">{{node.' + nodeBadge + '}}</span>' +
                '<div data-ng-hide="!node.expanded" data-tree-id="' + treeId + '"' + 
                    ' data-tree-model="node.' + nodeChildren + '"' +
                    ' data-node-id=' + nodeId + 
                    ' data-node-label=' + nodeLabel + 
                    ' data-node-badge=' + nodeBadge + 
                    ' data-node-children=' + nodeChildren + 
                '></div>' +
            '</li>' +
            '</ul>'
            ;
                    
            //check tree id, tree model
            if( treeId && treeModel ) {
                
                // root node
                if( attrs.angularTreeview ) {
                    
                    // create tree object if not exists
                    scope[treeId] = scope[treeId] || {};
                    
                    // if node head clicks,
                    scope[treeId].selectNodeHead = scope[treeId].selectNodeHead || function( selectedNode ){
                        // collapse or Expand
                        selectedNode.expanded = !selectedNode.expanded;
                    };
                    
                    scope[treeId].sortByLabel = scope[treeId].sortByLabel || function( node ){
                        return node.label();
                    };
                    
                }
                
                // rendering template
                var compiled = $compile( template )( scope );
                element.html('').append( compiled );
            }
            
        }
    };
}]);

})( angular );
