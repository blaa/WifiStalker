
app.controller("SenderCtrl", function($scope, $http, $interval, $log) {
    /*
     * Inherited:
     * $scope.tab - this tab
     */
    $scope.sender = undefined;

    /*
     * Helper functions
     */
    $scope.refreshSender = function() {
        function setSenderData(knowledge, knowledge_by_mac) {
            $scope.sender = knowledge[0];
            if ($scope.sender.user.alias)
                $scope.tab.title = $scope.sender.user.alias;
            else
                $scope.tab.title = $scope.tab.mac;
        }

        // Get knowledge
        $scope.loadKnowledge({
            'mac': $scope.tab.mac,
            'success': setSenderData
        });
    };

    /* Initialize tab contents */
    $scope.refreshSender();

    /*
     * Callers / main functions
     */
    $scope.saveTab = function(tab) {
        function success(data) {
            $log.info('SUCCESS', data);
            if (data['OK'] != true) 
                return;
            if ($scope.sender.user.alias)
                $scope.tab.title = $scope.sender.user.alias;
            else
                $scope.tab.title = $scope.tab.mac;
        }

        $http.post('/api/userdata', {
            'mac': $scope.sender.mac,
            'alias': $scope.sender.user.alias,
            'owner': $scope.sender.user.owner,
            'notes': $scope.sender.user.notes
        }).success(success);

        if (tab.alias) {
            tab.title = tab.alias;
        } else {
            tab.title = tab.mac;
        }

        $scope.loadKnowledge();
    };
});

