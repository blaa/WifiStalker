/*
 * Handle data for knowledge view, has two children controllers - table and sender.
 */

app.controller("KnowledgeCtrl", function($scope, $http, $log) {
    /* Opened senders tab */
    $scope.detailsTabs = [];

    $scope.loadKnowledge = function(opts) {
        /* Generic data loading function shared between child controllers */
        var args = {
            sort: '-aggregate.last_seen',
            mac: null,
            time_window: null,
            success: null
        };

        angular.extend(args, opts);

        function handle_success(data, status) {
            $log.info('Loaded data', data.knowledge.length);

            /* Reindex by MAC */
            var knowledge_by_mac = {};
            for (var i in data.knowledge) {
                var host = data.knowledge[i];
                knowledge_by_mac[host.mac] = host;
            }
            if (args.success)
                args.success(data.knowledge, knowledge_by_mac);
        }

        var httpRequest = $http({
            method: 'GET',
            url: '/api/knowledge',
            params: {
                time_window: args.time_window,
                sort: args.sort,
                mac: args.mac
            }
        }).success(handle_success);
    };
    $log.info('Knowledge loaded');

    /* Open tab for specified sender */
    $scope.openTab = function(mac, ap, title, type) {
        /* Check if already open */

        /* Try opening existing tab instead of opening new one*/
        var tab;
        for (var i in $scope.detailsTabs) {
            tab = $scope.detailsTabs[i];
            if (tab.mac == mac && tab.type == type) {
                // Just open it.
                tab.active = true;
                $log.info('Chart was already open');
                return;
            }
        }

        if (!title) {
            title = 'Opening new tab';
        }

        /* Not opened - Open new */
        tab = {    // aa:bb:cc:dd:ee:ff
            'title': title,
            'mac': mac,
            'active': true,
            'type': type,

            /* Used to show icon */
            'ap': ap,

            // Graph data
            graph: undefined
        };

        $scope.detailsTabs.push(tab);
    };

    $scope.closeTab = function(index) {
        var tabs = $scope.detailsTabs;
        tabs.splice(index, 1);
    };
});
