$(document).ready(function(){
    var contact = null
    var contact_email = null

    // Autocomplete for contacts
    var params = {}
    var request = ghiapi.get.contacts_json(params)

    request.execute(function(response) {
        $("input[name=contact]").autocomplete({
            source: JSON.parse(response.json_data),
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
            var params = {'contact_key':contact, 'year':year}

            var request = ghiapi.confirmation.annual_report(params)
            request.execute(function(response){
                rpcSuccessMessage(response)
                refreshPage()
            })
        }
        else{
            show_flash("undone", "Contact doesn't have an email address.", true)
        }
    })
});