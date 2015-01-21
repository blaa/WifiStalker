app.directive('wifiChart', function() {
    return {
        restrict: 'A',
        scope: {
            chartData: '='
        },
        //template: '<canvas width="800" height="400"></canvas>',
        link: function(scope, element, attrs) {
            scope.canvas = element[0];
            scope.context = scope.canvas.getContext('2d');

            Chart.defaults.global.animation = false;

            function update(newValue) {

                var options = {
                    bezierCurve: false,
                    datasetFill : false
                };
                if (newValue == null) {
                    return;
                }
                var chart = new Chart(scope.context).Line(newValue, options);
            }
            scope.$watch('chartData', update);
        }
    };
});


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

                var i;
                for (i in newValue.nodes) {
                    var node = newValue.nodes[i];
                    scope.g.addNode(node[0], node[1]);
                    console.log('Adding node', node[0], node[1]);
                }

                for (i in newValue.edges) {
                    var edge = newValue.edges[i];
                    scope.g.addEdge(edge[0], edge[1], edge[2]);
                }

                scope.layouter.layout();

                /* FIXME: It doesn't want to work not-by-id */
                if (scope.renderer == undefined) {
                    scope.renderer = new Graph.Renderer.Raphael(canvas_id, scope.g, 800, 400);
                }
                scope.renderer.draw();
            }
            scope.$watch('graphData', update);
        }
    };
});
