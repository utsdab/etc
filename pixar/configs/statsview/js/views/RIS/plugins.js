view = {  //MAIN PAGE Container
          //label: "Time",
          note: "Click on a table row for more info",
          children: [
          	//view is three rows, integrator, bxdf, pattern

            {
                label: "Bxdfs",
                value: function() {
                    return rmStats.pluginTableAndInfo(rmStats.getArray("/RIS/plugins/bxdfs"));
                }
            },

            {
                label: "Patterns",
                value: function() {
                    return rmStats.pluginTableAndInfo(rmStats.getArray("/RIS/plugins/patterns"));
                }
            }

            /*
          	{
          		label: "Active Pixels by Increment",
          		value: function() {
				        		return rmStats.renderChart(
					                      {
					                        label: "",
					                        style: "histogram",
					                        data: {
					                          rows: rmStats.getArray("/RIS/rayHider/adaptActive"),
					                          label: function() { return rmStats.getAttr("label");},
					                          value: function() { return rmStats.getInt('.');}
					                        }
					                      }
					                    );
				        	}
 
          	}*/
          ]

       }