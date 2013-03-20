$(document).ready(function(){
    var contact1 = null
    var contact2 = null

    // Autocomplete for contacts
    var request = ghiapi.get.contactsjson({})
    request.execute(function(response){
        var contacts_json = JSON.parse(response.contacts_json)

        $("input[name=merge_1]").autocomplete({
            source: contacts_json,
            select: function(e, ui){
                $("input[name=merge_1]").val(ui.item.name)
                contact1 = ui.item.key
            }
        });

        $("input[name=merge_2]").autocomplete({
            source: contacts_json,
            select: function(e, ui){
                $("input[name=merge_2]").val(ui.item.name)
                contact2 = ui.item.key
            }
        });
    })

    $("#merge_go").click(function(){
        if (contact1 && contact2){

            if (contact1 == contact2){
                show_flash("undone", "Select two different contacts to merge them.", true)
            }
            else{
                var params = {'contact1':contact1, 'contact2':contact2}
                var request = ghiapi.merge.contacts(params)
                request.execute(function(response){
                    rpcSuccessMessage(response)
                    refreshPage()
                })
            }
                
        }
        else{
            show_flash("undone", "Select two contacts to merge them.", true)
        }
        
    })
});