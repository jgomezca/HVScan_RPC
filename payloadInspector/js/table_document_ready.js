var oTable;
//iovList_array	=	new Array();
//$(document).ajaxStart(function (e)
//        {
//        $.blockUI({ message: $('#open_record')}); //setup with a loading msg.
//        });
//$(document).ajaxStop(function (e)
//        {       
//        $.unblockUI();
//        })


function getIovListBig(record){
    var output;
    var db  =   $("#DBservice").val();
    var acc =   $("#Account").val();

    $.ajax({
        url: "get_iovContent",
        data: {tagname : record, dbName : db, acc : acc},
        cache: true,
        async: true,
        success: function(data){
            setContenentInInnerTable(data,record);
}
});
}

function setContenentInInnerTable(iovContent,record){
    var chunkLength             =   38000;   
    var record = record.replace(".", "__");
    var iovContentLength    =   iovContent.length;
    var chunkNum                =   Math.floor(iovContentLength/chunkLength);
    if ($('#Account').val().indexOf('BEAMSPOT') != -1){
        //$('#headerInnerTable .sub_right').append("");
        $('#headerInnerTable .sub_right .trendPlot').css("visibility",'visible');
        $('#headerInnerTable .sub_right .plot').remove();
    }
    else 
        $('#headerInnerTable .sub_right .trendPlot').remove();
    var header_inner_table      =   $('#headerInnerTable').html();//+"<div class='tableContainer'><table class='myTable01'></table></div><script>bITS();</script>";
    var itemBigContainer        =   $('#bigIovContainer_'+record);
    itemBigContainer.html(header_inner_table);
    itemBigContainer.append("<div class='tableContainer'><table id='"+record+"' class='myTable01'></table></div>");
    //alert(chunkNum+"\n"+iovContent.slice(iovContent.length-100,iovContent.length));
    for(var i=0,x=0,y=chunkLength; i<chunkNum+1;i++){
        var iovContentChunk   =   iovContent.slice(x,y);
        y   =   iovContentChunk.lastIndexOf("#")+1;
        iovContentChunk    =   iovContent.slice(x,y);
        setTimeout(function(x,_i){
                return function(){
                x = decodeTbl(x);
                var idRcd   =   $("#"+record);
                if(_i==0){
                    x+="</tbody>";
                    idRcd.append(x);
                    bITS(record);
                }
                else
                    idRcd.append(x);
                }
                }(iovContentChunk,i)
                ,i*300);
        iovContent    =   iovContent.substr(y,iovContent.length);  
    }
    //$('#bigIovContainer').html(header_inner_table+_iovListContent);
    setJsInInnerTable(record);
    adjustInnerTable();
}

function decodeTbl(x){
    x = x.replace(/@/g,"<tr><td>");
    x = x.replace(/_/g,"</td><td>");
    x = x.replace(/#/g,"</td></tr>");
    return x;
}

function setJsInInnerTable(record){
    //var connection_string   =   "oracle://"+$('#DBservice').val()+"/"+$('#Account').val();
    var dbName = $('#DBservice').val();
    var accName = $('#Account').val();

    var urlPar  =   '?dbName='+dbName+'&acc='+accName+'&tag='+record.replace("__", ".") +'&since=';

    var url    =   'get_summaries.html'+urlPar;
    $('.summary').click(function(){
            selectCheckedSince($(this),'#summary_link', url);
            });

    var purl    =   'get_plot_list.html'+urlPar;
    $('.plot').click(function(){
            selectCheckedSince($(this),'#plot_link', purl);
            });

    var xurl    =   'get_xml'+urlPar;
    $('.cxml').click(function(){
            var new_url = selectCheckedSinceForXml($(this),'#xml_link', xurl);
            //window.open(new_url);
            window.location.href=new_url;
            alert("Operation in progres, please click ok and wait. You can continue working, after xml file will be generated, pop up window will apear!");
            });

    var tpurl       =   'get_trend_plot.html'+urlPar;
    $('.trendPlot').click(function(){ 
            var new_url = selectCheckedSince($(this),'#trendPlot_link', tpurl);
            });
}

/* Formating function for row details */
function fnFormatDetails_script ( nTr )
{
    var iIndex 	= 	oTable.fnGetPosition( nTr );
    var aData 	= 	oTable.fnSettings().aoData[iIndex]._aData;
    var comment	=	aData[1];
    var record	=	aData[2];
    var iovList;//	=	iovList_array[record];//aData[9];

    if(typeof iovList_array[record]  == "undefined"){
        getIovListBig(record);
    }
    else{
      
        iovList	=	iovList_array[record];//aData[9];
        setContenentInInnerTable(iovList,record);
    }
}

/* Formating function for row details */
function fnFormatDetails ( nTr )
{
    var iIndex 	= 	oTable.fnGetPosition( nTr );
    var aData 	= 	oTable.fnSettings().aoData[iIndex]._aData;
    var comment	=	aData[1];
    var pfn		=	aData[2];
    var record	=	aData[2].replace(".", "__");
    var iovSize     =       aData[4];
    var iovList	=	iovList_array[record];//aData[9];

    var sOut = '<table class="sort-table">';
    sOut += '<thead><tr>';
    sOut += '</tr></thead>';
    sOut += '<tbody><tr>';
    sOut += '<td id="bigIovContainer_'+record+'"></td>';
    sOut += '</tr></tbody>';
    sOut += '</table>';
    sOut += '<script>';

    var connection_string   =   "oracle://"+$('#DBservice').val()+"/"+$('#Account').val();
    var dbName = $('#DBservice').val();
    var accName = $('#Account').val();


    //get diff plot
    sOut += "var durl    =   '';"
        sOut += "durl        +=  'get_plot_cmp.html?';"
        sOut += "$('.diff').click("
        sOut += "  function(){"
        sOut += "  check_iov_for_diff($(this),'#diff_link', durl, '"+dbName+"', '"+accName+"', '"+record+"')"; 
    sOut += "  }"
        sOut += ");"


        //get histo
        sOut += "var hurl    =   '';"
        sOut += "hurl        +=  'get_histo.html?';"
        sOut += "hurl        +=  'dbName="+connection_string+"&';"
        sOut += "hurl        +=  'tag="+record+"&';"
        sOut += "hurl        +=  'since=1&';"
        sOut += "hurl        +=  'iframe=true&width=95%&height=97%';"
        sOut += "var hrf    =   $('#histo_link').attr('href',hurl);"
        sOut += "$('.histo').click(function(){$('#histo_link').click();});";
    //sOut += "$('.histo').click(function(){ window.location.href=hurl;});";
    sOut += '</script>';
    return sOut;
}


$(document).ready(function() {
        /*
         * Insert a 'details' column to the table
         */
    $('.myTable01 tbody tr').live({
        click: function() {
        ClassName   =   $(this).attr('class');
        if(ClassName && ClassName.indexOf('Selected')!=-1){
                $(this).removeClass("Selected");
                $(this).find("td").css('background-color', '');
        }
        else{
            $(this).addClass("Selected");
            $(this).find("td").css('background-color', '#0099CC');
            //alert($(this).find("td:first").html());
        }  }
    });

        var nCloneTh = document.createElement( 'th' );
        var nCloneTd = document.createElement( 'td' );
        nCloneTd.innerHTML = '<img src="lib/examples_support/details_open.png">';
        nCloneTd.className = "center";

        $('#example thead tr').each( function () {
            this.insertBefore( nCloneTh, this.childNodes[0] );
            } );

        $('#example tbody tr').each( function () {
            this.insertBefore(  nCloneTd.cloneNode( true ), this.childNodes[0] );
            });

        /*
         * Initialse DataTables, with no sorting on the 'details' column
         */
        oTable = $('#example').dataTable( {
            "aaSorting": [[ 1, "desc" ]],
            "iDisplayLength": 50,
            "oLanguage": {
            "sSearch": "Search all columns:"
            },

            "bJQueryUI": true,
            "sPaginationType": "full_numbers",

            "aoColumns": [
            /* 0 */   { "bSearchable":    true},
			/* 1 ID */    { "bSearchable":    true, "bVisible":    true}, 
			/* record */   { "bSearchable":    true, "bVisible":    true}, 
			/* label */   { "bSearchable":    true, "bVisible":    true, "sType": "date"},
			/* time*/  { "bSearchable":    true,"sType": 'numeric'}
		]
	});
	
	$.fn.dataTableExt.FixedHeader( oTable );
	/* Add event listener for opening and closing details
	 * Note that the indicator for showing which row is open is not controlled by DataTables,
	 * rather it is done here
	 */
	$('td img', oTable.fnGetNodes() ).each( function () {
		$(this).click( function () {
			var nTr = this.parentNode.parentNode;
			if ( this.src.match('details_close') )
			{
				/* This row is already open - close it */
				this.src = "lib/examples_support/details_open.png";
				oTable.fnClose( nTr );
			}
			else
			{
				/* Open this row */
				this.src = "lib/examples_support/details_close.png";
                                oTable.fnOpen( nTr, fnFormatDetails(nTr), 'details' );
                                fnFormatDetails_script(nTr);
			}
		} );
	} );
} );

