var dbName = ""; 
var acc = ""; 
var tag = ""; 
var since = ""; 

function getUrParams () {
    dbName = gup('dbName').replace("%20", " ");
    acc = gup('acc').replace("%20", " ");
    tag = gup('tag').replace("%20", " ");
    since = gup('since').replace("%20", " ");
    dbName = dbName.replace("%3B", ";");
    acc = acc.replace("%3B", ";");
    tag = tag.replace("%3B", ";");
    since = since.replace("%3B", ";"); 
}

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


