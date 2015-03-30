// Author: Tomasz bla Fortuna
// License: MIT

app.controller("SenderCtrl", function($scope, $http, $interval, $log) {
    /*
     * Inherited:
     * $scope.tab - this tab
     */
    $scope.mac = $scope.tab.id;
    $scope.sender = undefined;
    $scope.related = undefined;
    $scope.refreshing = false;

    /*
     * Helper functions
     */
    $scope.refreshSender = function() {
        function setSenderData(knowledge, related) {
            $scope.refreshing = false;
            $scope.sender = knowledge[0];
            $scope.related = related;

            /* Update tabs names */
            $scope.renameTabs($scope.mac, $scope.sender.user.alias);
        }

        function error() {
            $scope.refreshing = false;
        }

        // Get knowledge
        $scope.refreshing = true;
        $scope.loadKnowledge({
            'mac': $scope.mac,
            'success': setSenderData,
            'error': error
        });
    };

    /* Initialize tab contents */
    $scope.refreshSender();

    /*
     * Callers / main functions
     */
    $scope.saveTab = function(tab) {
        function success(data) {
            if (data['OK'] != true)
                return;

            $scope.renameTabs($scope.mac, $scope.sender.user.alias);
        }

        $http.post('/api/userdata', {
            'mac': $scope.sender.mac,
            'alias': $scope.sender.user.alias,
            'owner': $scope.sender.user.owner,
            'notes': $scope.sender.user.notes,
            'tags': $scope.sender.user.tags
        }).success(success);


        $scope.loadKnowledge();
    };
});
