$(document).ready(function(){
    var contact = null

    // Autocomplete for contacts
    params = {"action" : "getContactsJSON"}
    var url = '/rpc?' + $.param(params)
    $.getJSON(url, function(data){
        $("input[name=contact]").autocomplete({
            source: data,
            select: function(e, ui){
                $("input[name=contact]").val(ui.item.name)
                contact = ui.item.key
            }
        });
    })

    $("#generate").click(function(){
        var year = $("input[name=year]").val()
        if (contact && year){

            var params = {"c" : contact, "y" : year}
            var url = '/reports/donor?' + $.param(params)

            window.open(url, "_blank")
                
        }
        else{
            show_flash("undone", "Select both a contact and a year.", true)
        }
        
    })
});