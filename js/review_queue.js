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

function toggleSelectionButtons(query){
    // Manage selection buttons
    if (query == ""){
        $("#all_donations").addClass("blue")
        $("#unreviewed").removeClass("blue")
    }
    else if (query == "reviewed:no"){
        $("#unreviewed").addClass("blue")
        $("#all_donations").removeClass("blue")
    }
    else{
        $("#unreviewed").removeClass("blue")
        $("#all_donations").removeClass("blue")
    }
}

function trigger_search(query){

    //Reinitialize the table with new settings
    rpc_params = [query]
    pageThrough(data_table, 0, "getDonations", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    data_table = initializeTable(5, "getDonations", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    toggleSelectionButtons(query)

    $("#search_query").blur()
}

$(document).ready(function(){  
    var query = $("#search_query").val()
    var rpc_params = [query]
    var data_table = initializeTable(5, "getDonations", rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    toggleSelectionButtons(query)

    $("#donations").delegate("tr", "click", function(){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        var url = "/ajax/reviewdetails?id=" + clicked_id
        loadColorbox(url, "rq_details_container")
    });

    setupSearchEvents()

    $("#selector_buttons input").click(function(){
        var clicked_id = $(this).attr("id")
        if (clicked_id == "unreviewed"){
            $("#search_query").val("reviewed:no")
            $("#search_go").click()
        }
        else {
            $("#search_query").val("")
            $("#search_go").click()
        }
    })
    
    $("#download_query").click(function(){
        query = $("#search_query").val()
        data = {"query" : query}
        url = "/ajax/spreadsheetdonations?" + $.param(data)
        window.open(url)
    })
});