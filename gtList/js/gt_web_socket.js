            var s = 0
            
            function sock_open(e) {
                //TODO show info about automatic update
                 $('#status_ws').html("CONNECTED ( " + s.readyState + " )");
                document.getElementById("status_ws").style.color = "green"
            }
            
            function sock_close(e){
                setTimeout("init_sock()", 1000)
                $('#status_ws').html("CLOSED ( " + s.readyState + " )");
                document.getElementById("status_ws").style.color = "red"
            }
            
            function sock_error(e){
                if (this.readyState == this.CLOSED){
                    setTimeout("init_sock()", 1000)
                }
                //document.getElementById("status").innerHTML = "ERROR ( " + s.readyState + " )";
                //document.getElementById("status").style.color = "orange"
            }            
            function sock_msg(e){
                if (e.data != "[]"){
                    fnupdate_wrapper(e.data);
                    $("#debug_upload").append(e.data);
                    //TODO print data
                    //document.getElementById("history").innerHTML += "<b>[ " + new Date() + " ] Got data:</b><br />" + e.data + "<br />";
                    
                }
                    
            }            
            function init_sock(){
                s = new WebSocket("ws://popcon2vm.cern.ch:9087/")
                s.onopen = sock_open
                s.onclose = sock_close
                s.onerror = sock_error
                s.onmessage = sock_msg
                
            }           
            window.onload = init_sock()
            
            function disconnect(){
                s.close()
            }
            function clr(){
                ;//document.getElementById("history").innerHTML = "";
            }           

function fnupdate_wrapper(map){
    //map =   map ||  {"HcalRespCorrs_v1.02_mc": [[[145910, 4294967295]], "12 May 2009 06:00", 1213331]};
    map =   map ||  {"DQM_StreamExpress__Commissioning10-Express-v3": [[[146228, 146236], [146237, 4294967295]], 139, "21 Sep 2010 17:36"]};
    $.each(map, function(key, value) { 
            _tag    =   key;
            _time   =   value[2];
            _size   =   value[1];
            iov_list._new_value =   value[0];
            _lastSince          =   iov_list.get_last_since();//get_last_since(value[0]); 
            //$(value).each(function(){  alert(this);        })
            });
    var row_filtered    =   $('table tr:contains('+_tag+')');
            row_filtered.each(
                function(){ 
                var index   =   oTable.fnGetPosition(this);
                var row     =   oTable.fnGetData(index); 
                iov_list._old_value =   row;
                row[6]      =   _lastSince;//last_since
                row[7]      =   _time;
                row[10]     =   _size;
                row[9]     =   "<script>iovList_array['"+_tag+"']=\""+iov_list.get_new_list()+"\"</script>";
                //oTable.live("click",row, function(oTable){alert($(this));$(this).fnUpdate(row,index)});
                oTable.fnUpdate(row,index);
                });
            row_filtered.blink({speed: 400,blinks:10});
            return row_filtered;
}

