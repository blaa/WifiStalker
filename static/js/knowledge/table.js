
app.controller("TableCtrl", function($scope, $http, $interval, $log) {
    /*
     * Data model
     */

    /* Parameters */
    $scope.timeWindow = 120;
    $scope.refreshInterval = 10;
    $scope.snapshotName = '';

    $scope.knowledge = null;
    $scope.knowledge_by_mac = null;

    var refreshPromise = null;

    /*
     * Callers / main functions
     */
    $scope.refreshTable = function() {
        function handle_success(knowledge, knowledge_by_mac) {
            $scope.knowledge = knowledge;
            $scope.knowledge_by_mac = knowledge_by_mac;
        }

        $scope.loadKnowledge({
            'time_window': $scope.timeWindow,
            'sort': 'last_seen',
            'success': handle_success
        });
    };

    // Initial load
    $scope.refreshTable();

    // Auto refresh
    $scope.$watch('refreshInterval', function (newVal, oldVal) {
        /* Cancel current promise */
        if (refreshPromise == null || newVal != oldVal) {
            $interval.cancel(refreshPromise);

            if ($scope.refreshInterval != 'pause')
                refreshPromise = $interval($scope.refreshTable, $scope.refreshInterval * 1000);
        }
    });

    /* Handle knowledgedumps */
    $scope.snapshotCreate = function() {
        $http.post('/snapshot', {
            'name': $scope.snapshotName,
            'timeWindow': $scope.timeWindow
        });
    };

    $log.info('Table loaded');
});


