$(document).ready(function(){
     // Datepicker
    $(".datepicker").datepicker().children().show();

    $("#export_data").click(function(){
    	url = "/ajax/excel"
    	window.open(url)
    })
})