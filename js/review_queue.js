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
    if (data_table){
        data_table.fnClearTable()
    }
    
    //Reinitialize the table with new settings
    var rpc_request = ghiapi.get.donations
    var rpc_params = add_cookie({'query':query})

    data_table = initializeTable(5, rpc_request, rpc_params, function(data_table, d){
        dataTableWriter(data_table, d)
    })

    toggleSelectionButtons(query)
    change_search_hash(query)

    $("#search_query").blur()
}

$(document).ready(function(){  
    var query = $("#search_query").val()

    //If ?search= doesn't exist in URL bar, resort to default search reviewed:no
    if (window.location.hash.indexOf("search=") == -1 && query == ""){
        query = "reviewed:no"
        $("#search_query").val(query)
    }
    
    trigger_search(query)

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