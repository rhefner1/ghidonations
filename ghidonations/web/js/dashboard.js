function drawChart() {
    var params = {};
    var request = ghiapi.get.monthly_chart_data(params);
    request.execute(function (response) {
        data = JSON.parse(response.json_data);
        var data = google.visualization.arrayToDataTable(data);
        var options = {
            hAxis: {title: 'Date'},
            vAxis: {title: 'Amount Donated ($)'},
            title: 'Last 30 days of donations'
        };
        var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
        chart.draw(data, options);
    });
}
$(document).ready(function () {
    // -- If there are unread donations, highlight box with yellow -- //
    var num_donations = $('#review_queue .value').html();
    if (parseInt(num_donations) !== 0) {
        $('#review_queue').addClass('attention');
    }
    // -- This function makes buttons clickable -- //
    $('#dashboard .report .button').click(function (e) {
        var hash = $(this).attr('data-location');
        change_hash(e, hash);
    });
    // Initialize chart visualization (timeout needed to load correctly)
    setTimeout(function () {
        google.load('visualization', '1', {
            'callback': 'drawChart()',
            'packages': ['corechart']
        });
    }, 1);
});