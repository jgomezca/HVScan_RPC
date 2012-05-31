function TopScrollBar() {
   var _relateScrollBars, div, div1, a;
   _relateScrollBars = function() {
      $(function(){
         $(".dataTables_scrollBody_wrapper").scroll(function(){
            $(".dataTables_scrollBody")
               .scrollLeft($(".dataTables_scrollBody_wrapper").scrollLeft());
         });
         $(".dataTables_scrollBody").scroll(function(){
            $(".dataTables_scrollBody_wrapper")
               .scrollLeft($(".dataTables_scrollBody").scrollLeft());
         });
      });
   };
   div1 = document.createElement("div");
   temp_width = $('.dataTables_scrollBody tr:eq(1)').width();
   div1.setAttribute('style', 'width:' + temp_width.toString() + 'px; height: 20px;');   //1435px
   div = document.createElement("div");
   div.setAttribute('class', 'dataTables_scrollBody_wrapper');
   div.setAttribute('style', 'width: 100%; height: 20px; border: none 0px RED; overflow-x: scroll; overflow-y:hidden;');
   div.appendChild(div1);
   $('.dataTables_scrollBody').attr('id','jmk_id');
   a = document.getElementById('jmk_id');
   a.parentNode.insertBefore(div,a);
   $('.dataTables_scrollBody').removeAttr('id');
   $('.DTFC_Cloned thead tr:eq(1)').attr('style','height: 16px;');
   _relateScrollBars();
}
