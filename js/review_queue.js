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
    var query = $("#search_query").val()
    var rpc_params = [query]
    var data_table = initializeTable(5, "getDonations", rpc_params, function(data_table, d){
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
        $("#unreviewed").removeClass("blue")
        $("#all_donations").removeClass("blue")

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

    $("#selector_buttons input").click(function(){
        var clicked_id = $(this).attr("id")
        if (clicked_id == "unreviewed"){
            $("#search_query").val("reviewed:no")
            $("#search_go").click()

            $("#unreviewed").addClass("blue")
            $("#all_donations").removeClass("blue")
        }
        else {
            $("#search_query").val("")
            $("#search_go").click()
            
            $("#all_donations").addClass("blue")
            $("#unreviewed").removeClass("blue")
        }

    })
    
    $("#download_query").click(function(){
        query = $("#search_query").val()
        data = {"query" : query}
        url = "/ajax/spreadsheetdonations?" + $.param(data)
        window.open(url)
    })
});