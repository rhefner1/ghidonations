jQuery.fn.dataTableExt.oApi.fnTruncateCells = function (oSettings, aiColumnMaxChars) {
    /*
    * Type:        Plugin for DataTables (www.datatables.net) JQuery plugin.
    * Name:        dataTableExt.oApi.fnTruncateCells
    * Version:     1.0.0
    * Description: Truncates table cells to length specified in <th data-maxChars> attribute. 
    *              Puts ellipses in place of last 3 characters, and pre-truncated
    *              cell data in cell's title attribute.
    * Inputs:      object:oSettings - dataTables settings object
    *              array: aoColumnMaxChars - an array, element 0 being left most, containing a positive integer or null for each column.
    *              Null means do not truncate column, positive integer means to only allow that many characters to display in the column text. 
    *
    * Returns:     JQuery
    * Usage:       $('#example').dataTable().fnTruncateCells();
    * Requires:	  DataTables 1.7.0+
    *
    * Author:      Justin Pate
    * Created:     26/7/2012
    * Language:    Javascript
    * License:     GPL v2 or BSD 3 point style
    * Contact:     justin.pate /AT\ gmail.com
    */
    this.each(function (i) {
        $.fn.dataTableExt.iApiIndex = i;
        var baseFunction = (oSettings.fnRowCallback) ? oSettings.fnRowCallback : function () { };
        oSettings.fnRowCallback = function (nRow) {
            baseFunction(nRow);
            $('td', nRow).each(function (index) {
                var maxChars = (typeof aiColumnMaxChars !== 'undefined') ? aiColumnMaxChars[index] : oSettings.aoColumns[index].nTh.getAttribute("data-maxChars");
                if (maxChars) {
                    var unfilteredText = $(this).text();
                    if (unfilteredText.length > maxChars && maxChars > 3) {
                        $(this).attr("title", unfilteredText);
                        $(this).html(unfilteredText.substring(0, maxChars) + "...");
                    }
                }
            });
            return nRow;
        };
        return this;
    });
    return this;
};

/* Example call */
/*$(document).ready(function () {

//looks for maxChars in <th data-maxChars="5"></th> html markup
$('.dataTable').dataTable().fnTruncateCells();

//use from javascript
$('.dataTable').dataTable().fnTruncateCells([20, null, 10, null, null, 10]);

});*/
