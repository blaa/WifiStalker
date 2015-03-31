app.controller("TaggingCtrl", function($scope, $http, $log, $filter) {

    var now = new Date();

    /* Altered rows */
    $scope.altered = null;
    /* Operation status - true (ok)/false (bad)/null */
    $scope.status = null;


    $scope.tagTypes = 'all';
    $scope.minStrength = -90;
    $scope.tags = '';
    
    /* Date/time pickers */
    $scope.dateOptions = {
        formatYear: 'yy',
        startingDay: 1
    };

    $scope.rangeFrom = now;
    $scope.rangeTo = now;


    function toUTC(date) {
        //var utc = new Date(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate(),  
        //                   date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds());
        return date;
        //return utc;
    }

    $scope.setRange = function(seconds) {
        var endMSeconds = $scope.rangeTo.getTime();
        var startMSeconds = endMSeconds - seconds*1000;

        $scope.rangeFrom = new Date(startMSeconds);
    };

    /* Reset datetimepicker to Now */
    $scope.setNow = function(which) {
        if (which == 'from')
            $scope.rangeFrom = new Date();
        else if (which == 'to')
            $scope.rangeTo = new Date();
    };

    /* Submit tagging data */
    $scope.submit = function(untag) {
        var data = {
            'from': toUTC($scope.rangeFrom),
            'to': toUTC($scope.rangeTo),
            'min_str': $scope.minStrength,
            'tags': $scope.tags,
            'types': $scope.tagTypes,
            'untag': untag // Untag if true
        };

        function success(data) {
            if (data['OK'] != true)
                return;
            $scope.altered = data.cnt;
            $scope.status = data.OK;
        }

        $http.post('/api/tag/range', data).success(success);
    };


});