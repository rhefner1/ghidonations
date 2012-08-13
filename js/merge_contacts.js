$(document).ready(function(){
    var contact1 = null
    var contact2 = null

    // Autocomplete for contacts
    params = {"action" : "getContactsJSON"}
    var url = '/rpc?' + $.param(params)
    $.getJSON(url, function(data){
        $("input[name=merge_1]").autocomplete({
            source: data,
            select: function(e, ui){
                $("input[name=merge_1]").val(ui.item.name)
                contact1 = ui.item.key
            }
        });

        $("input[name=merge_2]").autocomplete({
            source: data,
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
                var params = ["mergeContacts", contact1, contact2]

                rpcPost(params, function(data){
                    refreshPage()
                })
            }
                
        }
        else{
            show_flash("undone", "Select two contacts to merge them.", true)
        }
        
    })
});