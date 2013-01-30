// ---------- Data type ----------

function Status (new_value, new_reference)
{
   var value = new_value;
   var reference = new_reference;

   this.getValue = function ()
   {
      return value;
   }

   this.setValue = function (newValue)
   {
      if (typeof newValue != 'undefined')
      {
         value = newValue;
      }
   }

   this.getRef = function ()
   {
      return reference;
   }
}

// ---------- Data ----------

function ValuesArray ()
{
      // --- ValuesArray privte methods ---
   
   var _sortByNumber = function (a, b)
   {
      return a.getValue() - b.getValue();
   }

   var _prepareArray = function (array_to_prepare)
   {
      var tempStr = "";
      for (var i = 0; i < array_to_prepare.length; i++)
      {
         tempStr = array_to_prepare[i].getValue();
         array_to_prepare[i].setValue(tempStr.slice(8, tempStr.length - 1));
      }
      return array_to_prepare;
   }

   var _fetchData = function ()
   {
      var tempArray = new Array();
      
      var id = $('li .chart span');
      
      for (var i = 0; i < id.length; i++)
      {
         tempArray[i] = new Status($('li .chart span:eq(' + i + ')').html(), i);
      }
      
      return tempArray;
   }

      // --- End of privte methods ---

   var data = _fetchData();
   
      // --- ValuesArray public methods ---
   
   this.sortArray = function ()
   {
      _prepareArray(data).sort(_sortByNumber);
   }

   this.refreshList = function ()
   {
      for (var i = 0; i < data.length; i++)
      {
         $('li:eq(' + i + ')').attr('id',i);
      }
      var tempI = 0;
      var notFound = true;
      for (var i = 0; i < data.length; i++)
      {
         tempI = 0;
         notFound = true;
         while (notFound)
         {
            if ($('li:eq(' + tempI + ')').attr('id') == data[i].getRef())
            {
               notFound = false;
            }
            else
            {
               tempI++;
            }
         }
         $('ul').append($('li:eq(' + tempI + ')'));
      }
      $('li:eq(0)').attr('tabindex','0');
      for (var i = 1; i < data.length; i++)
      {
         $('li:eq(' + i + ')').attr('tabindex','-1');
      }
   }
   
      // --- End of public methods ---
}

