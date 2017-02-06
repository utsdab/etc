var lightingTimers =  [
					{
						name: "Sample Evaluation",
						path: "/RIS/Lighting/lightingMaterialTime",
						children: [
							{
								name: "Shadows",
								path: "/RIS/Lighting/lightingMaterialShadowTime"
							},
							{
								name: "Tracing",
								path: "/RIS/Lighting/lightingMaterialTraceTime"
							},
							{
								name: "Other",
								path: "/RIS/Lighting/lightingMaterialTimeExcluding"
							}

						]
					},
					{
						name: "Sample Generation",
						path: "/RIS/Lighting/lightingLightSampleTime",
						children: [
							{
								name: "Shadowing",
								path: "/RIS/Lighting/lightingLightShadowTime"
							},
							{
								name: "Bxdf Evaluation",
								path: "/RIS/Lighting/lightingLightEvalTime"
							},
							{
								name: "Other",
								path: "/RIS/Lighting/lightingLightSampleTimeExcluding"
							}

						]
					},
					{
						name: "Photon Generation",
						path: "/RIS/Lighting/lightingPhotonSampleTime",
						children: [
							{
								name: "Tracing and hit Bxdf Evaluation",
								path: "/RIS/Lighting/lightingPhotonTraceBxdfTime"
							},
							{
								name: "Other",
								path: "/RIS/Lighting/lightingPhotonSampleTimeExcluding"
							}

						]
					}
				]


view = {
	columns:2,
	//two columns, table on left and charts (3) on right
	//memory?
	children: [
		{

			children: [
				{
					label: "Time Spent by Phase",
					pushd: "/RIS/Lighting",
					value: function() {
						
						var totaltime = rmStats.getValue("lightingTotalTime");
						return rmStats.renderTable({
														headers: ['Timer', 'Time Spent', "% Total"],
														columns: [
		                          function() {return rmStats.getAttr('description');},
		                          function() {return rmStats.toString(".");},
		                          function() {return rmStats.format(
		                            {
		                              value:rmStats.getFloat('elapsed') / totaltime,
		                              style:'percent'
		                            });}
		                        ],
		                                              rows: rmStats.buildNodesFromSchema(lightingTimers, 'timer', true),
		                                              totalRow: ["Total Lighting", rmStats.format(
		                                              					{value: totaltime,
		                                              					style: "seconds"}), "100.0%"]
		                                         });
					}
				},
				/*{
	                label: "Light Emission Computation",
	                note: "This is the time spent computing emit() from light shaders.",
	                value: function() {
		                var lights = rmStats.getArray("/shaders/light");
		                var totalPoints = rmStats.sum(lights, function() { return rmStats.getValue("pointsShaded");});
		                var totalTime = rmStats.sum(lights, function() { 
		                                                return rmStats.getValue("shaderTimer");});

		                return rmStats.renderTable(
		                  {
		                    rows: lights,
		                    headers: ["Name", "Points Shaded", "Compute Time"],
		                    totalRow: ["Total", 
		                                totalPoints,
		                                rmStats.format( {
		                                        value:totalTime,
		                                        style: "seconds"
		                                })
		                              ],
		                    columns: [
		                      function() {return rmStats.getAttr('name');},
		                      function() {return rmStats.format({
		                                    value: rmStats.getInt('pointsShaded')/totalPoints,
		                                    style: "percent"
		                                  });},
		                      function() {return rmStats.format({
		                                    value: rmStats.getInt('shaderTimer')/totalTime,
		                                    style: "percent"
		                                  });}
		                      ],
		                    
		                  }
		                );
	                }
        		},*/
        		/*{
					label: "Time per Sample",
					note: "This table shows the time per sample spent in various areas.  You can change the listed integrator setting in RIB if the integrator is spending too much time in one.",
					pushd: "/RIS/Lighting",
					value: function() {
						var rows = [];
						rows.push(["Photon Generation", 
								rmStats.format({style:'milliseconds', 
									value:rmStats.getValue("lightingPhotonSampleTime")/rmStats.getValue("mPhotonSamples")}),
								'no setting'
							]);
						rows.push(["Sample Generation", 
								rmStats.format({style:'milliseconds', 
									value:rmStats.getValue("lightingLightSampleTime")/rmStats.getValue("nLightSamples")}),
								"Light Samples = " + rmStats.getValue("/RIS/plugins/integrator/[0]/parameters/numLightSamples")
							]);
						rows.push(["Sample Evaluation", 
								rmStats.format({style:'milliseconds', 
									value:rmStats.getValue("lightingMaterialTime")/rmStats.getValue("nMaterialSamples")}),
								"Bxdf Samples = " + rmStats.getValue("/RIS/plugins/integrator/[0]/parameters/numBxdfSamples")
							]);
						var totaltime = rmStats.getValue("lightingTotalTime");
						return rmStats.renderTable({
														headers: ['Timer', 'Time per sample', "Integrator Setting"],
														rows: rows
													});
					}
				}*/

        	]
        },
		
		//second column, three rows of charts
		{
			width: 4,
			children: [
				{
					label: "Photon Generation",
					value: function() {
						return rmStats.renderChart({
			                type:"verticalBar",
			                data:{
			                  rows: rmStats.buildNodesFromSchema(lightingTimers[2].children, 'timer', true),
			                  label: function() {return rmStats.getName() + " - " + rmStats.format({
			                                                          value:rmStats.getValue('.'),
			                                                          style: 'seconds'});},
			                  value: function() {return rmStats.getValue('.');},
			                  //style: "timer",
			                }
			              });
					}
				},
				{
					label: "Sample Generation",
					value: function() {
						return rmStats.renderChart({
			                type:"verticalBar",
			                data:{
			                  rows: rmStats.buildNodesFromSchema(lightingTimers[1].children, 'timer', true),
			                  label: function() {return rmStats.getName() + " - " + rmStats.format({
			                                                          value:rmStats.getValue('.'),
			                                                          style: 'seconds'});},
			                  value: function() {return rmStats.getValue('.');},
			                  //style: "timer",
			                }
			              });
					}
				},
				{
					label: "Sample Evaluation",
					value: function() {
						return rmStats.renderChart({
			                type:"verticalBar",
			                data:{
			                  rows: rmStats.buildNodesFromSchema(lightingTimers[0].children, 'timer', true),
			                  label: function() {return rmStats.getName() + " - " + rmStats.format({
			                                                          value:rmStats.getValue('.'),
			                                                          style: 'seconds'});},
			                  value: function() {return rmStats.getValue('.');},
			                  //style: "timer",
			                }
			              });
					}
				}
			]
		}
	]

}