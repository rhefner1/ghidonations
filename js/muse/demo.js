$(function() {

    // Autocomplete
    var countryList = ["Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antarctica", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burma", "Burundi", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo, Democratic Republic", "Congo, Republic of the", "Costa Rica", "Cote d'Ivoire", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Greenland", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea, North", "Korea, South", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Mongolia", "Morocco", "Monaco", "Mozambique", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Norway", "Oman", "Pakistan", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Samoa", "San Marino", " Sao Tome", "Saudi Arabia", "Senegal", "Serbia and Montenegro", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "Spain", "Sri Lanka", "Sudan", "Suriname", "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"];
    $("#countries").autocomplete({
        source: countryList
    });

    // Accordion
    $(".accordion").accordion({ header: "h3" });

    // Tabs
    $('#tabs').tabs();

    // Dialog			
    $('#dialog').dialog({
        autoOpen: false,
        width: 600,
        buttons: {
            "Ok": function() {
                $(this).dialog("close");
            },
            "Cancel": function() {
                $(this).dialog("close");
            }
        },
        modal: true
    });

    // Dialog Link
    $('#dialog_link').button().click(function() {
        $('#dialog').dialog('open');
        return false;
    });

    // Datepicker
    $('#datepicker').datepicker().children().show();

    // Horizontal Slider
    $('#horizSlider').slider({
        range: true,
        values: [17, 67]
    })

    // Vertical Slider				
    $("#eq > span").each(function() {
        var value = parseInt($(this).text());
        $(this).empty().slider({
            value: value,
            range: "min",
            animate: true,
            orientation: "vertical"
        });
    });

    //hover states on the static widgets
    $('#dialog_link, ul#icons li').hover(
        function() {
            $(this).addClass('ui-state-hover');
        },
        function() {
            $(this).removeClass('ui-state-hover');
        }
    );

    // Button
    $("#divButton, #linkButton, #submitButton, #inputButton").button();

    // Icon Buttons
    $("#leftIconButton").button({
        icons: {
            primary: 'ui-icon-wrench'
        }
    });

    $("#bothIconButton").button({
        icons: {
            primary: 'ui-icon-wrench',
            secondary: 'ui-icon-triangle-1-s'
        }
    });

    // Button Set
    $("#radio1").buttonset();


    // Progressbar
    $("#progressbar").progressbar({
        value: 37
    }).width(500);
    $("#animateProgress").click(function(event) {
        var randNum = Math.random() * 90;
        $("#progressbar div").animate({ width: randNum + "%" });
        event.preventDefault();
    });


    //Datatable
    $('.dataTable').dataTable({
        "sPaginationType": "full_numbers",
        "bJQueryUI": true
    });

    //Tooltips
    $("[rel=tooltips]").twipsy({
        "placement": "right",
        "offset": 5
    });

    //WYSIWYG Editor
    $(".cleditor").cleditor();

    //HTML5 Placeholder for lesser browsers. Uses jquery.placeholder.1.2.min.shrink.js
    $.Placeholder.init();


    //Uses formvalidator
    $("#form0, #form1, #form2").validationEngine();

    //Calendar
    var date = new Date();
    var d = date.getDate();
    var m = date.getMonth();
    var y = date.getFullYear();

    $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        editable: true,
        theme: true,
        defaultView: 'agendaWeek',
        events: [
            {
                title: 'All Day Event',
                start: new Date(y, m, 1)
            },
            {
                title: 'Long Event',
                start: new Date(y, m, d - 5),
                end: new Date(y, m, d - 2)
            },
            {
                id: 999,
                title: 'Repeating Event',
                start: new Date(y, m, d - 3, 16, 0),
                allDay: false
            },
            {
                id: 999,
                title: 'Repeating Event',
                start: new Date(y, m, d + 4, 16, 0),
                allDay: false
            },
            {
                title: 'Meeting',
                start: new Date(y, m, d, 10, 30),
                allDay: false
            },
            {
                title: 'Lunch',
                start: new Date(y, m, d, 12, 0),
                end: new Date(y, m, d, 14, 0),
                allDay: false
            },
            {
                title: 'Birthday Party',
                start: new Date(y, m, d + 1, 19, 0),
                end: new Date(y, m, d + 1, 22, 30),
                allDay: false
            },
            {
                title: 'Click for Google',
                start: new Date(y, m, 28),
                end: new Date(y, m, 29),
                url: 'http://google.com/'
            }
        ]
    });

    $('#gcalendar').fullCalendar({
        // US Holidays
        events: 'http://www.google.com/calendar/feeds/usa__en%40holiday.calendar.google.com/public/basic',
        theme: true,

        eventClick: function(event) {
            // opens events in a popup window
            window.open(event.url, 'gcalevent', 'width=700,height=600');
            return false;
        },

        loading: function(bool) {
            if (bool) {
                $('#loading').show();
            } else {
                $('#loading').hide();
            }
        }
    });

});
























// Customize


$(function() {
    
    // Sliding Panel
    $(".trigger").click(function() {
        $(".panel").toggle("slow");
        $(this).toggleClass("active");
        return false;
    });

    // Color Picker for Demo

    $('#in-header').ColorPicker({
        color: '3d0707',
        onShow: function (colpkr) {
            
            $(colpkr).fadeIn(500);
            return false;
        },
        onHide: function (colpkr) {
            $(colpkr).fadeOut(500);
            return false;
        },
        onChange: function (hsb, hex, rgb) {
            $('header').css('backgroundColor', '#' + hex);
            $('#in-header').css('backgroundColor', '#' + hex);
            createCookie('headerCss', hex);
        }
    });

    // Cookies for Demo

    $('#in-nav').ColorPicker({
        color: '222936',
        onShow: function (colpkr) {
            $(colpkr).fadeIn(500);
            return false;
        },
        onHide: function (colpkr) {
            $(colpkr).fadeOut(500);
            return false;
        },
        onChange: function (hsb, hex, rgb) {
            $('nav, nav li, .sf-menu li li, .sf-menu li li li, #sidebar').css('backgroundColor', '#' + hex);
            $('#in-nav').css('backgroundColor', '#' + hex);
            createCookie('navCss', hex);
        }
    });

    $('#in-title').ColorPicker({
        color: '222936',
        onShow: function (colpkr) {
            $(colpkr).fadeIn(500);
            return false;
        },
        onHide: function (colpkr) {
            $(colpkr).fadeOut(500);
            return false;
        },
        onChange: function (hsb, hex, rgb) {
            $('#titlediv').css('backgroundColor', '#' + hex);
            $('#in-title').css('backgroundColor', '#' + hex);
            createCookie('titleCss', hex);
        }
    });

    var headerCss = readCookie('headerCss')
    var navCss = readCookie('navCss')
    var titleCss = readCookie('titleCss')
    var titleBG = readCookie('titleBG')
    var bodyBG = readCookie('bodyBG')

    if (headerCss != null) {
        $('header').css('backgroundColor', '#' + headerCss);
        $('#in-header').css('backgroundColor', '#' + headerCss);
    }

    if (navCss != null) {
        $('nav').css('backgroundColor', '#' + navCss);
        $('nav li').css('backgroundColor', '#' + navCss);
        $('.sf-menu li li').css('backgroundColor', '#' + navCss);
        $('.sf-menu li li li').css('backgroundColor', '#' + navCss);
        $('#in-nav').css('backgroundColor', '#' + navCss);
        $('#sidebar').css('backgroundColor', '#' + navCss);
    }

    if (titleCss != null) {
        $('#titlediv').css('backgroundColor', '#' + titleCss);
        $('#in-title').css('backgroundColor', '#' + titleCss);
    }

    if (titleBG != null) {
        $("#pattern").css("backgroundImage", "url(assets/images/background/" + titleBG + ")");
    }

    if (bodyBG != null) {
        $("body").css("backgroundImage", "url(assets/images/background/" + bodyBG + ")");
    }


    $('#colorChanger').change(function() {
        var str = $(this).val();
        var colors = str.split(',');

        $('header').css('backgroundColor', '#' + colors[0]);
        $('nav, nav li, .sf-menu li li, .sf-menu li li li, #sidebar').css('backgroundColor', '#' + colors[1]);
        $('.pagetitle').css('backgroundColor', '#' + colors[2]);
        $('#in-header').css('backgroundColor', '#' + colors[0]);
        $('#in-nav').css('backgroundColor', '#' + colors[1]);
        $('#sidebar').css('backgroundColor', '#' + colors[1]);
        $('#in-title').css('backgroundColor', '#' + colors[2]);

        //update cookies
        createCookie('headerCss', colors[0]);
        createCookie('navCss', colors[1]);
        createCookie('titleCss', colors[2]);
    });

});

function createCookie(name, value, days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        var expires = "; expires=" + date.toGMTString();
    }
    else var expires = "";
    document.cookie = name + "=" + value + expires + "; path=/";
}
function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}
function eraseCookie(name) {
    createCookie(name, "", -1);
}
// /cookie functions
function changeTitlePattern() {
    var imgfile = $("#titlepattern").val();
    //alert("url(assets/images/background/"+imgfile+")");
    $("#pattern").css("backgroundImage", "url(assets/images/background/" + imgfile + ")");
    createCookie('titleBG', imgfile);
}

function changeBGPattern() {
    var imgfile = $("#backgroundpattern").val();
    //alert("url(assets/images/background/"+imgfile+")");
    $("body").css("backgroundImage", "url(assets/images/background/" + imgfile + ")");
    createCookie('bodyBG', imgfile);
}

function changePreset(){
    var preset = $("#preset").val();
    var presets = preset.split(",");
    $('header').css('backgroundColor', presets[0]);
    $('#in-header').css('backgroundColor', presets[0]);
    $('#in-header').ColorPickerSetColor( presets[0]);
    
    $('nav').css('backgroundColor', presets[1]);
    $('nav li').css('backgroundColor', presets[1]);
    $('#in-nav').css('backgroundColor', presets[1]);
    $('#in-nav').ColorPickerSetColor( presets[1]);
    
    $('#titlediv').css('backgroundColor',  presets[2]);
    $('#in-title').css('backgroundColor',  presets[2]);
    $('#in-title').ColorPickerSetColor( presets[2]);
    
    createCookie('headerCss', presets[0].replace("#",""));
    createCookie('navCss', presets[1].replace("#",""));
    createCookie('titleCss', presets[2].replace("#",""));
    $("#pattern").css("backgroundImage", "url(assets/images/background/" + presets[3] + ")");
    createCookie('titleBG', presets[3] );
    $("body").css("backgroundImage", "url(assets/images/background/" + presets[4] + ")");
    createCookie('bodyBG', presets[4]);
}