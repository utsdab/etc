view = {  //MAIN PAGE Container
          //label: "Textures",
          children: [
          	{
          		label: "Texture List",
          		value: function() {
          			var rows = rmStats.getArray("/texture/textureFiles");
          			var bytesTotal = rmStats.getInt("/texture/textureTileCache/bytesRead");

					return rmStats.renderTable(
                    	{
	                        rows: rows,
	                        headers: ["Filename", "Lookups", "Reads", 
	                                  "Bytes Read", "% Total"],
	                        columns: [
	                          function() {return rmStats.toString('fileName');},
	                          function() {return rmStats.getInt('lookups');},
	                          function() {return rmStats.getInt('reads');},
	                          function() {return rmStats.format(
	                            {
	                              value:rmStats.getInt('bytesRead'),
	                              style:'bytes'
	                            });
	                          },
	                          function() {return rmStats.format(
	                            {
	                              value:rmStats.getInt('bytesRead')/bytesTotal,
	                              style:'percent'
	                            });
	                          },
	                        ],
	                        totalRow: ["Total",
	                        	rmStats.sum(rows, function() {return rmStats.getInt('lookups');}),
	                        	rmStats.sum(rows, function() {return rmStats.getInt('reads');}),
	                        	rmStats.format({
	                        		value: rmStats.sum(rows, function () { return rmStats.getInt('bytesRead');}),
	                        		style: "bytes"
	                        	})
	                        ]
	                        
	                    }
                    );

          		}
          	},
          	{
          		label: "Texture Filtering Widths",
          		value: function() {
	        		return rmStats.renderChart(
		                      {
		                        type: "histogram",
		                        data: {
		                          rows: rmStats.getArray("/texture/textureFiltering/filterWidthHist"),
		                          label: function() { return rmStats.getAttr("label");},
		                          value: function() { return rmStats.getInt('.');}
		                        }
		                      }
		                    );
	        	}

          	},
          	{
          		label: "Texture Cache",
          	}
          ]

          
       }