$(document).ready(function(){  

    //Initialize data table
    var initial_cursor = $("#initial_cursor").val()
    var data_table = initializeTable(2, initial_cursor, "getIndividuals", null, function(data_table, d){
        data_table.fnAddData([
            d.key,
            d.name,
            d.email
        ])
    })

    //When individual is clicked, go to their profile page
    $("#individuals").delegate("tr", "click", function(e){
        var row_data = data_table.fnGetData(this)
        var clicked_id =  row_data[0]

        change_hash(e, "profile?i=" + clicked_id)
    });

});