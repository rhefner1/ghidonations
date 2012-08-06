$(document).ready(function(){

    //Initialize data table
	var initial_cursor = $("#initial_cursor").val()
	var data_table = initializeTable(1, initial_cursor, "getDeposits", null, function(data_table, d){
        data_table.fnAddData([
            d.key,
            d.time_deposited
        ])
    })

    //When deposit is clicked, go to its page
	$("#all_deposits").delegate("tr", "click", function(){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        window.location.hash = "deposit?d=" + clicked_id
    });

})