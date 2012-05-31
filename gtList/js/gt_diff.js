var GlobalTag = "";
var GlobalTag2 = "";
var table_tag;

//FUNCTIONS
$(document).ready( function () {
    GTdiffCompare();
    var oTable = $('#GTcompare').dataTable( {
        "bPaginate": false,
    });
});

function gup( name ) {
    name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( window.location.href );
    if( results == null )
        return "";
    else
        return results[1];
}

function GTdiffCompare() {
    table_tag = $('#body');
    if (gup ("GlobalTag") != "") {
        GlobalTag = gup ("GlobalTag");
    }
    if (gup ("GlobalTag2") != "") {
        GlobalTag2 = gup ("GlobalTag2");
    }
    var returnedData;
    var error = true;
    $.ajax({
        type: 'POST',
        url: 'getGTDiff',
        data: {gt1_name : GlobalTag, gt2_name : GlobalTag2},
        async: false,
        dataType: 'json',
        success: function (data) { returnedData = data; error = false; },
        error: function() { error = true; alert("Error in data send while getting GT Diff List"); parent.$.closeDOMWindow();}
    });
    if ( !error) {
        var html_table = "";
        var temp = "";
        var tagBackground = "";
        var pfnBackground = "";
        var GlobalTag = returnedData["head"]["gt_names"][0]
        var GlobalTag2 = returnedData["head"]["gt_names"][1]
        html_table = "<table id='GTcompare'><thead><tr><th>Record & label</th><th>Tag in " + GlobalTag + "</th><th>PFN in " + GlobalTag +"</th><th>Tag in " + GlobalTag2 + "</th><th>PFN in " + GlobalTag2 +"</th></tr></thead><tbody>";
        var keys = returnedData.body;
        for (var key in keys) {
            tagBackground = "#6AFB92";
            pfnBackground = "#6AFB92";
            if (returnedData.body[key]["pfns_identical"] == false) {
                pfnBackground = "#F75D59";
            }
            if (returnedData.body[key]["tags_identical"] == false) {
                tagBackground = "#F75D59";
            }
            html_table += "<tr><td>" + key + "</td><td style='background-color:" + tagBackground + "'>" + returnedData.body[key]["tags"][0] + "</td><td style='background-color:" + pfnBackground + "'>" + returnedData.body[key]["pfns"][0] + "</td><td style='background-color:" + tagBackground + "'>" + returnedData.body[key]["tags"][1] + "</td><td style='background-color:" + pfnBackground + "'>" + returnedData.body[key]["pfns"][1] + "</td></tr>";
        }
        html_table += "</tbody></table>";
        table_tag.append(html_table);
    }
}

$(function(){
    $("#blocker").hide();
});


