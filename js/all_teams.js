$(document).ready(function(){  

    //Initialize data table
    var initial_cursor = $("#initial_cursor").val()
    var data_table = initializeTable(1, initial_cursor, "getTeams", null, function(data_table, d){
        data_table.fnAddData([
            d.key,
            d.name
        ])
    })

    //When team is clicked, go to its page
    $("#teams").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "teammembers?t=" + clicked_id)
    });
});