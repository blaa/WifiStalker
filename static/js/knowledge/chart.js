app.directive('wifiChart', function() {
    return {
        restrict: 'A',
        scope: {
            graphData: '='
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
            scope.$watch('graphData', update);
        }
    };
});
