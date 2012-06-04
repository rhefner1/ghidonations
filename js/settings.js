var impressions = []

function get_mclists(){
    var mc_donorlist = $("#var_donorlist").val()

    $("#mclists_container").html("Loading...")
    var mc_apikey = $("input[name=mc_apikey]").val()

    params = {action : "getMailchimpLists", arg0:JSON.stringify(mc_apikey)}
    rpcGet(params, function(data){
        if (data[0] == true){
            mcl_c = $("#mclists_container")
            mcl_c.hide()
            mcl_c.html("")

            var selector = document.createElement("select")
            mcl_c.append(selector)

            var lists_dict = data[1]

            $.each(lists_dict, function(name, id){
                var new_option = document.createElement("option")
                $(new_option).attr("data-id", id)

                if (mc_donorlist == id){
                    $(new_option).text("* " + name)
                    $(new_option).attr("selected", "selected")
                }
                else{
                    $(new_option).text(name)
                }
                
                $(selector).append(new_option)

                .attr("selected", "selected")

            })

            $("input[name=mc_apikey]").parent().parent().removeClass("red-highlight")
            $("input[name=mc_apikey]").parent().parent().addClass("green-highlight")
            $("#mclists_container").show()
        }
        else{
            show_flash("undone", data[1], true)
            $("input[name=mc_apikey]").parent().parent().removeClass("green-highlight")
            $("input[name=mc_apikey]").parent().parent().addClass("red-highlight")
            $("#mclists_container").html("Failed...")
        }
    })
}

function sort_and_unique(my_array) {
    my_array.sort();
    for ( var i = 1; i < my_array.length; i++ ) {
        if ( my_array[i] === my_array[ i - 1 ] ) {
                    my_array.splice( i--, 1 );
        }
    }
    return my_array;
};

function refreshImpressions(){
    $("#current_impressions").html("")
    impressions = sort_and_unique(impressions)

    count = 0

    $.each(impressions, function(dummy, name){
        var new_div = '<tr data-id="key" style="clear:both; margin-top:10px"></tr>'
        var insert_name = '<td>name</td>'
        var input = '<td><button class="button small" style="margin-left:15px">Remove</></td>'
                
        $("#current_impressions").append(new_div.replace("key", count))
        $("#current_impressions tr[data-id=" + count + "]").append(insert_name.replace("name", name))
        $("#current_impressions tr[data-id=" + count + "]").append(input)

        count += 1
    })
}

$(document).ready(function(){
    var mc_use = $("#var_mcuse").val()
    var use_custom = $("#var_usecustom").val()

    //Get impressions and write to page
    var json_impressions = $("#var_impressions").val()
    impressions = JSON.parse(json_impressions)
    refreshImpressions()

    $("form").validationEngine()


    $("#get_mclists").click(function(){
        get_mclists()
    })

    $("#save").click(function(){
        var validation_result = $("form").validationEngine('validate')
        if (validation_result == true){
            var name = $("input[name=name]").val()
            var email = $("input[name=email]").val()
            var mc_use = Boolean($("input[name=mc_use]:checked").val())

            if (mc_use == true){
                var mc_apikey = $("input[name=mc_apikey]").val()
                var mc_donorlist = $("#mclists_container select option:selected").attr("data-id")
            }
            else{
                var mc_apikey = null
                var mc_donorlist = null
            }
            
            var paypal_id = $("input[name=paypal_id]").val()

            var amount1 = $("input[name=amount1]").val()
            var amount2 = $("input[name=amount2]").val()
            var amount3 = $("input[name=amount3]").val()
            var amount4 = $("input[name=amount4]").val()
            var use_custom = Boolean($("input[name=use_custom]:checked").val())

            var confirmation_header = $("textarea[name=confirmation_header]").val()
            var confirmation_info = $("textarea[name=confirmation_info]").val()
            var confirmation_footer = $("textarea[name=confirmation_footer]").val()
            var confirmation_text = $("textarea[name=confirmation_text]").val()

            var wp_url = $("input[name=wp_url]").val()
            var wp_username = $("input[name=wp_username]").val()
            var wp_password = $("input[name=wp_password]").val()

            var params = ["updateSettings", name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions,
                    amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text,
                    wp_url, wp_username, wp_password]

            //Flash message
            show_flash("setting", "Updating settings...", false)

            rpcPost(params, function(data){
                refreshPage()
            })        
        }
    })

    $("#new_impression button").click(function(event){
        event.preventDefault();
        
        var name = $("#new_impression input").val()
        if (name != ""){
            impressions.push(name)
            $("#new_impression input").val("")
            $("#new_impression input").focus()

            //Refresh impressions page
            refreshImpressions()
        }
        
    })

    $("#current_impressions").delegate("button", "click", function(){
        //Delete the thing from array
        var impression_index = $(this).parent().parent().attr("data-id")
        impressions.splice(impression_index, 1)

        $(this).parent().parent().remove()
    })

    $("input[name=mc_apikey]").blur(function(){
        get_mclists()
    })

    //WYSIWYG Editor
    $("textarea[name=confirmation_text]").cleditor({
        height: 500
    });
    $(".cleditor").cleditor()

    if (mc_use == "True"){
        $("#mc_yes").attr("checked", "checked")
        $("#mc_additional").fadeIn()
        get_mclists()
    }
    else{
        $("#mc_no").attr("checked", "checked")
        $("#mc_additional").fadeOut()
    }

    if (use_custom == "True"){
        $("#use_custom").attr("checked", "checked")
    }

    $("input[name=mc_use]").change(function(){
        if ($("input[name=mc_use]:checked").val() == "yes"){
            $("#mc_additional").slideDown()
        }
        else{
            $("#mc_additional").slideUp()
        }
    })

});