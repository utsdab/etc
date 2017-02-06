view = {  //MAIN PAGE Container
          //label: "Raytracing",
          columns: 2,
          children: [
          	
	          	{
          			label: "Time Spent",
          			value: function() {
	                    return rmStats.renderTable(
	                      {
	                        rows: rmStats.find("/rayAccel/timer"),
	                        headers: ["Description", "Time", "% Total"],
	                        totalRow: ["Ray Tracing Time", 
	                                    rmStats.toString("/time/timers/rayTraceTime"),
	                                    ""
	                                  ],
	                        columns: [
	                          function() {return rmStats.getAttr('description');},
	                          function() {return rmStats.toString('.');},
	                          function() {return rmStats.format(
	                            {
	                              value: rmStats.getFloat('elapsed')/rmStats.getFloat('/time/timers/rayTraceTime'),
	                              style:'percent'
	                            });
	                          }	                            
	                        ],
	                        
	                      }
	                    );
                  	}
                },
                {  // column 2
                	children: [
	                	{
	                		value: function() {
			                    return rmStats.renderChart(
			                      {
			                        label: "Raytracing time breakdown",
			                        style: "pie",
			                        data: {
			                          rows: rmStats.find("/rayAccel/timer"),
			                          label: function() { return rmStats.getAttr("name");},
			                          value: function() { return rmStats.getFloat('elapsed');}
			                        }
			                      }
			                    );
			                }
			            },
			            {
				        	label: "Ray Depths",
				        	value: function() {
				        		return rmStats.renderChart(
					                      {
					                        label: "Ray Depths",
					                        type: "histogram",
					                        data: {
					                          rows: rmStats.getArray("/rayAccel/rayDepthHistogram"),
					                          label: function() { return rmStats.getAttr("label");},
					                          value: function() { return rmStats.getInt('.');}
					                        }
					                      }
					                    );
				        	}

				        }
				    ]
                }

	        

	        
	      ] //columns
}