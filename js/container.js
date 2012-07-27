var home_page = $("#home_page").val()

// ---- Show flash message ---- //
function show_flash(type, message, fade){
    $("#flash_message").fadeOut(function(){
        $("#flash_message").html("")
        
        var banner = '<span class="notification banner_type">banner_message</span>'
        banner = banner.replace("banner_type", type).replace("banner_message", message)
        $("#flash_message").html(banner)
        $("#flash_message").fadeIn()

        if (fade === true){
            var t = setTimeout("hide_flash()", 10000)
        }
        
    })
}

function hide_flash(){
    $("#flash_message").fadeOut()
}

// ---- AJAX setup ---- //
var current_colorbox = null
var current_container = null
var loading = false
var colorbox_open = false

function change_tab(location)
{
    loading = true

    $.colorbox.close()

    show_flash("setting", "Loading page...", false)

    $("#actualbody").fadeOut(300, function(){
        //To prevent page flashing before the fadeOut is finished
        $.ajax({
            url: "/ajax/" + location,
            cache: false, 
            success: function(html){

                $("#actualbody").html(html);
                hide_flash()

                //If we lost the auth cookie, bounce back to login screen instead of loading that in the body
                if ($("#login_form").exists()){
                    window.location = "/login"
                }
                else {
                    $("#actualbody").fadeIn(300)
                    $("#refresh").attr("href", window.location.hash) 
                }                
            }
        });
    })

    loading = false
}

// ---- DataTables ---- //
var cursors_dict = {0:null}
var data_loading = false
var current_page = 0
var data_table = null

var pub_rpc_action = null
var pub_rpc_params = null
var pub_callback = null

function initializeTable(num_columns, initial_cursor, rpc_action, rpc_params, callback){
    //Making these variables public
    pub_rpc_action = rpc_action
    pub_rpc_params = rpc_params
    pub_callback = callback

    var column_array = [{bVisible:false}]

    var i=0;
    for (i=0; i<num_columns; i++)
    {
        //Makes an array that DataTables likes for formatting
        column_array.push(null)
    }

    if (data_table){
        //Destroy a table if it exists
        data_table.fnDestroy()
    }

    //Set up Datatable
    data_table = $(".dataTable").dataTable({
        "sPaginationType": "two_button",
        "bJQueryUI": true,
        "bVisible" : true,
        "bDestroy": true,
        "bAutoWidth" : true,

        "oLanguage": {
            "sEmptyTable": "No data here."
        },

        //Disable some features
        "bLengthChange": false,
        "bFilter": false,
        "bSort": false,
        "bInfo": false,
        "iDisplayLength": 15,

        "aoColumns" : column_array
    });

    $(".dataTable").css("width", "100%")

    //Setting initial database cursor
    if (initial_cursor == "None"){
        cursors_dict[1] = "end"
    }
    else{
        cursors_dict[1] = initial_cursor
    }
    
    //Setting page to 0
    current_page = 0

    //AJAX Controls
    $(".ui-corner-left").unbind("click")
    $(".ui-corner-right").unbind("click")

    $(".ui-corner-right").click(function(){
        if (data_loading == false){
            data_loading = true
            $(this).effect("highlight", {}, 3000);

            current_page += 1
            pageThrough(data_table, current_page, rpc_action, rpc_params, callback)
        } 
    })

    $(".ui-corner-left").click(function(){
        if (data_loading == false){
           data_loading = true
           $(this).effect("highlight", {}, 3000);

            if (current_page >= 1){
                current_page -= 1
                pageThrough(data_table, current_page, rpc_action, rpc_params, callback)
            }  
        }
        
    })

    return data_table
}

function pageThrough(data_table, page_number, rpc_action, rpc_params, callback){
    var query_cursor = cursors_dict[page_number]

    if(query_cursor == "end"){
        show_flash("setting", "There isn't any more data to show.", true)
        return
    }
    else if (query_cursor != null){
        query_cursor = JSON.stringify(query_cursor)
    }

    // -- RPC to get donations -- //
    var params = {action: rpc_action, arg0:query_cursor}

    //Adding additional parameters to params dictionary
    if (rpc_params != null){
        var current_arg = 1
        for (p in rpc_params){
            var param_name = "arg" + current_arg.toString()
            params[param_name] = JSON.stringify(rpc_params[p])
        }
    }

    rpcGet(params, function(data){
        data_table.fnClearTable()

        $.each(data[0], function(status, d){
            callback(data_table, d)
        })

        if (data[1] == null){
            var new_cursor = "end"
        }
        else{
            var new_cursor = data[1]
        }
        
        cursors_dict[page_number + 1] = new_cursor

        data_table.fnAdjustColumnSizing()

        data_loading = false
    })   
}

function htmlDecode(input){
  var e = document.createElement('div');
  e.innerHTML = input;
  return e.childNodes.length === 0 ? "" : e.childNodes[0].nodeValue;
}

// ---- Colorbox ---- //
//Initialize Colorbox
function loadColorbox(url, container){
    current_colorbox = url
    current_container = container
    //console.log("Loading url: " + url + " in container: " + container)

    $.get(url, function(data) {
        $("#" + container).html(data);
        $("#" + container).css("display", "block")

        if ($("#login_page").exists()){
            window.location = "/login"
        }
        else{
            $.colorbox({inline:true, href:"#" + container, width:"80%", height:"80%"})
        } 
    });
}

//Closes Colorbox
function closeColorbox(){
    $.colorbox.close()
}

function refreshPage(){
    if (colorbox_open == true){
        loadColorbox(current_colorbox, current_container)
    }
    else{
        var hash = window.location.hash
        var location = hash.substr(1)
        change_tab(location)
    }    
}

function refreshTable(){
    pageThrough(data_table, current_page, pub_rpc_action, pub_rpc_params, pub_callback)
}

function rpcGet(data, callback){
    var url = '/rpc?' + $.param(data)
    $.getJSON(url, function(data){
        callback(data)
    })
}

function rpcPost(data, callback){
    $.ajax({type: "post",
            url: "/rpc",
            data: $.toJSON(data), 
            success: function(data) {
                data = JSON.parse(data)
                if (data[0] == true){
                    show_flash("done", data[1], true)
                    callback(data)
                }
                else{
                    
                    try{
                        message = data[1]
                        if (message == ""){
                            message = "An error occurred."
                        }
                    }
                    catch(err){
                        message = "An error occurred."
                    }

                    show_flash("undone", data[1], true)
                }
            }
        });
}

$(document).ready(function(){
    //Function to check if an element exists
    jQuery.fn.exists = function() {
        return jQuery(this).length > 0;
    }

    $(document).bind('cbox_open', function(){
        colorbox_open = true
    });

    $(document).bind('cbox_closed', function(){
       colorbox_open = false

       if (loading == false & window.location.hash == "#review"){
            refreshTable()
        }

        $("#" + current_container).css("display", "none")
    });
        
    // Bind the event.
    $(window).hashchange( function(){
        // Fires every time the hash changes!
        var hash = window.location.hash

        if (hash !== ""){
            var location = hash.substr(1)
            change_tab(location)
        }

        else{
            window.location.hash = home_page
            change_tab(home_page)
        }
    })

    // Trigger the event (useful on page load).
    $(window).hashchange();

    $("#refresh").click(function(){
        refreshPage()
    })

    //Set up AJAX
    $.ajaxSetup({
        error: function(jqXHR, exception) {
            if (jqXHR.status === 0) {
                show_flash("undone", "I couldn't connect to the Internet. Check your connection.", true)
            } else if (jqXHR.status == 404) {
                show_flash("undone", "Whoops! I couldn't find that page.", true)
            } else if (jqXHR.status == 500) {
                show_flash("undone", "Uh oh! The server's not playing nice right now. Try again later.", true)
            } else if (exception === 'parsererror') {
                show_flash("undone", "Uh oh! The server gave me something I don't understand. Try again later.", true)
            } else if (exception === 'timeout') {
                show_flash("undone", "Hmm... the server's not responding. Try your request again.", true)
            } else {
                show_flash("undone", "Uh oh, something happened but I don't know what it is - " + jqXHR.responseText, true)
            }
        }
    });
});