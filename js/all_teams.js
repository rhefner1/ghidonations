function dataTableWriter(data_table, d){
    data_table.fnAddData([
        d.key,
        d.name,
    ])

    data_table.fnAdjustColumnSizing()
}

function trigger_search(query){
    data_table.fnClearTable()

    //Reinitialize the table with new settings
    rpc_params = [query]
    pageThrough(data_table, 0, "getTeams", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    data_table = initializeTable(1, "getTeams", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    $("#search_query").blur()
}

$(document).ready(function(){  

    //Initialize data table
    var query = $("#search_query").val()
    var rpc_params = [query]

    var data_table = initializeTable(1, "getTeams", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    //When team is clicked, go to its page
    $("#teams").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "teammembers?t=" + clicked_id)
    });

    $("#search_query").focus(function(){
        $("#search_help").slideDown()
    })

    $("#search_query").focusout(function(){
        $("#search_help").slideUp()
    })

    $("#search_go").click(function(){
        var query = $("#search_query").val()
        change_search_hash(query)
    })
        

    $("#search_query").keyup(function(e){
        if (e.keyCode == 13){
            $("#search_go").click()
        }
    })
});