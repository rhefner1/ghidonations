$(document).ready(function(){  

    //Initializing data table
    var initial_cursor = $("#initial_cursor").val()
    var data_table = initializeTable(2, initial_cursor, "getContacts", null, function(data_table, d){
        data_table.fnAddData([
            d.key,
            d.name,
            d.email
        ])
    })

    // Autocomplete for contacts
    params = {"action" : "getContactsJSON"}
    var url = '/rpc?' + $.param(params)
    $.getJSON(url, function(data){
        $("input[name=search]").autocomplete({
            source: data,
            select: function(e, ui){
                $("input[name=search]").val(ui.item.name)
                change_hash(e, "contact?c=" + ui.item.key) 
            }
        });
    })

    //When contact row in data table is clicked, go to contact page
    $("#contacts").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "contact?c=" + clicked_id)
    });

});