$(document).ready(function(){
     // Datepicker
    $(".datepicker").datepicker().children().show();

    $("#export_data").click(function(){
    	url = "/ajax/spreadsheet?e=contacts"
    	window.open(url)
    })

    $("#recurring_donors").click(function(){
    	url = "/ajax/spreadsheet?e=recurring_donors"
    	window.open(url)
    })

    
})