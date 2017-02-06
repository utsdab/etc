view = {  //MAIN PAGE Container
          //label: "Time",
          columns: 2,
          children: [
          	{
          		children: [
          		{
          		label: "Bxdf Plugins",
          		value: function() {
	                    var bxdfs = rmStats.getArray("/RIS/RixPluginCache");
	                    bxdfs = rmStats.filter(bxdfs, function() {return (rmStats.getAttr('kind') == 'bxdf');});

	                    return rmStats.renderTable(
	                      {
	                        rows: bxdfs,
	                        headers: ["Name", "Num Begins", "Begin Time"],
	                        totalRow: ["Total Bxdf's", 
	                                    rmStats.sum(bxdfs, function() { return rmStats.getInt("NumBegins");}),
	                                    rmStats.format( {
	                                    	value:rmStats.sum(bxdfs, function() { 
	                                    		return rmStats.getFloat("BeginTime/elapsed");}),
	                                    	style: "seconds"
	                                    })
	                                  ],
	                        columns: [
	                          function() {return rmStats.getAttr('name');},
	                          function() {return rmStats.getInt('NumBegins');},
	                          function() {return rmStats.get("BeginTime");}
	                        ],
	                        
	                      }
	                    );
                  	}
          		},

          		{
          		label: "Pattern Plugins",
          		value: function() {
	                    var patterns = rmStats.getArray("/RIS/RixPluginCache");
	                    patterns = rmStats.filter(patterns, function() {return (rmStats.getAttr('kind') == 'pattern');});

	                    return rmStats.renderTable(
	                      {
	                        rows: patterns,
	                        headers: ["Name", "Num Computes", "Compute Time"],
	                        totalRow: ["Total Pattens", 
	                                    rmStats.sum(patterns, function() { return rmStats.getInt("NumComputes");}),
	                                    rmStats.format( {
	                                    	value:rmStats.sum(patterns, function() { 
	                                    		return rmStats.getFloat("ComputeTime/elapsed");}),
	                                    	style: "seconds"
	                                    })
	                                  ],
	                        columns: [
	                          function() {return rmStats.getAttr('name');},
	                          function() {return rmStats.getInt('NumCompute');},
	                          function() {return rmStats.get("ComputeTime");}
	                        ],
	                        
	                      }
	                    );
                  	}
          		}
          		]
          	},
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
 
          	}
          ]

       }