__setFooter = function (tableName, names) {

        var output = "";
        output += '<tfoot><tr>';
        for (var i in names) {
            if (names[i].bVisible == undefined || names[i].bVisible == true) {
                output += '<th>' + names[i].sTitle + '</th>';
            }
        }
        output += '</tr></tfoot>';
        $(tableName).append(output);

}


);
    jQuery.ajax({
        url: source,
        dataType: 'json',
        success: function (json) {
            if (json.aaSorting == undefined) {
                json.aaSorting = [];
            }
            oTable = $(tableName).dataTable( {
                "aaData" : json.aaData,
                "aoColumns" : json.aaColumns,
                "aaSorting": json.aaSorting
            } );
            __setFooter(tableName, json.aaColumns);
            $.unblockUI();

        }
    });


}
