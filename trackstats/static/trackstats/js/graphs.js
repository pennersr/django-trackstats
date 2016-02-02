(function () {

    function init() {
        var elt = document.querySelector('div.trackstats-graph');
        if (elt) {
            new Chartist.Line('div.trackstats-graph',
                              graphData,
                              {fullWidth: true,
                               height: '500px'
                              });
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
        init();
    });
})();
