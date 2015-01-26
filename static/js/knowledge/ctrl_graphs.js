app.directive('wifiGraph', function() {
    return {
        restrict: 'A',
        scope: {
            graphData: '='
        },
        //template: '<canvas width="800" height="400"></canvas>',
        link: function(scope, element, attrs) {
            scope.canvas = element[0];
            scope.g = new Graph();
            scope.renderer = undefined;
            scope.layouter = new Graph.Layout.Spring(scope.g);
            function update(newValue) {
                if (!newValue) {
                    console.log('Ignore update, no data');
                    return;
                }
                var canvas_id = scope.canvas.id;
                console.log(canvas_id, scope.canvas);

                /* Clear graph */
                scope.g.nodes = [];
                scope.g.edges = [];

                /* FIXME: No jquery maybe? */
                $('svg', scope.canvas).children().remove();

                /* Add nodes */
                var i;
                for (i in newValue.nodes) {
                    var node = newValue.nodes[i];
                    scope.g.addNode(node[0], node[1]);
                }

                /* Add edges */
                for (i in newValue.edges) {
                    var edge = newValue.edges[i];
                    scope.g.addEdge(edge[0], edge[1], edge[2]);
                }

                scope.layouter.layout();

                /* FIXME: It doesn't want to work not-by-id */
                if (scope.renderer == undefined) {
                    scope.renderer = new Graph.Renderer.Raphael(canvas_id, scope.g, 1024, 768);
                }
                scope.renderer.draw();
            }
            scope.$watch('graphData', update);
        }
    };
});


app.controller("GraphsCtrl", function($scope, $http, $interval, $log) {
    /*
     * Inherited:
     * $scope.tab - this tab
     */
    $scope.mac = $scope.tab.id;
    $scope.graphData = undefined;
    $scope.refreshing = false;

    /* Enabled chart */
    $scope.graphType = 'ssids';

    /*
     * Helper functions
     */
    $scope.refreshGraph = function() {
        $scope.refreshing = true;

        function setGraphData(data) {
            $scope.refreshing = false;
            $scope.graphData = data.graph;
        }

        function error() {
            $scope.refreshing = false;
        }

        // Get chart data
        $http({
            method: 'GET',
            url: '/api/graph/relations/' + $scope.mac,
            data: {}
        }).success(setGraphData).error(error);
    };

    /* Initialize tab contents */
    $scope.refreshGraph();
});
