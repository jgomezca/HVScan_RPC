var iovList_array = new Array();
var CMSVersion;
$(document).ready(function() {
    getCMSVersions();
    (function(){ // Import GET Vars
        document.$_GET = [];
        var urlHalves = String(document.location).split('?');
        if(urlHalves[1]){
            var urlVars = urlHalves[1].split('&');
            for(var i=0; i<=(urlVars.length); i++){
                if(urlVars[i]){
                    urlVars[i] = (urlVars[i]).replace(/%20/g," ");
                    urlVars[i] = (urlVars[i]).replace(/\+/g," ");
                    var urlVarPair = urlVars[i].split('=');
                    document.$_GET[urlVarPair[0]] = urlVarPair[1];
                }
            }
        } 
        get_DBS();
        generateTable();
    })();
    $(function(){
        $("#blocker").hide();
    });
    adjustInnerTable();
    var resizeTimer = null;
    $(window).bind('resize', function() {
        if (resizeTimer)
            clearTimeout(resizeTimer);
        resizeTimer = setTimeout(adjustInnerTable, 100);
    });
    $("a.iframe").fancybox({
        'hideOnContentClick': true,
        'width'                 : '100%',
        'height'                : '100%',
        'transitionIn'  :   'elastic',
        'transitionOut' :   'elastic',
        'speedIn'       :   600,
        'speedOut'      :   200,
        'overlayShow'   :   false
    });
});
function get_DBS() {
    $.ajax({
        type: 'GET',
        url: 'get_dbs',
        dataType: "json",
        async: false,
        success: function (data) { 
                                     var html = '<option value=""></option>';
                                     var len = data.length;
                                     for (var i = 0; i < len; i++) {
                                         html += '<option value="' + data[i].DBID+ '"';
                                         if (gup('dbService') == data[i].DBID) {
                                             html += ' selected';
                                             getOptions(data[i].DBID);
                                         }
                                         html += '>' +    data[i].DB + '</option>';
                                     }
                                     $('#DBservice').append(html);
                                     $('#DBservice').change(function(list_item){
                                         getOptions(list_item.target.options[list_item.target.selectedIndex].text);
                                     });
                                  },
        error: function() { CMSVersion = ""; alert("Error in data send while getting dbs"); }
    });
    $(function(){
        $("#blocker").hide();
    });
}

$(function(){
    $("#blocker").hide();
});

function gup( name ) {
    name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( window.location.href );
    if( results == null )
        return "";
    else
        var rez= results[1].replace(/%20/g," ");
        rez = results[1].replace(/\+/g," ");
    return rez;
}

function getOptions(target_value){    
    $.ajax({
        type: 'GET',
        url: 'get_schemas',
        data: { db : target_value },
        dataType : 'json',
        async: false,
        success: function (data) {   
                                     var options = '';
                                     for (var i = 0; i < data.length; i++) {
                                         options += '<option value="' + data[i].Account+ '"';
                                         if (gup('Account') == data[i].Account) {
                                             options += ' selected';
                                         }
                                         options += '>' + data[i].Account + '</option>';
                                     }
                                     $("#Account").html(options);
                                 },
           error: function() { CMSVersion = ""; alert("Error in data send when getting db schemas"); }
    });   
}

function adjustInnerTable() {
    var wsw = $(window).width(); 
    var wsh = $(window).height(); 
    var tableWidth = Math.round((wsw/1.5),0) + 43;
    var widthOfCell = Math.round((((wsw/1.5)-56)/2),0);
    $('table.scrollTable').width(tableWidth);
    $('div.tableContainer').width(tableWidth);
    $('.changingCell').width(widthOfCell);
    $('.changingCell2').width(widthOfCell);
};

function getCMSVersions() {
    $.ajax({
        type: 'POST',
        url: 'get_cmsswReleas',
        async: true,
        success: function (data) { CMSVersion = data;
                                   if (CMSVersion == "") {
                                       $('#cmssw_release').append("<option value='Server down'>Server down</option>");
                                   } else {
                                       $('#cmssw_release').append("<option value=" + CMSVersion + ">" + CMSVersion + "</option>");
                                   }
                                 },
        error: function() { CMSVersion = ""; alert("Error in data send while getting CMS Version"); }
    });
}

var _gaq = _gaq || [];
_gaq.push(['_setAccount', 'UA-1950165-27']);
_gaq.push(['_setDomainName', '.cern.ch']);
_gaq.push(['_trackPageview']);

(function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
})();


function generateTable() {
    if (gup('dbService') != "" && gup('Account') != "") {
        $.ajax({
            type: 'POST',
            url: 'get_lastIovTable',
            data : { dbName : gup('dbService'), acc : gup('Account') },
            async: false,
            success: function (data) {    
                                       $('#container').append(data);
                                       $("#dataCreation").hide();
                                       var getdataCreation = $("#dataCreation").html();
                                       $("#dataBuilding").html(" <b> Last update: </b>"+getdataCreation+" UTC");
                                       $("body").css("background-color","#F0F0F0");
                                     },
            error: function() { alert("Error in data send while getting IOV table"); }
        });
    } 
}
