var globalTagList;
var GlobalTag = "";
var GlobalTag2 = "";
var CMSVersion = "";
var tagNameEnterForm;
var GTDiffAppendTag;
var secTagEnterField;
var _currentTime;
var cmsReleaseTag;
var tableContainer;
var globalTagNameField;

//FUNCTIONS
$(document).ready(function(){
    msg    = "Refresh Global Tag<br><h2>"+$('#suggest1').val()+"</h2>"
    tagNameEnterForm = $('#tagEnter');
    GTDiffAppendTag = $('#GTDiffTag');
    secTagEnterField = $('#secondTagNAmeField');
    _currentTime = $('#currentTime');
    cmsReleaseTag = $('#cmssw_release');
    tableContainer = $('#container');
    globalTagNameField = $('#GlobalTagNameField');

    getCMSVersions();
    if (gup ("GlobalTag") != "") {
        GlobalTag = gup ("GlobalTag");
    }
    if (gup ("GlobalTag2") != "") {
        GlobalTag2 = gup ("GlobalTag2");
    }
    loadData(GlobalTag, GlobalTag2);
    if(globalTagList[0]!='ServerDown' && $.inArray(GlobalTag, globalTagList)==-1){
        alert("The Global Tag entered, " + GlobalTag + ", is wrong or missing.\nPlease select another Global Tag from the input box!!!! Data will be loaded for GT GR_P_V32!!!");
        GlobalTag = "GR_P_V32";
    }
    if($('#fileNotAvailable').html()=="" && $.inArray(GlobalTag, globalTagList)!=-1){
        var answer = confirm("The Global Tag " + GlobalTag + " has never been produced.\nDo you want to produce for the first time?");
        if (answer){
            refresh_backend();
        }
    }

    globalTagNameField.html(GlobalTag);
    tagNameEnterForm.append('<input type="text" name="GlobalTag" id="suggest1" value=' + GlobalTag +'><input type="submit" value="Submit new GT"><input type="button" id="RefrButt"value="Refresh to update"onClick="javascript: document.url=\'<?=$config[\'url\'][\'request\']?>uploadGT?tag=TEST\'">');
    GTDiffAppendTag.append('<a id="GTdiff" title="difference between ' + GlobalTag + ' and ' + GlobalTag2 + '" href="#"></a>');
    secTagEnterField.append('<input type="text" name="GlobalTag2" id="suggest2" value=' + GlobalTag2 +'><input type="button" id="GTCompare" value="Compare" style=\'//text-decoration: blink;\'>');
    setTable();

    $(".msg_body").hide();
    $(".msg_head").click(function(){
        $(this).next(".msg_body").slideToggle(250);
        if ($(this).hasClass('close_head'))
            $(this).removeClass('close_head').addClass('open_head');
        else
            $(this).removeClass('open_head').addClass('close_head');
    });

    if($(document).getUrlParam("cmssw_release")){
        var cmssw_release_val   =   $(document).getUrlParam("cmssw_release");
        $('#cmssw_release').find("option[value='"+cmssw_release_val+"']").attr("selected","selected");
    }

    $('#cmssw_release').change(function(){
        window.location.href="gtlist/?cmssw_release="+$(this).val();
    });


    $("#alert_link").fancybox({'type'        : 'iframe','onComplete':setTimeout(fix_fancybox_frame_size,1500)});
    $(".col3").append($("#creation_time").html());
    var limitInMinutes = 20;
    reloadData($(".col3 b").html(), limitInMinutes);
    reloadPage($(".col3 b").html(), limitInMinutes, 1);
    updateCurrentTime();
    if(globalTagList[0]=='ServerDown'){
       $('#alert_link').attr('href', ('gtlist/message-box.html?msg_name=Server Not Available'));
       $('#alert_link').click();       
    }

    $('#GTdiff').openDOMWindow({ 
        width:($('body').width()*0.9), 
        height:($(window).height()*0.9), 
        eventType:'click', 
        windowSource:'iframe', 
        windowPadding:0, 
        loader:1, 
        loaderImagePath:'image/ajaxloader.gif',
        loaderHeight:16, 
        loaderWidth:17 
    });

    $("#form1").submit(function() {
        var tmp = $('#suggest1').val();
        window.location.href="gtlist?GlobalTag="+$('#suggest1').val()+"&GlobalTag2="+$('#suggest2').val()+"&filter="+$('#example_filter input').val();
        return false;
    });

    $('#RefrButt').click(function() {
        refresh_backend();
    });
 
    $('#GTCompare').click(function() {
       compareGT();
    }); 
});

//GET URL PARAMETER VALUE
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


function loadData(globalTag, globalTag2) {
    var check = false;
    if (globalTag != "" && globalTag2 != "") {
        GlobalTag = globalTag;
        GlobalTag2 = globalTag2;
        check = true;
    } else {
        if (globalTag != "") {
            GlobalTag = globalTag;
            GlobalTag2 = globalTag;
            check = true;
        }
        if (globalTag2 != "") {
            GlobalTag = globalTag2;
            GlobalTag2 = globalTag2;
            check = true;
        }
    }  
    if (check == false) {
        $.ajax({
            type: 'POST',
            url: 'getProductionGTs',
            data: {},
            async: false,
            dataType: 'json',
            success: function (data) {     
                                       if (data["prompt"] == "") { 
                                           GlobalTag = "GR_P_V14";
                                           GlobalTag2 = "GR_P_V14";
                                       }
                                       else { 
                                           GlobalTag = data["prompt"];
                                           GlobalTag2 = data["prompt"];
                                           
                                       }                        
                                      },
            error: function() { 
                                GlobalTag = "GR_P_V14";
                                GlobalTag2 = "GR_P_V14";
                                alert("Error in data send while getting production GT's");                
                              }
        }); 
    } 
    check = false;
    $.ajax({
        type: 'POST',
        url: 'getGTList',
        data: {},
        async: false,
        dataType: 'json',
        success: function (data) {
                                  globalTagList = data;
                                  $.unblockUI();
  
                                 },
        error: function() { alert("Error in data send while getting GT List"); }
    });
}


function getCMSVersions() {
    $.ajax({
        type: 'POST',
        url: 'getCMSSWVersion',
        dataType: "json",
        async: false,
        success: function (data) { CMSVersion = data; 
                                   if (CMSVersion["CMSSW_Version"] == "") {
                                       cmsReleaseTag.append("<option value='Server down'>Server down</option>");
                                   } else {
                                       cmsReleaseTag.append("<option value=" + CMSVersion["CMSSW_Version"] + ">" + CMSVersion["CMSSW_Version"] + "</option>");
                                   } 
                                 },
        error: function() { CMSVersion = ""; alert("Error in data send while getting CMS Version"); }
    });
}

function setTable() {
    var containerTag = $('#container');
    $.ajax({
        type: 'POST',
        url: 'getGTInfo',
        data: {GT_name : GlobalTag},
        dataType: "json",
        async: false,
        success: function (data) { 
                                     var currentTime = new Date();
                                     var month = currentTime.getMonth() + 1;
                                     var day = currentTime.getDate();
                                     var year = currentTime.getFullYear();
                                     var hours = currentTime.getHours();
                                     var minutes = currentTime.getMinutes();
                                     var seconds = currentTime.getSeconds();
                                     var monthStr = "";
                                     if (minutes < 10){
                                         minutes = "0" + minutes
                                     }
                                     switch (month) {
                                         case 1:
                                             monthStr = "January";
                                             break;
                                         case 2:
                                             monthStr = "February";
                                             break;
                                         case 3:
                                             monthStr = "March";
                                             break;
                                         case 4:
                                             monthStr = "April";
                                             break;
                                         case 5:
                                             monthStr = "May";
                                             break;
                                         case 6:
                                             monthStr = "June";
                                             break;
                                         case 7:
                                             monthStr = "July";
                                             break;
                                         case 8:
                                             monthStr = "August";
                                             break;
                                         case 9:
                                             monthStr = "September";
                                             break;
                                         case 10:
                                             monthStr = "October";
                                             break;
                                         case 11:
                                             monthStr = "November";
                                             break;
                                         case 12:
                                             monthStr = "December";
                                             break;
                                         default:
                                             monthStr = "";
                                             break;
                                     }
                                     var html_data = "";
                                     html_data = "<div id='creation_time' style='visibility:hidden;'><b>"+ day + " " + monthStr + ", " + year + " " + hours + ":" + minutes + ":" + seconds + "</b></div><table class='display' id='example'><thead><tr><th>ID</th><th>record</th><th>label</th><th>pfn</th><th>tag</th><th>lastSince</th><th>time</th><th>comment</th><th>iovlist</th><th>size</th><th>lastLogEntry</th></thead><tbody>";
                                     var index = 0;
                                     for (i=0; i <  data.body.length; i++) {
                                         index += 1;
                                         html_data += "<tr class='" + index + "'>";
                                         html_data += "<td>" + index + "</td>";
                                         html_data += "<td class='RCd'>" + data.body[i].record + "</td>";
                                         html_data += "<td></td>";
                                         html_data += "<td>" + data.body[i].pfn + "</td>";
                                         html_data += "<td>" + data.body[i].tag + "</td>";
                                         html_data += "<td>" + data.body[i].last_since + "</td>";
                                         html_data += "<td>" + data.body[i].time + "</td>";
                                         html_data += "<td>" + data.body[i].comment + "</td>";
                                         var temp = ""
                                         for (j=0; j < data.body[i].iov_list.length; j++) { 
                                             temp += "<tr>";
                                             for (k=0; k < data.body[i].iov_list[j].length; k++) {
                                                 temp += "<td>" + data.body[i].iov_list[j][k] +"</td>";
                                             }
                                             temp += "</tr>";
                                         }
                                         html_data += "<td></td>";
                                         iovList_array[data.body[i].record]=temp;
                                         temp = "";
                                         html_data += "<td>" + data.body[i].size + "</td>";
                                         html_data += "<td>" + data.body[i].last_log_entry + "</td>";
                                         html_data += "</tr>";
                                     }
                                     html_data += "</tbody></table>"
                                     tableContainer.append(html_data);},
        error: function() { alert("Error in data send while getting info about GT"); }
    });
}


function refreshPage() {
        ;
}

function blinkOn() {
    $("#RefrButt").css('color', 'black');
    setTimeout('blinkOff()', 300);
}


function blinkOff() {
    $("#RefrButt").css('color', 'white');
    setTimeout('blinkOn()', 300);
}

function reloadPage(creationDateString, limitInMinutes, waitPeriodInMinutes) {
    var creationDate = new Date(creationDateString);
    var currentDate = new Date();
    var dateDiffInMinutes = Math.round((currentDate - creationDate) / 1000 / 60 );
    if (dateDiffInMinutes > limitInMinutes) {
    }
    var wait = waitPeriodInMinutes * 1000 * 60;
    var callString = 'reloadPage("' + creationDateString + '", ' + limitInMinutes + ', ' + waitPeriodInMinutes + ')';
    setTimeout(callString, wait);
}

function reloadData(creationDateString, limitInMinutes) {
    var creationDate = new Date(creationDateString);
    var currentDate = new Date();
    var dateDiffInMinutes = Math.round((currentDate - creationDate) / 1000 / 60 );
    if ($("#creation_time").html() && (dateDiffInMinutes > limitInMinutes) && (globalTagList[0]!='ServerDown')) {
       $('#alert_link').attr('href', ('/gtlist/message-box.html?msg_name=Refreshing&refreshDate='+$("#creation_time").html()));
       $('#alert_link').click();       
    }
}

function updateCurrentTime() {
    monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    function pad(n) { 
        return n < 10 ? '0' + n : n;
    }
    var currentTimeObject = new Date();
    var currentTime = pad(currentTimeObject.getDate()) + ' ' + monthNames[currentTimeObject.getMonth()] +  ', ' + currentTimeObject.getFullYear() + ' ' + pad(currentTimeObject.getHours()) + ':' + pad(currentTimeObject.getMinutes()) + ':' + pad(currentTimeObject.getSeconds());
    _currentTime.html(currentTime);
    setTimeout('updateCurrentTime()', 5000);
}

function fix_fancybox_frame_size(){
    var fr_w = $('#fancybox-frame').contents().find('#alert').width();
    $("iframe#fancybox-frame").css('width', fr_w*1.19)
    $('div#fancybox-outer').css('width',fr_w*1.25)
    var fr_h = $('#fancybox-frame').contents().find('#alert').height();
    $("iframe#fancybox-frame").css('height',fr_h*1.11)  
    $('div#fancybox-outer').css('height',fr_h*1.17)
}


//var _gaq = _gaq || [];
//  _gaq.push(['_setAccount', 'UA-1950165-27']);
//  _gaq.push(['_setDomainName', '.cern.ch']);
//  _gaq.push(['_trackPageview']);
//
//  (function() {
//    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
//    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
//    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
//  })();

$(function(){
    $("#blocker").hide();
});

function compareGT(){
    var GT1 =  $('#suggest1').val();
    var GT2 =  $('#suggest2').val();
    $('#GTdiff').attr('href', ('gtlist/GTdiff.html?GlobalTag='+GT1+'&GlobalTag2='+GT2));
    $('#GTdiff').attr("title", ("difference between "+GT1+" and "+GT2));
    $('#GTdiff').click();       
}

function blockWindow() {
    $('.BoxTitle').html(msg);
    $.blockUI({ message: $('#processing') });
}

function refresh_backend(){
    msg    = "Refresh Global Tag<br><h2>"+$('#suggest1').val()+"</h2>"     
    location.href="gtlist?GlobalTag="+$('#suggest1').val()+"&GlobalTag2="+$('#suggest2').val()+"&filter="+$('#example_filter input').val();
}




