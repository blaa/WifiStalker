
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

    var debug_open = true;

    /*
     * Callers / main functions
     */
    $scope.refreshTable = function() {
        function handle_success(knowledge, knowledge_by_mac) {
            $scope.knowledge = knowledge;
            $scope.knowledge_by_mac = knowledge_by_mac;

            /* DEBU OPEN ALL */
            if (debug_open == false) {
                debug_open = true;
                var sender = knowledge[0];
                var mac = sender.mac;
                $scope.openTab(mac, sender.meta.ap, sender.user.alias, 'sender');
                $scope.openTab(mac, sender.meta.ap, sender.user.alias, 'charts');
            }
        }

        $scope.loadKnowledge({
            'time_window': $scope.timeWindow,
            'sort': '-meta.running_str',
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


