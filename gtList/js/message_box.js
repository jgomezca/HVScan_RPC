var alertDivTag;

alerting();

$("#no").click(function(){
    parent.$.fancybox.close();
});

$('#missingRcd').click(function(){
    emailSubject = "String not found"; 
    messageText = "The String "+$('#example_filter input', window.parent.document).val()+" is missing for "+$('#suggest1',window.parent.document).val()+" for "+$('select#cmssw_release',window.parent.document).val(),
    sendEmail(messageText, emailSubject);
    parent.$.fancybox.close();
});

$("#refresh").click(function(){
    parent.refresh_backend();
    parent.$.fancybox.close();
});

$("#server_down").click(function(){
    emailSubject = "GT List Server down";
    messageText = "GT List Server down for "+$('select#cmssw_release',window.parent.document).val(),
    sendEmail(messageText, emailSubject);
    parent.$.fancybox.close();
});

function sendEmail(messageText, emailSubject){
    $.ajax({        
        type: "GET",
        url: "/sendMail",
        data: { messageText : messageText, emailSubject : emailSubject },
        cache: false,
        success: function(data){
                    alert(data);
                    $("#response").fadeIn("slow");
                    setTimeout('$("#response").fadeOut("slow")',9000);
                 },
        error: function(data) { alert(data); }
    });
}

function alerting() {
    alertDivTag = $('#alert');
    var req = new XMLHttpRequest();
    req.open('GET', document.location, false);
    req.send(null);
    var headers = req.getResponseHeader("Info").toLowerCase();
    if ( headers == "server not available") {
        alertDivTag.append(" <div class='header'>Server Not aviable</div><div id='stringUnmatch' class='textfield'>This error message may indicate that the server is temporarily down or unreachable.<br>Please retry to reconnect in few seconds.<br>If the problem persists, contact the db expert group clicking on 'Report a problem' button.</div><div style='font-size:14px;'><a class='button_grey' id='server_down' href = '#'>Report a problem</a><a class='button_grey' id='no' href = '#'>No</a></div>");
        $('.textfield').css('font-size','124%');
    } else {
        if (headers == "refreshing") {
            alertDivTag.append(" <div class='header'>Refreshing</div><div class='textfield'>The last time the data was refreshed was <script> document.write($('#creation_time',window.parent.document).html());</scr"+"ipt><br>Do you want to refresh the data?<br>It usually required about thirty seconds.</div><div style='font-size:14px;'><a class='button_grey' id='refresh' href = '#'>Yes</a><a class='button_grey' id='no' href = '#'>No</a></div>"); 
        } else {
            if (headers =="missingrecordname") {
                alertDivTag.append("<div class='header'>String not found</div><div class='textfield'>The string <b><script>document.write($('#example_filter input', window.parent.document).val());</scr" + "ipt></b> for the Global Tag <b><script>document.write($('#suggest1',window.parent.document).val());</scr" + "ipt></b> built using the release <b><script>document.write($('#cmssw_release',window.parent.document).val());</scr" + "ipt></b> does not match the contents of any columns.<br>Check if the string you typed was correct,and try to build the list for the GT using another release.<br>If you think you are experiencing a problem, please contact the DB experts  by clicking on button 'Report a problem'.</div><div style='font-size:14px;'><a class='button_grey' id='missingRcd' href = '#'>Report a problem</a><a class='button_grey' id='no' href = '#'>No</a></div>")
            }
        }
    }
}                
