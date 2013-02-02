function dataTableWriter(data_table, d){
    data_table.fnAddData([
            d.key,
            d.time_deposited
        ])

    data_table.fnAdjustColumnSizing()
}

function trigger_search(query){
    data_table.fnClearTable()
    
    //Reinitialize the table with new settings
    rpc_params = [query]
    pageThrough(data_table, 0, "getDeposits", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    data_table = initializeTable(1, "getDeposits", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    $("#search_query").blur()
}

$(document).ready(function(){

    //Initialize data table
    var query = $("#search_query").val()
	rpc_params = [query]

	var data_table = initializeTable(1, "getDeposits", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    //When deposit is clicked, go to its page
	$("#all_deposits").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "deposit?d=" + clicked_id)
    });

    setupSearchEvents()

})