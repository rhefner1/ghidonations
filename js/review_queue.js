function dataTableWriter(data_table, d){
    data_table.fnAddData([
        d.key,
        d.formatted_donation_date,
        d.name,
        d.email,
        d.amount_donated,
        d.payment_type
    ])

    data_table.fnAdjustColumnSizing()
}

$(document).ready(function(){  
    var initial_cursor = $("#initial_cursor").val()
    var rpc_params = ["unreviewed"]
    var data_table = initializeTable(5, initial_cursor, "getDonations", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    $("#donations").delegate("tr", "click", function(){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        var url = "/ajax/reviewdetails?id=" + clicked_id
        loadColorbox(url, "rq_details_container")
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
        pageThrough(data_table, 0, "getDonations", rpc_params, function(data_table, d){
            dataTableWriter(data_table, d)
        })

        data_table = initializeTable(5, initial_cursor, "getDonations", rpc_params, function(data_table, d){
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
});