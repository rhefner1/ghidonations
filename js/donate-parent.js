// This file resides on the parent page of the donate iframe.
// To support the autodesignation function (where the team and
// individual IDs can be passed as parameters in the URL), this
// file performs the communication between the URL and the iframe.

var TARGET_HOST = "https://5s-dot-ghidonations.appspot.com";

function getUrlVars() {
    var vars = [], hash;
    var url = document.referrer;
    var hashes = url.slice(url.indexOf('?') + 1).split('&');
    for (var i = 0; i < hashes.length; i++) {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

// Check if team and individual are provided
var url_vars = getUrlVars();
var team_key = url_vars['t'];
var individual_key = url_vars['i'];

if (team_key != null && individual_key != null) {
    // Removing parameters from URL
    // var location_temp = window.location.href.toString();
    // location_temp = location_temp.replace(window.location.search, "");
    // history.replaceState({}, "", location_temp);

    // Letting iframe know what team and individual have been selected
    var send_values = JSON.stringify({'t': team_key, 'i': individual_key});
    window.top.frames[0].postMessage(send_values, TARGET_HOST);
}