{ 
        "bg_colour":"#FAFAFA",

        "title":{
            "text":" Activity History recorded ",
            "style":"{font-size: 20px;}"
        },

        "y_legend":{
            "text":     "Occurency",
            "style":    "{font-size: 12px; color:#736AFF;}"
        },


        "y_axis":{
        "max":   125,"steps": 13.0},

	"x_axis":{"steps": 10,"labels":      {"rotate":-45, "labels":["Thu 28, Jan", "Fri 29, Jan", "Sat 30, Jan", "Sun 31, Jan", "Mon 01, Feb", "Tue 02, Feb", "Wed 03, Feb", "Thu 04, Feb", "Fri 05, Feb"]}},

"elements":[

 {
   "type": "line",
   "colour": "#53B9AA",
    "bg_colour": "#E58A25",
    "background-color":"#53B9AA",
    "inner_background": "#E58A25",
    "text": "Antonio",
    "font-size": 19,
    "width": 2,
    "dot-style": {
    "type":"solid-dot", "colour":"#F57F22", "dot-size": 3,
         "tip":"Account: #key#<br>Value: #val#<br>Date: #x_label#" },
         "on-show": {"type": "shrink-in", "cascade":1, "delay":0.7},
          "values" : [
                 5,7,10,12,13, 10,9,8,7]
},

{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#FF0000",
"text": "CMS_COND_31X_ALIGNMENT",
"values" :[0, 0, 0, 0, 0, 4, 0, 0, 0]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#458B00",
"text": "CMS_COND_31X_RUN_INFO",
"values" :[0, 0, 0, 0, 0, 0, 125, 117, 0]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#8B2323",
"text": "CMS_COND_34X_GEOMETRY",
"values" :[0, 0, 0, 0, 7, 9, 0, 0, 0]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#000000",
"text": "CMS_COND_31X_RPC",
"values" :[0, 24, 24, 16, 24, 24, 24, 24, 24]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#8B008B",
"text": "CMS_COND_31X_L1T",
"values" :[65, 10, 0, 0, 0, 6, 65, 54, 0]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#00FA9A",
"text": "CMS_COND_31X_DT",
"values" :[3, 0, 0, 0, 0, 0, 0, 0, 0]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#FFA500",
"text": "CMS_COND_31X_ECAL",
"values" :[1, 2, 0, 0, 0, 0, 1, 0, 4]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#458B74",
"text": "CMS_COND_31X_STRIP",
"values" :[0, 0, 0, 0, 4, 0, 15, 15, 0]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#CD661D",
"text": "CMS_COND_31X_HCAL",
"values" :[8, 0, 0, 0, 0, 0, 0, 0, 0]
},
{
"type":      "line",
"tip": "#key#<br>Value: #val#, Date: #x_label#",
"colour":"#7FFF00",
"text": "CMS_COND_31X_PIXEL",
"values" :[0, 0, 0, 0, 0, 0, 3, 6, 0]
}
]};
