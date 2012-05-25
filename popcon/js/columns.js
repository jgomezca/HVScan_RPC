var oTable; 

__setFooter = function (tableName, names) {

        var output = "";
        output += '<tr>';
        for (var i in names) {
            //if (names[i].bVisible == undefined || names[i].bVisible == true) {
                output += '<th>' + names[i].sTitle + '</th>';
            //}
        }
        output += '</tr>';
        $(tableName + ' tfoot').append(output);

}

function processColumns(data) {
    returnList = [];
    for (var i in data) {
        if (data[i].bVisible == undefined || data[i].bVisible == true)
            visible = 1;
        else
            visible = 0;
        returnList[i] = {'visible': visible, 'title': data[i].sTitle};
    }
    return returnList;
}

function drawList(data) {
    output = "";
    for (var i in data) {
        output += "<ul><li>";
        //
        output += "<input type='checkbox' name='columns' onClick='fnShowHide(" + i.toString() + ");setVis(" + i.toString() + ");'";
        if (data[i].visible == 1)
            output += " checked='checked'";
        output += " />";
        output += " " + data[i].title;
        output += "</li></ul>";
    }

    //jQuery part
    output += "</ul>"
    $("#list").html(output);
}

function processCookies(name, data) {
    dataFromCookies = $.cookie(name);
    if (dataFromCookies == undefined) {
        cookieData = "";
        for (var i in data) {
            cookieData += data[i].visible + "_";
        }
        $.cookie(name, cookieData, {'expires': 7});
    } else { 
        cookieData = $.cookie(name).split("_");
        for (var i in data) {
            if (data[i].visible != cookieData[i])
                fnShowHide(i);

            data[i].visible = cookieData[i];
        }
    }
    return data;
}

function setVis(id) {
    data = $.cookie('columns').split("_");
    output = "";
    for (var i in data) {
        if (data[i] != "_" && data[i] != "") {
            if (i == id) {
                if (data[i] == "0")
                    output += "1_";
                else
                    output += "0_";
            } else {
                output += data[i] + "_";
            }
        }
    }
    $.cookie('columns', output, {'expires': 7});
}

// Sort
function trim(str) {
	str = str.replace(/^\s+/, '');
	for (var i = str.length - 1; i >= 0; i--) {
	    if (/\S/.test(str.charAt(i))) {
	        str = str.substring(0, i + 1);
	        break;
	    }
	}
	return str;
}


function drawTable(tableName, srcUrl) {
 $.blockUI({ message: $('#processing')});
    jQuery.ajax({
        url: srcUrl,
        dataType: 'json',
        success: function (json) {
            if (json.aaSorting == undefined) {
                json.aaSorting = [];
            }
            __setFooter(tableName, json.aaColumns);
            oTable = $(tableName).dataTable( {
        "fnDrawCallback": function() {
            fix_table_size();
        },
		"bAutoWidth": false,
                "aaSorting": json.aaSorting,
                "aoColumns" : json.aaColumns,
                "aaData" : json.aaData,
		"bJQueryUI": true,
		"sPaginationType": "full_numbers"
            } );
            new FixedHeader( oTable );
            var columnsData = processColumns(json.aaColumns)
            columnsData = processCookies('columns', columnsData);
            drawList(columnsData)
            $.unblockUI();
        }
    });
}

function fnShowHide(iCol) {
    if (oTable != undefined) {
        var bVis = oTable.fnSettings().aoColumns[iCol].bVisible;
        oTable.fnSetColumnVis( iCol, bVis ? false : true );
    }
}
function fix_table_size(){
$('table#example').css('width', $('body').width()-10)
$('div.fg-toolbar').css('width', $('body').width()-25)
$('tr').css('word-wrap','break-word')
$('td').css('max-width',40)
$('div#footer').css('width',$('body').width()-45)
}
