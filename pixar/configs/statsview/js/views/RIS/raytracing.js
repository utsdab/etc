//MAIN PAGE Container
view =
{
//label: "Raytracing",
columns: 2,
children: [
    // column 1
    {
        width: 8,
        pushd: "/rayAccel",
        children: [

        {
          label: "Time Spent by Raytype",
          value: function() {
              var timerRows = [rmStats.find('transmissionTime'), rmStats.find('directlightTime'),
                          rmStats.find('cameraTime'), rmStats.find('indirectTime')];

              return rmStats.renderTable(
                {
                  rows: timerRows,
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
        {
          label: "Other Raytrace Timers",
          value: function() {
              var tempRows = rmStats.find("/rayAccel/timer");
              var skipItems = ['transmissionTime', 'directlightTime', 'cameraTime', 'indirectTime'];
              var rows = rmStats.filter(rmStats.find("/rayAccel/timer"), function() {
                return skipItems.indexOf(rmStats.getName()) == -1;
              });


              return rmStats.renderTable(
                {
                  rows: rows,
                  headers: ["Description", "Time"],
                  columns: [
                    function() {return rmStats.getAttr('description');},
                    function() {return rmStats.toString('.');},
                  ],
                  
                }
              );
          }
        }]

    },
    // column 2
    {  
        width: 4,
        pushd: "/rayAccel",
        children: [
        // row 1
        {
            height:300,
            value: function() {
                var timerRows = [rmStats.find('transmissionTime'), rmStats.find('directlightTime'),
                        rmStats.find('cameraTime'), rmStats.find('indirectTime')];

                return rmStats.renderChart(
                  {
                    label: "Raytracing time breakdown",
                    type: "verticalBar",
                    data: {
                      rows: timerRows,
                      label: function() { return rmStats.getAttr("description");},
                      value: function() { return rmStats.getFloat('elapsed');}
                    }
                  }
                );
            }
        },
        // row 2
        /*{
            label: "Ray Depths",
            value: function() {
                return rmStats.renderChart(
                          {
                            type: "histogram",
                            xAxisTitle: "Depth",
                            yAxisTitle: "Number of Rays",
                            data: {
                              rows: rmStats.getArray("/rayAccel/rayDepthHistogram"),
                              label: function() { return rmStats.getAttr("label");},
                              value: function() { return rmStats.getInt('.');}
                            }
                          }
                        );
            }
        }*/
        ]
    }     
    ] //columns
}