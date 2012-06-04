function contactSearch(){
     $("#back_allcontacts").show()
    // I have no idea why the review queue code like this works
    rpc_params = [$("input[name=search]").val()]
    pageThrough(data_table, 0, "contactSearch", rpc_params, function(data_table, d){
        data_table.fnAddData([
            d.key,
            d.name,
            d.email
        ])
    })
}

function loadAllContacts(){
     $("#back_allcontacts").hide()
     pageThrough(data_table, 0, "getContacts", null, function(data_table, d){
        data_table.fnAddData([
            d.key,
            d.name,
            d.email
        ])
    })
    
}

$(document).ready(function(){  
    var initial_cursor = $("#initial_cursor").val()
    var data_table = initializeTable(2, initial_cursor, "getContacts", null, function(data_table, d){
        data_table.fnAddData([
            d.key,
            d.name,
            d.email
        ])
    })

    $("#back_allcontacts").click(function(){
        $("input[name=search]").val("")
        loadAllContacts()
    })

    $("input[name=search]").keyup(function(event){
        if(event.keyCode == 13){
            contactSearch()
        }
    });

    $("#submit_search").click(function(){
        contactSearch(data_table)
    })

    $("#contacts").delegate("tr", "click", function(){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        window.location.hash = "contact?c=" + clicked_id
    });

});