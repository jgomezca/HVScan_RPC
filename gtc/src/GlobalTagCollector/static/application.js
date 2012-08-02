$(function(){
    var AccountType = Backbone.Model.extend();
    var Account = Backbone.Model.extend();
    var Tag = Backbone.Model.extend();
    var Record = Backbone.Model.extend();
    var Queue = Backbone.Model.extend();

    var AccountTypes = Backbone.Collection.extend({
        url: '/gtc/json/account_types/',
        model: AccountType
    });

    var Accounts = Backbone.Collection.extend({
        model: Account
    });

    var Tags = Backbone.Collection.extend({
        model: Tag
    });

    var Records = Backbone.Collection.extend({
        model: Record
    });

    var Queues = Backbone.Collection.extend({
            model: Queue
        });


    var SelectionView = Backbone.View.extend({
        tagName: "option",

        initialize: function(){
            _.bindAll(this, 'render');
        },
        render: function(){
            $(this.el).attr('value', this.model.get('id')).html(this.model.get('name'));

            return this;
        }
    });


    var SelectionsView = Backbone.View.extend({
    	events: {
        	"change": "changeSelected"
    	},
        initialize: function(){
            _.bindAll(this, 'addOne', 'addAll');
            this.collection.bind('reset', this.addAll);
        },
        addOne: function(location){
            var selectionView = new SelectionView({ model: location });
            this.selectionViews.push(selectionView);
            $(this.el).append(selectionView.render().el);
        },
        addAll: function(){
        	_.each(this.selectionViews, function(selectionView) { selectionView.remove() });
	        this.selectionViews = [];
        	this.collection.each(this.addOne);
            $(this.el).trigger("liszt:updated");

        },
        changeSelected: function(){
        	this.setSelectedId($(this.el).val());
    	},
        populateFrom: function(url) {
            this.collection.url = url;
            this.collection.fetch();
            this.setDisabled(false);
        },
        setDisabled: function(disabled) {
            $(this.el).attr('disabled', disabled);
        }
    });


    var AccountTypesView = SelectionsView.extend({
    	setSelectedId: function(accountTypeId) {
        	this.accountsView.populateFrom("/gtc/json/accounts/?parent=" + accountTypeId);

            this.tagsView.collection.reset();
            $(this.tagsView.el).attr('disabled', true);

            this.recordsView.collection.reset();
            $(this.recordsView.el).attr('disabled', true);

            this.queuesView.collection.reset();
            $(this.queuesView.el).attr('disabled', true);
	    }
	});


	var AccountsView = SelectionsView.extend({
	    setSelectedId: function(accountId) {
            this.tagsView.populateFrom("/gtc/json/tags/?parent=" + accountId);

            this.recordsView.collection.reset();
            $(this.recordsView.el).attr('disabled', true);

            this.queuesView.collection.reset();
            $(this.queuesView.el).attr('disabled', true);
    	}
	});


    var TagsView = SelectionsView.extend({
        setSelectedId: function(tagId) {
            this.recordsView.populateFrom("/gtc/json/records/?parent=" + tagId);

            this.queuesView.collection.reset();
            $(this.queuesView.el).attr('disabled', true);

        }
    });

    var RecordsView = SelectionsView.extend({
        setSelectedId: function(recordId) {
            // Do nothing - for now
            this.queuesView.populateFrom("/gtc/json/queues/?parent=" + recordId);
        }
    });

    var QueuesView = SelectionsView.extend({
        initialize: function(){ //dummy rewrite
            QueuesView.__super__.initialize.apply(this)
            _.bindAll(this, 'update_component');
            this.collection.bind('reset', this.update_component);
        },
        setSelectedId: function(recordId) {
            // Do nothing - for now

        },
        update_component: function(){
           $(this.el).multiSelect('refresh');




            this.collection.each(function(my_model){
                var description = my_model.get('descr');
                var id = my_model.get('id');
                $('#ms-queue').find("li[ms-value=" + id +"]").attr('alt',description).tooltip({title:description});
//                $('#ms-queue').find("li[ms-elem-selected=" + id +"]").attr('alt',description).twipsy({title:'alt'});
            });



            return this;
        }
    });


    var accountTypes = new AccountTypes();
    var accountTypesView = new AccountTypesView({el: $("#accountType"), collection: accountTypes});
	var accountsView = new AccountsView({el: $("#account"), collection: new Accounts()});
    var tagsView = new TagsView({el: $("#tag"), collection: new Tags()});
    var recordsView = new RecordsView({el: $("#record"), collection: new Records()});
    var queuesView = new QueuesView({el: $("#queue"), collection: new Queues()});
    accountTypesView.accountsView = accountsView;
    accountTypesView.tagsView = tagsView;
    accountsView.tagsView = tagsView;
    accountTypesView.recordsView = recordsView;
    accountsView.recordsView = recordsView;
    tagsView.recordsView = recordsView;
    accountTypesView.queuesView = queuesView;
    accountsView.queuesView = queuesView;
    tagsView.queuesView = queuesView;
    recordsView.queuesView = queuesView;
    accountTypes.fetch();



    (function( $ ) {
	var oldClean = jQuery.cleanData;

	$.cleanData = function( elems ) {
		for ( var i = 0, elem;
		(elem = elems[i]) !== undefined; i++ ) {
			$(elem).triggerHandler("destroyed");
			//$.event.remove( elem, 'destroyed' );
		}
		oldClean(elems);
	};

    })(jQuery);


    jQuery(document).ajaxSend(function(event, xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        function sameOrigin(url) {
            // url could be relative or scheme relative or absolute
            var host = document.location.host; // host + port
            var protocol = document.location.protocol;
            var sr_origin = '//' + host;
            var origin = protocol + sr_origin;
            // Allow absolute or scheme relative URLs to same origin
            return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
                (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
                // or any other URL that isn't scheme relative or absolute i.e relative.
                !(/^(\/\/|http:|https:).*/.test(url));
        }
        function safeMethod(method) {
            return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }

        if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    });


    function newAlert(type, message) {
        $("#alert_container").html($("<div class='alert " + type + " fade in' data-alert><p><h4 class='alert-heading'>We got errors</h4> " + message + " </p></div>"));
    }

    function newErrorAlert(message) {
        newAlert('alert-error', message);
    }

    function newSuccessAlert(message) {
        $("#alert_container").html($("<div class='alert " + 'alert-info' + " fade in' data-alert><p><h4 class='alert-heading'>Success</h4> " + message + " </p></div>"));

    }

    function newInfoAlert(message) {

        $("#alert_container").html($("<div class='alert " + 'alert-info' + " fade in' data-alert><p><h4 class='alert-heading'>Info</h4> " + message + " </p></div>"));

        }

    function removeAlerts(){
        $(".alert").remove();
    }

    function errors_to_html(data){
        var error_list = $("<dl></dl>");
        for (var key in data) {
            if (data.hasOwnProperty(key)) {
                $("<dt></dt>").text(key).appendTo(error_list);
                for (i=0;i<=data[key].length;i++)
                {
                    $("<dd></dd>").text(data[key][i]).appendTo(error_list);
                }
            }
        }
        return error_list.html();
    }

    function errors_count(data){
        var current_errors_count = 0;
        for (var key in data) {
            if (data.hasOwnProperty(key)) {
                current_errors_count += 1;
            }
        }
        return current_errors_count;
    }

    function post_form_data(redirect_on_success){
        newInfoAlert('Subbmitting');
        $.ajax({
          type: 'POST',
          url: 'new-request',
          data: $("#record_submit_form").serialize(),
          success: function(data){
              removeAlerts();

              if (data['form'] == 'FAILED'){
                  var errors_html = errors_to_html(data['errors'][0]); //should be avoided ['0']
                  newErrorAlert(errors_html);
              }
              else{
                  newSuccessAlert('Submitting was successful');
                  if (redirect_on_success){
                      window.location.replace("list_view");
                  }
              }
            },
          error: function(jqXHR, textStatus, errorThrown){
              newErrorAlert(textStatus);
              return false;
          },
          dataType: 'json'
        });
    };

    $(document).ready(function() {
        $("#accountType").chosen({no_results_text: "No results matched"});
        $("#account").chosen({no_results_text: "No results matched"});
        $("#tag").chosen({no_results_text: "No results matched"});
        $("#record").chosen({no_results_text: "No results matched"});
        $('#queue').multiSelect({
              selectableHeader : '<h5>Selectable Items</h5>',
              selectedHeader : '<h5>Selected Items</h5>',
              afterSelect: function(value, text){
                  var description = queuesView.collection.get(value).get('descr');
                  $('#ms-queue').find("li[ms-value=" + value +"]").attr('alt', description).tooltip({title:description});
                  $('#ms-queue').find("li[ms-value=" + value +"]").bind("destroyed", function(){
                      $('#ms-queue').find("li[ms-value=" + value +"]").tooltip('hide');
                 })
                },
                afterDeselect: function(value, text){
                    var description = queuesView.collection.get(value).get('descr');
                    $('#ms-queue').find("li[ms-value=" + value +"]").tooltip('hide');
                }

            });
        $(".chzn-select").chosen(); $(".chzn-select-deselect").chosen({allow_single_deselect:true});
        $("#submit_and_view").bind('click', function(){ post_form_data(true); return false;});
        $("#submit_and_edit").bind('click', function(){ post_form_data(false); return false; });

    })

});





