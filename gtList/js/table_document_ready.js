var oTable;
iovList_array	=	new Array();

function fnFormatDetails ( nTr )
{
	var iIndex 	= 	oTable.fnGetPosition( nTr );
	var aData 	= 	oTable.fnSettings().aoData[iIndex]._aData;
	var comment	=	aData[8];
	var pfn		=	aData[4];
	var record	=	aData[2];
	var iovList	=	iovList_array[record];
	var lastLogEntry=	aData[11];
	

        sOut2="\
               <link rel='stylesheet' type='text/css' href='css/inner_table.css' />\
               <div id='container_small'>\
               <div id='menu'>\
               <dl id='blue'>\
               <dd>\
               &nbsp;\
               <div class='scrollTableIOV'><table>\
               <table><thead><tr><th>Since</th><th>Till</th></tr></thead><tbody>"+iovList+"</tbody></table>\
               </table></div>\
               </dd>\
               </dl>\
               </div>\
               <div id='content'>\
               <dl class='red'>\
               <dt>Comment</dt>\
               <dd>"+format_comment(comment)+"</dl>\
               <dl class='red'>\
               <dt>PFN</dt>\
               <dd>"+format_pfn(pfn)+"</dl>\
               <dl class='red'>\
               <dt>Last Log entry</dt>\
               <dd>"+format_comment(lastLogEntry)+"</dd>\
               </dl>\
               </div>\
               </div>\
               <script  type='text/javascript'>iov_table_fix_height();</script>\
                ";
        return sOut2;
}


$(document).ready(function() {
        if($(document).getUrlParam("filter")=='RunInfoRcd_Bari'){
            $('#alert_link').attr('href', ('message-box.html?msg_name=missingRecordName'));
            $("#alert_link").fancybox({'type'        : 'iframe','width':485,'height':290});
            $('#alert_link').click(); 
        }
        $("#example_filter input").live("keyup", function() {
            if(oTable.fnSettings().aiDisplay.length < 1){
                    rcd_name    =   $("#example_filter input").val();
                    $('#alert_link').attr('href', ('message-box.html?msg_name=missingRecordName'));
                    $('#alert_link').click();       
                    }
        });
	/*
	 * Insert a 'details' column to the table
	 */
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
		"aaSorting": [[ 7, "desc" ]],
		"iDisplayLength": 50,
                "bStateSave": true,
		"oLanguage": {
			"sSearch": "Search all columns:",
                        "sZeroRecords": "No records display"
		},

					"bJQueryUI": true,
					"sPaginationType": "full_numbers",

		"aoColumns": [
			/* 0 */   { "bSearchable":    false},
			/* 1 ID */    { "bSearchable":    true, "bVisible":    false}, 
			/* record */    null,
			/* label */   { "bSearchable":    true, "bVisible":    true},
			/* pfn */   { "bSearchable":    true, "bVisible":    false},
                        /* tag */   { "bSearchable":    true},
			/* lastSince */   {"sSortDataType": "dom-text", "sType": "numeric" },
			/* time*/  {"sSortDataType": "dom-text", "sType": "date" },
			/* comment */  { "bSearchable":    true, "bVisible":    false},
			/* iovlist */ { "bSearchable":    false, "bVisible":    false},
			/* time*/  null,
			/* lastLogEntry */ { "bSearchable":    true, "bVisible":    false}
		],
	});
	
	$.fn.dataTableExt.FixedHeader( oTable );
	/* Add event listener for opening and closing details
	 * Note that the indicator for showing which row is open is not controlled by DataTables,
	 * rather it is done here
	 */
	//$('td img', oTable.fnGetNodes() ).each( function () {
        $('#example tbody tr td img').live("click", function() {
		//$(this).click( function () {
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
			}
		//} );
	} );
            
        if ($(document).getUrlParam("filter") != null) {
                oTable.fnFilter($(document).getUrlParam("filter"));
			$("#example_filter input").val($(document).getUrlParam("filter"));
        }
} );

