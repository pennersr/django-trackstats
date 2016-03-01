(function () {

    function init() {
        google.load('visualization', '1', {packages: ['corechart']});
        google.setOnLoadCallback(drawChart);

        function drawChart() {
            var data = new google.visualization.DataTable();
            data.addColumn('date', 'Date');
            data.addColumn('number', 'Value');

            data.addRows(graphData);
            var chart = new google.visualization.ColumnChart(document.getElementById('trackstats-graph'));
            chart.draw(data, graphOptions);
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
        init();
    });
})();
