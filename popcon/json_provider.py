import random
import time
import re
import datetime
import json
from sets import Set

from popconSQL import popconSQL

#data_dict = {'CMS_COND_21X_RPC': {'2009:01:31': 5, '2009:01:30': 5, '2009:01:28': 5, '2009:01:29': 5, '2009:01:26': 5, '2009:01:27': 5, '2009:01:20': 5, '2009:01:21': 5, '2009:01:22': 5, '2009:01:23': 5, '2009:02:03': 5, '2009:02:02': 5, '2009:02:01': 5}, 'CMS_COND_21X_ALIGNMENT': {'2009:01:30': 1, '2009:01:28': 2, '2009:01:29': 2}, 'CMS_COND_21X_HCAL': {'2009:01:13': 13, '2009:01:12': 3, '2009:02:03': 35}, 'CMS_COND_21X_PIXEL': {'2009:01:15': 1}, 'CMS_COND_21X_ECAL': {'2009:01:28': 2, '2009:01:30': 5, '2009:02:03': 1, '2009:01:29': 2, '2009:02:02': 1}, 'CMS_COND_21X_DT': {'2009:01:30': 9, '2009:01:28': 13, '2009:01:29': 19, '2009:01:26': 1, '2009:01:27': 3, '2009:01:20': 86, '2009:01:22': 3, '2009:01:23': 12, '2009:02:02': 2}} 

class JsonProvider:

    COLOR = ('FF0000','458B00','8B2323','000000','8B008B','00FA9A','FFA500','458B74','CD661D','7FFF00','8B7355','FDB65A','00688B','DC143C','8A2BE2')

    def rand_color(self, index):
    	return '#' + ''.join(self.COLOR[index])

    def IOVTAGs_json_format(self, data_dict=[('runsummary_test',), ('TrackerCRAFTScenario22X_v2_mc',)]):
        IOVTAGs_json = []
        for iovtag in data_dict:
            IOVTAGs_json.append(iovtag[0])
        return IOVTAGs_json

    def json_dict_output_barstack(self, data_dict={'CMS_COND_21X_Antonio': {'2009:01:31': 5, '2009:01:30': 5},'CMS_COND_21X_RPC': {'2009:01:31': 5, '2009:01:30': 5}},title="Activity History recorded"):
       x_labels = []
       x_labels_mod	=   []
       account_list = []
       for account in data_dict.iterkeys():
            print data_dict[account]
            account_list.append(account)
            topics = data_dict[account].keys()
            topics.sort()
            for topic in topics:
                x_labels.append(topic)
                
		x_labels    =   list(Set(x_labels))
		x_labels.sort()

		converted_dates = [time.strftime("%a %d, %b", time.strptime(datestr[:10], "%Y:%m:%d")) for datestr in x_labels]
                converted_dates =   str(converted_dates).replace('\'','"')
		
		data_dict_json = """
                   "bg_colour":"#EBEAEA",
                   
                   "title":{
                            "text":"PopCon Activity History",
                            "style":"font-size:18px; font-family:Verdana; text-allign:center; height:500px;"
                    },
                """
       max_occ = 0;
       for time_date in x_labels:
            val = 0
            for account in account_list:
                tmp = 0
                try:
                        data_dict[account][time_date]
                        tmp = data_dict[account][time_date]
                except KeyError:
                        tmp = 0
                val += tmp
                if val > max_occ:
                        max_occ = val
                   
       one_step = round(max_occ/10.0,0)
       max_occ += one_step 
       
       data_dict_json += "\"x_axis\":{\"labels\":{\"rotate\":-45, \"labels\":"+converted_dates+"}},"

       data_dict_json += "\"y_axis\":{\"steps\":"+str(one_step)+", \"min\":0, \"max\":"+str(max_occ)+"},"
       #data_dict_json += "\"y_axis\":{\"steps\":"+str(round(max_occ/10.0,0))+", \"min\":0, \"max\":"+str(max_occ)+"},"
       
       #data_dict_json += """
       data_dict_json += "\"elements\":[{\"type\":\"bar_stack\", \"tip\":\"#total#\"," 
       data_dict_json += "\"values\":["
       
       index_color   =   0
       LEN_COLOR   =   len(self.COLOR)-1
       accout2color         =   {}
       accout2color_json    =   [] 
       for account in account_list:
            if index_color <  LEN_COLOR:
                    index_color +=  1
            else:
                    index_color   =   0
            accout2color[account]=self.rand_color(index_color)
            accout2color_json.append({"text":account,"colour":self.rand_color(index_color),"font-size": 13})
       
       for time_date in x_labels:
            data_dict_json += "["
            for account in account_list:
                    value = 0
                    try:
                            data_dict[account][time_date]
                            value = data_dict[account][time_date]
                            #data_dict_json += "\n{\"val\":"+str(value)+",\"colour\":\""+str(self.rand_color(index_color))+"\",\"tip\":\""+str(account)+": #val#<br>Total: #total#\"},"
                            data_dict_json += "\n{\"val\":"+str(value)+",\"colour\":\""+accout2color[account]+"\",\"tip\":\""+str(account)+": #val#<br>Total: #total#\"},"
                            
                    except KeyError:
                            value = 0
                    
            
            data_dict_json += "],"		       
       data_dict_json += "],"
       #data_dict_json += """"keys": [ { "colour": "#C4D318", "text": "Antonio2", "font-size": 13 }]"""
       data_dict_json += """"keys": """+str(accout2color_json).replace("'","\"")+""" """
       data_dict_json += "},"
       data_dict_json += "]"
       data_dict_json   =   str(data_dict_json).replace('},]','}]')
       data_dict_json   =   str(data_dict_json).replace('],]',']]')
       
       return "{"+data_dict_json+"}"

    def json_dict_output_barstack2(self, data_dict={'CMS_COND_21X_Antonio': {'2009:01:31': 5, '2009:01:30': 5},'CMS_COND_21X_RPC': {'2009:01:31': 5, '2009:01:30': 5}},title="Activity History recorded"):
       resultJSON = ""
       dateLabels = []
       tickNames = []
       tickCount = 30

       for account in data_dict.iterkeys():
            topics = data_dict[account].keys()
            for topic in topics:
                dateLabels.append(topic)
       dateLabels    =   list(Set(dateLabels))
       dateLabels.sort()

       index = 0
       totalValues = []
       if len(dateLabels) > tickCount:
           index = len(dateLabels) - tickCount
       while index < len(dateLabels):
           tickNames.append(dateLabels[index]) 
           index+=1 
           totalValues.append(0)

       resultJSON += """
           tickNames : [ 
       """
       counter = 0
       someHTML = "class='tickToFormat'"
       for i in tickNames:
           if counter > 0:
               resultJSON += ", "
           resultJSON += "[" + str(counter) + ',"<span ' + someHTML + '>' + time.strftime("%a %d, %b", time.strptime(i[:10], "%Y:%m:%d")) + '</span>"]'
           counter += 1
       resultJSON += " ], "

       plotData = "plotData : ["
       counter = 0
       for account in data_dict.iterkeys():
            if counter > 0:
                plotData += ', '        
            plotData += '{ label : "' + account + '&nbsp;&nbsp;&nbsp;&nbsp;",'
            plotData += 'data : ['
            dates = data_dict[account].keys()
            counter2 = 0
            for date in tickNames:
                if counter2 > 0:
                    plotData += ', '
                if date in dates:
                    totalValues[counter2] += data_dict[account][date]
                    plotData += '[' + str(counter2) + ',' + str(data_dict[account][date])  + ']'
                else:
                    plotData += '[' + str(counter2) + ', 0]'
                counter2 += 1 
            plotData += "]}"
            counter += 1
       plotData += ']'

       resultJSON += "totalValues : ["
       counter = 0
       for totalValue in totalValues:
           if counter >0:
               resultJSON += ", "
           resultJSON += str(totalValue)
           counter += 1
       resultJSON += '], '

       resultJSON += plotData

       return "{"+resultJSON+"}"
	
    
    def Elements_pie(self, 
                    data_dict= {'USED': {'2011:03:01': 4089980, '2009:11:18': 3813560, '2009:11:19': 3980952, '2009:11:15': 3757680, '2009:11:16': 3758472, '2009:11:17': 3792284}, 'QUOTA': {'2011:03:01': 5120000, '2009:11:18': 5120000, '2009:11:19': 5120000, '2009:11:15': 5120000, '2009:11:16': 5120000, '2009:11:17': 5120000}},
                    title   =   "Set your title"): 
        quota_info = {}
        try:
            quota_info["Used"] = data_dict['USED'][time.strftime('%Y:%m:%d')]
            quota_info["Remaining"] = data_dict['QUOTA'][time.strftime('%Y:%m:%d')]  -   quota_info['Used']
            current_data = time.strftime('%Y:%m:%d')
        except:
            quota_info["Used"] = data_dict['USED'][time.strftime('%Y:%m:%d', time.localtime(time.time()-86400))]
            quota_info["Remaining"] = data_dict['QUOTA'][time.strftime('%Y:%m:%d',time.localtime(time.time()-86400))]  -   quota_info['Used']
            current_data = time.strftime('%Y:%m:%d',time.localtime(time.time()-86400))
        values = []
        for i in quota_info:
            dic = {}
            dic["label"] = i
            dic["value"] = quota_info[i]
            values.append(dic)

    #"""
    #   for Detailed Example Using json pie chart see: 
    #   1)http://ofc2dz.com/OFC2/examples/Pies.html
    #   2)http://ofc2dz.com/OFC2/examples/pie-many-slices.txt
    #"""
	example	= """
            {
              "elements": [
                {
                  "type": "pie",
                  "alpha": 0.6,
                  "start-angle": 35,
                  "animate": [
                    {
                      "type": "fade"
                    }
                  ],
                  "tip": "#val# of #total#<br>#percent# of 100%",
                  "colours": [
                    "#1C9E05",
                    "#FF368D"
                  ],
                  "values": 
                    """+str(values).replace('\'','"')+"""
                }
              ],
              "title": {
                "text": " """+title+""": """+current_data+"""  "
              },
              "x_axis": null
            }
        """
        return example
    
    def stacked_bar_chart(self, data_dict={'CMS_COND_21X_RPC': {'2009:01:31': 5, '2009:01:30': 5}}, title='set your title'):
        x_labels = []
	x_labels_mod = [] #mod1 using this to enter an empty dates to the labels
        account_list = []
        data_y = {}  #data_y[account_list]
        for account in data_dict.iterkeys():
            data_y[account] =   []
            account_list.append(account)
            topics = data_dict[account].keys()
            topics.sort()
            for topic in topics:
                x_labels.append(topic)
        x_labels    =   list(Set(x_labels))
        x_labels.sort()

	#mod1
        first_date = x_labels[0] #getting the first date
        last_date = x_labels[-1] #getting the last date
        time_first = time.strptime(first_date,"%Y:%m:%d") #extracting time from the format
        time_last = time.strptime(last_date,"%Y:%m:%d")
	date_start = datetime.date(time_first[0], time_first[1], time_first[2]) #the first date
	date_last = datetime.date(time_last[0], time_last[1], time_last[2])	#the last date
	date_diff = (date_last - date_start).days
	one_day = datetime.timedelta(days=1) #this is the one day to be used to increase the date
	
	counter = 0;
	while counter <= date_diff:
            new_date = date_start + datetime.timedelta(days=counter) 
            new_date_mod = new_date.strftime("%Y:%m:%d")
            x_labels_mod.append(new_date_mod)
            counter = counter + 1

	#end of mod1
        max_occurency = 0
        for account in account_list:
            #for time_data in x_labels:
	    for time_data in x_labels_mod:
                try:
                    data_dict[account][time_data]
		    data_y[account].append(data_dict[account][time_data])
                    if max_occurency < data_dict[account][time_data]:
                        max_occurency   =   data_dict[account][time_data]
                except KeyError:
                    data_y[account].append(0)
        
        steps = 10
        converted_dates = [time.strftime("%a %d, %b", time.strptime(datestr[:10], "%Y:%m:%d")) for datestr in x_labels_mod]
        
        #creating the correct json output
        data_dict_json = {"bg_colour" : "#FAFAFA", 
                          "title": {"text" : title, "style" : "{font-size: 20px;}"},
                          "y_legend" : {"text" : "Occurency", "style" : "{font-size: 12px; color: #736AFF;}"},
                          "y_axis" : {"max" : max_occurency, "steps" : round(max_occurency/steps,0)},
                          "x_axis" : {"steps" : steps, "labels" : {"rotate" : -45, "labels" : converted_dates}},
                          "elements" : []}
        
        index_color = 0
        LEN_COLOR = len(self.COLOR)-1
        delay = 1.0
        for account in data_y:
            #delay += 0.0
            lineColour = str(self.rand_color(index_color))
            line = {"type" : "line"}
            line['colour'] = lineColour
            line['bg_colour'] = "#E58A25"
            line['background-color'] = "#53B9AA"
            line['inner_background'] = "#E58A25"
            line['text'] = str(account)
            line['font-size'] = 13
            line['width'] = 2
#            line['dot-style'] = {}
#            line['dot-style']['type'] = 'solid-dot'
#            line['dot-style']['colour'] = lineColour
#            line['dot-style']['dot-size'] = 3
#            line['dot-style']['tip'] = "Account: #key#<br>Value: #val#<br>Date: #x_label#"
#            line['on-show'] = {"type" : "shrink-in", "cascade" : 3, "delay" : delay}
            line['values'] = data_y[account]
            data_dict_json["elements"].append(line)
            if index_color <  LEN_COLOR:
              index_color +=  1
            else:
              index_color   =   0
        return json.dumps(data_dict_json)
        
    def json_dict_output(self, data_dict={'CMS_COND_21X_RPC': {'2009:01:31': 5, '2009:01:30': 5}}, title='set your title'):
        x_labels = []
	x_labels_mod = [] #mod1 using this to enter an empty dates to the labels
        account_list = []
        data_y = {}  #data_y[account_list]
        for account in data_dict.iterkeys():
            data_y[account] =   []
            account_list.append(account)
            topics = data_dict[account].keys()
            topics.sort()
            for topic in topics:
                x_labels.append(topic)
        x_labels    =   list(Set(x_labels))
        x_labels.sort()

	#mod1
        first_date = x_labels[0] #getting the first date
        last_date = x_labels[-1] #getting the last date
        time_first = time.strptime(first_date,"%Y:%m:%d") #extracting time from the format
        time_last = time.strptime(last_date,"%Y:%m:%d")
	date_start = datetime.date(time_first[0], time_first[1], time_first[2]) #the first date
	date_last = datetime.date(time_last[0], time_last[1], time_last[2])	#the last date
	date_diff = (date_last - date_start).days
	one_day = datetime.timedelta(days=1) #this is the one day to be used to increase the date
	
	counter = 0;
	while counter <= date_diff:
            new_date = date_start + datetime.timedelta(days=counter) 
            new_date_mod = new_date.strftime("%Y:%m:%d")
            x_labels_mod.append(new_date_mod)
            counter = counter + 1

	#end of mod1
        max_occurency = 0
        for account in account_list:
            #for time_data in x_labels:
	    for time_data in x_labels_mod:
                try:
                    data_dict[account][time_data]
		    data_y[account].append(data_dict[account][time_data])
                    if max_occurency < data_dict[account][time_data]:
                        max_occurency   =   data_dict[account][time_data]
                except KeyError:
                    data_y[account].append(0)
        
        steps = 10
        converted_dates = [time.strftime("%a %d, %b", time.strptime(datestr[:10], "%Y:%m:%d")) for datestr in x_labels_mod]
        
        #creating the correct json output
        data_dict_json = {"bg_colour" : "#FAFAFA", 
                          "title": {"text" : title, "style" : "{font-size: 20px;}"},
                          "y_legend" : {"text" : "Occurency", "style" : "{font-size: 12px; color: #736AFF;}"},
                          "y_axis" : {"max" : max_occurency, "steps" : round(max_occurency/steps,0)},
                          "x_axis" : {"steps" : steps, "labels" : {"rotate" : -45, "labels" : converted_dates}},
                          "elements" : []}
        
        index_color = 0
        LEN_COLOR = len(self.COLOR)-1
        delay = 1.0
        for account in data_y:
            #delay += 0.0
            lineColour = str(self.rand_color(index_color))
            line = {"type" : "line"}
            line['colour'] = lineColour
            line['bg_colour'] = "#E58A25"
            line['background-color'] = "#53B9AA"
            line['inner_background'] = "#E58A25"
            line['text'] = str(account)
            line['font-size'] = 13
            line['width'] = 2
            line['dot-style'] = {}
            line['dot-style']['type'] = 'solid-dot'
            line['dot-style']['colour'] = lineColour
            line['dot-style']['dot-size'] = 3
            line['dot-style']['tip'] = "Account: #key#<br>Value: #val#<br>Date: #x_label#"
            line['on-show'] = {"type" : "shrink-in", "cascade" : 3, "delay" : delay}
            line['values'] = data_y[account]
            data_dict_json["elements"].append(line)
            if index_color <  LEN_COLOR:
              index_color +=  1
            else:
              index_color   =   0
        return json.dumps(data_dict_json)
        
    def queryRow2dict(self,
                      rows = [('2009:11:20', 4089980, 5120000), ('2009:11:15', 3757680, 5120000), ('2009:11:16', 3758472, 5120000), ('2009:11:17', 3792284, 5120000), ('2009:11:18', 3813560, 5120000), ('2009:11:19', 3980952, 5120000)]):
        d,d1,d2={},{},{}
        for line in rows:
            d1[line[0]]= line[1]
            d2[line[0]]= line[2]
        d = {'USED':d1, 'QUOTA':d2}
        return d

    def queryRow2pie(self,
                     rows = [('2009:11:20', 4089980, 5120000), ('2009:11:15', 3757680, 5120000), ('2009:11:16', 3758472, 5120000), ('2009:11:17', 3792284, 5120000), ('2009:11:18', 3813560, 5120000), ('2009:11:19', 3980952, 5120000)]):
        d,d1,d2={},{},{}
        for line in rows:
            d1[line[0]]= line[1]
            d2[line[0]]= line[2]
        d = {'USED':d1, 'QUOTA':d2}
        return d

if __name__ == "__main__":
    JsonProvider   =   JsonProvider()
    print JsonProvider.json_dict_output_barstack()
    #print   JsonProvider.queryRow2dict()
    #print   JsonProvider.json_dict_output(data_dict=JsonProvider.queryRow2dict())
    #print   JsonProvider.Elements_pie()
    #JsonProvider   =   JsonProvider.IOVTAGs_json_format()
    #print JsonProvider
