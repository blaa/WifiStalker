
app.controller("SenderCtrl", function($scope, $http, $interval, $log) {
    /*
     * Inherited:
     * $scope.tab - this tab
     */
    $scope.sender = undefined;
    $scope.graphData = undefined;

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
        function setGraphData(data) {
            $scope.graphData = data.graph;
            $log.info('Loaded graph data', $scope.graphData);
        }

        // Get knowledge
        $scope.loadKnowledge({
            'mac': $scope.tab.mac,
            'success': setSenderData
        });

        // Get graph data
        var httpRequest = $http({
            method: 'GET',
            url: '/api/graph/strength/' + $scope.tab.mac,
            data: {}
        }).success(setGraphData);
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

