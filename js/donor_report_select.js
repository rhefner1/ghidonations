$(document).ready(function(){
    var contact = null
    var contact_email = null

    // Autocomplete for contacts
    params = {"action" : "getContactsJSON"}
    var url = '/rpc?' + $.param(params)
    $.getJSON(url, function(data){
        $("input[name=contact]").autocomplete({
            source: data,
            select: function(e, ui){
                $("input[name=contact]").val(ui.item.name)
                contact = ui.item.key
                contact_email = ui.item.email
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

    $("#sendemail").click(function(){
        if (contact_email && contact_email != ""){
            var year = $("input[name=year]").val()
            var params = ["emailAnnualReport", contact, year]

            rpcPost(params, function(data){
                refreshPage()        
            })
        }
        else{
            show_flash("undone", "Contact doesn't have an email address.", true)
        }
    })
});