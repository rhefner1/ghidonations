function dataTableWriter(data_table, d){
    data_table.fnAddData([
        d.key,
        d.name,
        d.email
    ])

    data_table.fnAdjustColumnSizing()
}

$(document).ready(function(){  

    //Initializing data table
    var initial_cursor = $("#initial_cursor").val()
    var data_table = initializeTable(2, initial_cursor, "getContacts", null, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    //When contact row in data table is clicked, go to contact page
    $("#contacts").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "contact?c=" + clicked_id)
    });

   $("#search_query").focus(function(){
        $("#search_help").slideDown()
    })

    $("#search_query").focusout(function(){
        $("#search_help").slideUp()
    })

    $("#search_go").click(function(){
        var query = $("#search_query").val()

        data_table.fnClearTable()

        //Reinitialize the table with new settings
        rpc_params = [query]
        pageThrough(data_table, 0, "getContacts", rpc_params, function(data_table, d){
            dataTableWriter(data_table, d)
        })

        data_table = initializeTable(2, initial_cursor, "getContacts", rpc_params, function(data_table, d){
            dataTableWriter(data_table, d)
        })

        data_table.fnAdjustColumnSizing()

        $("#search_query").blur()
    })
        

    $("#search_query").keyup(function(e){
        if (e.keyCode == 13){
            $("#search_go").click()
        }
        
    })

    $("#download_query").click(function(){
        query = $("#search_query").val()
        data = {"query" : query}
        url = "/ajax/spreadsheetcontacts?" + $.param(data)
        window.open(url)
    })

});