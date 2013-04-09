var home_page = $("#home_page").val()
var previous_hash_params = {}
var previous_hash_base = ""
var ghiapi = null

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

function change_hash(e, location){
    if (e.ctrlKey){
        window.open("#" + location, "_blank")
    }
    else{
        window.location.hash = location
    }  
}

function bind_hashchange(){
    $(window).hashchange(function(){
        // Fires every time the hash changes!  This thing is pretty jimmy rigged.
        var hash = window.location.hash
        var parameters = {}

        if (hash !== ""){
            var location = hash.substr(1)
            var location_split = location.split("?")
            
            if (location_split[0] != previous_hash_base){
                // If the base page changes, trigger change_tab
                change_tab(location)
            }
            else{
                if (location_split[1]){
                    //If there are parameters, deparam them
                    parameters = $.deparam(location_split[1])
                }
                
                difference = diff(previous_hash_params, parameters)
                var search_change = false
                var other_change = false
                for (var key in difference){
                    // If there is a search difference, throw flag
                    if (key == "search"){
                        search_change = true
                    }
                    // If there is any other difference in the parameter, throw flag
                    else{
                        other_change = true
                    }
                }

                // If any part of the parameters changed besides search, change tab like normal
                if (other_change == true){
                    change_tab(location)
                }
                // But if search is the only thing that changed, insert query into box and fire
                else if(search_change == true){
                    var query = parameters["search"]
                    if (query == null){
                        query = ""
                    }
                    
                    $("#search_query").val(query)
                    trigger_search(query)
                }
            }
        }

        else{
            window.location.hash = home_page
            change_tab(home_page)
        }

        //Saving these parameters for comparison next time
        if (location_split){
            previous_hash_base = location_split[0]
        }
        else{
            previous_hash_base = ""
        }

        previous_hash_params = parameters
    })
}

function change_search_hash(query){
    var hash = window.location.hash.split("?")
    if (hash[1]){
        var parameters = $.deparam(hash[1])
        parameters["search"] = query
    }
    else{
        var parameters = {"search" : query}
    }

    hash = hash[0] + "?" + $.param(parameters)
    window.location.hash = hash   
}

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

function setupSearchEvents(){
    $("#search_query").focus(function(){
        $("#search_help").slideDown()
    })

    $("#search_query").focusout(function(){
        $("#search_help").slideUp()
    })

    $("#search_go").click(function(){
        var query = $("#search_query").val()
        change_search_hash(query)
    })
        

    $("#search_query").keyup(function(e){
        if (e.keyCode == 13){
            $("#search_go").click()
        }
    })
}

// ---- DataTables ---- //
var cursors_dict = {0:null}
var data_loading = false
var current_page = 0
var data_table = null

var pub_rpc_request = null
var pub_rpc_params = null
var pub_callback = null

function initializeTable(num_columns, rpc_request, rpc_params, callback){
    //Making these variables public
    pub_rpc_params = rpc_params
    pub_rpc_request = rpc_request
    pub_callback = callback

    // Reset cursor dict
    cursors_dict = {0:null}

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
            "sEmptyTable": " "
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
    
    //Setting page to 0
    current_page = 0

    //AJAX Controls
    $(".ui-corner-left").unbind("click")
    $(".ui-corner-right").unbind("click")

    $(".ui-corner-right").click(function(){
        if (data_loading == false){
            data_loading = true
            $(this).effect("highlight", {}, 3000);

            try{
               current_page += 1
               pageThrough(data_table, current_page, rpc_request, rpc_params, callback)  
            }
            catch(e){
                current_page -= 1
                pageThrough(data_table, current_page, rpc_request, rpc_params, callback) 
            }
             
        } 
    })

    $(".ui-corner-left").click(function(){
        if (data_loading == false){
           data_loading = true
           $(this).effect("highlight", {}, 3000);

            if (current_page >= 1){
                try{
                    current_page -= 1 
                    pageThrough(data_table, current_page, rpc_request, rpc_params, callback) 
                }
                catch(e){
                    current_page += 1
                    pageThrough(data_table, current_page, rpc_request, rpc_params, callback) 
                }
            } 
            else{
                show_flash("setting", "There isn't any more data to show.", true)
                pageThrough(data_table, current_page, rpc_request, rpc_params, callback) 
            } 
        }
    })

    pageThrough(data_table, current_page, rpc_request, rpc_params, callback)
    return data_table
}

function pageThrough(data_table, page_number, rpc_request, rpc_params, callback){
    try{
        var query_cursor = cursors_dict[page_number]
    }
    catch(e){
        var query_cursor = "end" 
    }

    if(query_cursor == "end"){
        show_flash("setting", "There isn't any more data to show.", true)
        throw "No more data"
    }
    
    if (query_cursor != null){
        query_cursor = query_cursor
    }

    // -- RPC to get donations -- //
    var params = {'action':rpc_request, 'query_cursor':query_cursor}

    //Adding additional parameters to params dictionary
    if (rpc_params != null){
        params = $.extend(params, rpc_params)
    }

    $("#search_icon").hide()
    $("#search_loading").show()

    var request = rpc_request(params)
    request.execute(function(response){
        $("#search_loading").hide()
        $("#search_icon").show()

        data_table.fnClearTable()

        if (response.objects){

            $.each(response.objects, function(index, d){
                callback(data_table, d)
            })
        }
        

        if (response.new_cursor == null){
            var new_cursor = "end"
        }
        else{
            var new_cursor = response.new_cursor
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

        cursors_dict = {0:null}
        data_loading = false
        current_page = 0
        data_table = null

        pub_rpc_request = null
        pub_rpc_params = null
        pub_callback = null
    }    
}

function refreshTable(){
    pageThrough(data_table, current_page, pub_rpc_request, pub_rpc_params, pub_callback)
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

function rpcSuccessMessage(response){
    if (response.success == true){
        show_flash("done", response.message, true)
    }
    else{
        if (response.error_message){
            message = response.error_message
        }
        else{
            message = response.message
        }
        
        try{
            if (message == ""){
                message = "An error occurred."
            }
            else if(message == "Internal Server Error"){
                message = "Uh oh! The server's not playing nice right now. Try again later."
            }
        }
        catch(err){
            message = "An error occurred."
        }

        show_flash("undone", message, false)
        throw "Server error"
    }
}

// ---- Spreadsheet Download Controllers ---- //
function checkTaskStatus(response){
    var params2 = {"job_id":response.job_id}
    var request2 = ghiapi.spreadsheet.check(params2)

    request2.execute(function(response2){

        if (response2.completed == true){
            var url = "/ajax/spreadsheet/download?blob_key=" + response2.blob_key
            window.open(url)

            $("#download_query").html('Downloading now...')
            setTimeout(function(){
                $("#download_query").html('<button class="small button">Download query as a spreadsheet</button>')
            }, 5000)
        }
        else{
            // If the report isn't done generating, check again in 10 sec.
            timeoutCheckStatus(response)
        }

    })
}

function setupDownloadQuery(mode, file_name){
    $("#download_query").delegate("button", "click", function(){
        $(this).hide()
        $("#download_query").html("Generating report - this may take a moment. <img src='/images/ajax-loader.gif'>")

        query = $("#search_query").val()
        params = {"mode":mode, "filename":file_name, "query" : query}
        var request = ghiapi.spreadsheet.start(params)

        request.execute(function(response){
            timeoutCheckStatus(response)
        })


    })
}

function timeoutCheckStatus(response){
    setTimeout(function(){
        checkTaskStatus(response)
    }, 5000)
}

// ---- Utilities ---- //
function diff(obj1,obj2) {
    var newObj = $.extend({},obj1,obj2);
    var result = {};
    $.each(newObj, function (key, value) {
        if (!obj2.hasOwnProperty(key) || !obj1.hasOwnProperty(key) || obj2[key] !== obj1[key]) {
            result[key] = [obj1[key],obj2[key]];
        }
    });

    return result;
}

function initializeAPI(){
    // Load GHI Donations API
    var ROOT = '/_ah/api';
    gapi.client.load('ghidonations', 'v1', function() {
        ghiapi = gapi.client.ghidonations

        // Trigger the event to load first page
        $(window).hashchange();
    }, ROOT); 

}

$(document).ready(function(){ 
    if (ghiapi == null){
        show_flash("setting", "Loading GHI Donations...", false)
    }

    //Function to check if an element exists
    jQuery.fn.exists = function() {
        return jQuery(this).length > 0;
    }

    $(document).bind('cbox_open', function(){
        colorbox_open = true
    });

    $(document).bind('cbox_closed', function(){
        colorbox_open = false

        var on_review_queue = window.location.hash.indexOf("#review")
        if (loading == false & on_review_queue != -1){
            var t=setTimeout(function(){refreshTable()}, 1000)
        }

        $("#" + current_container).css("display", "none")
    });
        
    // Bind the event.
    bind_hashchange()

    $("#refresh").click(refreshPage)

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
                show_flash("undone", "Uh oh! I don't understand something on this page. Try again later.", true)
            } else if (exception === 'timeout') {
                show_flash("undone", "Hmm... the server's not responding. Try your request again.", true)
            } else {
                show_flash("undone", "Uh oh, something happened but I don't know what it is - " + jqXHR.responseText, true)
            }
        }
    });

    //This is necessary for the theme to function
    $("ul.sf-menu").superfish(); // Superfish Menus!

    $("#myaccount").click(function() {
        $("#logindrop").toggle("slow");
        return false;
    });

    $("#logindrop a").click(function(){
        $("#logindrop").toggle("slow");
    })

    $("#search").click(function() {
        $("#searchdrop").toggle("slow");
        return false;
    });
    
    $(".notification").click(function() {
        $(this).fadeOut("slow");
    });
});