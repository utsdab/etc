importantTimeStats = ["/time/timers/shadingTimer",
                      "/time/timers/rayTraceTime",
                      "/texture/textureTileCache/readTime",
                      ];
//importantTimeStats.concat(rmStats.findWorst('timer', 3));


view = {  //MAIN PAGE Container
          //label: "Overview",
          children: [  // a  list of the items under the above label
            { 
              label:'Time',   
              columns: 2,
              children:[
                {
                  value: function() {
                    var subsystems = rmStats.find("/time/timers/timer");
                    subsystems = rmStats.filter(subsystems, function() {
                      return rmStats.getName() != 'totaltime';
                    });
                    subsystems = rmStats.sort(subsystems);
                    subsystems = subsystems.slice(0, 5);

                    var totalRow = rmStats.find("/time/timers/totaltime");

                    return rmStats.renderTable({
                      style: "timer",
                      rows: subsystems,
                      totalRow: totalRow
                    });
                  }

                },
                {
                  value: function() {
                    var subsystems = rmStats.find("/time/timers/timer");
                    subsystems = rmStats.filter(subsystems, function() {
                      return rmStats.getName() != 'totaltime';
                    });
                    subsystems = rmStats.sort(subsystems);
                    subsystems = subsystems.slice(0, 5);
                    return rmStats.renderChart({
                      type:"pie",
                      data:{
                        rows: subsystems,
                        style: "timer",
                      }
                    });
                  }
                }
              ]
            },
            { 
              label:'Memory',
              columns: 2,
              children: [
                {
                  value: function() {
                    var subsystems = rmStats.getArray("/memory/subsystems");
                    subsystems = rmStats.sort(subsystems);
                    subsystems = subsystems.slice(0, 5);
                    var totalMem = rmStats.getInt("/memory/systemMem/peakResidentSize");
                    var subTotal = rmStats.getInt("/memory/subsystemMem/peak");
                    var sum = rmStats.sum(subsystems);

                    var totalRow = rmStats.find("/memory/systemMem/peakResidentSize");

                    var rows = subsystems.slice();
                    rows.push(["Other Subsystems", 
                      rmStats.format({value: (subTotal-sum), style:'bytes'}),
                      rmStats.format({value: (subTotal-sum)/totalMem, style:'percent'})
                    ]);
                    rows.push(["Misc", 
                      rmStats.format({value: (totalMem-subTotal), style:'bytes'}),
                      rmStats.format({value: (totalMem-subTotal)/totalMem, style:'percent'})
                    ]);
                    
                    return rmStats.renderTable({
                      style: "memory",
                      rows: rows,
                      totalRow: totalRow
                    });
                  }

                },
                {
                  value: function() {
                    var subsystems = rmStats.getArray("/memory/subsystems");
                    subsystems = rmStats.sort(subsystems);
                    subsystems = subsystems.slice(0, 5);
                    var totalMem = rmStats.getInt("/memory/systemMem/peakResidentSize");
                    var subTotal = rmStats.getInt("/memory/subsystemMem/peak");
                    var sum = rmStats.sum(subsystems);

                    var rows = subsystems.slice();
                    rows.push(["Other Subsystems", (subTotal - sum)]);
                    rows.push(["Misc", (totalMem-subTotal)]);
                    return rmStats.renderChart({
                      type:"pie",
                      data:{
                        rows: rows,
                        style: "memory",
                      }
                    });
                  }
                }
              ]
              
            },
            { 
              label:'Raytracing',
              columns: 2,
              children: [
                {
                  value: function() {
                    var raysByType = rmStats.getArray("/rayAccel/raysByType");
                    var sum = rmStats.sum(raysByType, function() {return rmStats.getInt('.');});
                    var pixels = ( rmStats.getFloat('/options/xRes') * 
                                          rmStats.getFloat('/options/yRes'));
                    var samples = pixels * rmStats.getFloat('/options/xSamples') *
                                          rmStats.getFloat('/options/ySamples');

                    return rmStats.renderTable(
                      {
                        rows: raysByType,
                        headers: ["Ray Type", "# Rays", "Per Pixel", 
                                  "Per Sample", "% Total"],
                        totalRow: ["Totals", 
                                    sum,
                                    rmStats.format({
                                      value: sum/pixels,
                                      style: 'float',  
                                    }),
                                    rmStats.format({
                                      value: sum/samples,
                                      style: 'float',  
                                    }), ""
                                  ],
                        columns: [
                          function() {return rmStats.getAttr('name');},
                          function() {return rmStats.getInt('.');},
                          function() {return rmStats.format(
                            {
                              value:rmStats.getFloat('.') /pixels,
                              style:'float'
                            });
                          },
                          function() {
                            return rmStats.format(
                            {
                              value: rmStats.getFloat('.') /samples,
                              style:'float'
                            });
                          },
                          function() {
                            return rmStats.format(
                              {
                                value:rmStats.getFloat('.') / sum,
                                style:'percent'
                              });
                          },
                            
                        ],
                        
                      }
                    );
                  }
                },
                {
                  value: function() {
                    return rmStats.renderChart(
                      {
                        label: "Rays by Type",
                        type: "pie",
                        data: {
                          rows: rmStats.getArray("/rayAccel/raysByType"),
                          label: function() { return rmStats.getAttr("name");},
                          value: function() { return rmStats.getInt('.');}
                        }
                      }
                    );
                  }
                }
              ]
            },  
            
          ]
        };
      
