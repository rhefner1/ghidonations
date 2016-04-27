function dataTableWriter(data_table, d) {
    data_table.fnAddData([
        d.key,
        d.name,
        d.email
    ])

    data_table.fnAdjustColumnSizing()
}

function trigger_search(query) {
    if (data_table) {
        data_table.fnClearTable()
    }

    query = query.replace(",", "")

    var rpc_request = ghiapi.get.contacts
    var rpc_params = {'query': query}

    var data_table = initializeTable(2, rpc_request, rpc_params, function (data_table, d) {
        dataTableWriter(data_table, d)
    })

    $("#search_query").blur()
}

$(document).ready(function () {

    //Initializing data table
    var query = $("#search_query").val()
    trigger_search(query)

    //When contact row in data table is clicked, go to contact page
    $("#contacts").delegate("tr", "click", function (e) {
        var row_data = data_table.fnGetData(this)
        var clicked_id = row_data[0]

        change_hash(e, "contact?c=" + clicked_id)
    });

    setupSearchEvents()
    setupDownloadQuery("contacts", "Contacts")

});