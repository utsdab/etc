view = {
//MAIN PAGE Container
  label: rmStats.getName("/RIS/plugins/integrator/stats"),
  children: [
    //two rows
    {
      //first row two columns, params and performance
      columns: 3,
      children: [
        {
          value: function() {
            return rmStats.toString("/RIS/plugins/integrator/stats/parameters");
          }
        },
        {
          value: function() {
            if(rmStats.getName("/RIS/plugins/integrator/stats") == "PxrVCM")
              return rmStats.toString("/RIS/plugins/integrator/stats/operation");
            else
              return "";
          }
        },
        {
          label:'Camera samples heatmap',
          value: function() {
            rows =
            [
              ["&nbsp;","&nbsp;"],
              ["Time",
              rmStats.format({value: rmStats.getFloat('/time/timers/totaltime'), 
                                style: "time",
                                textStyle: "bold"})],
              ["Average", rmStats.format({
                                value: (rmStats.getInt("/options/maxSamples") *
                                      (1.0 - rmStats.getValue("/RIS/rayHider/adaptSkipped"))),
                                style: "float",
                                textStyle: "bold"}) + " samples per pixel"],
              ["Max Samples", rmStats.getInt("/options/maxSamples")],
              ["Min Samples", rmStats.getInt("/options/minSamples")],
              ["Pixel Variance&nbsp;&nbsp;", rmStats.getFloat("/options/pixelVariance")],
            ];
            var table = rmStats.renderSimpleTable(rows, 0.9);

            r =
            [
              rmStats.renderHeatMap({data: rmStats.find("/RIS/rayHider/adaptMap"),
                                scale: 0, colorMethod: 0}),
              table
            ]

            return r;
          }
        },
      ]

    },
    //second row active pixels
    {
    label: "Active Pixels by Increment - Max Samples " + rmStats.getInt("/options/maxSamples"),
    value: function() {
        return rmStats.renderChart(
                  {
                    label: "",
                    type: "spline",
                    ymin: 0,
                    xmax: rmStats.getInt("/options/maxSamples"),
                    data: {
                      rows: rmStats.getArray("/RIS/rayHider/adaptActive"),
                      label: function() { return rmStats.getAttr("label");},
                      value: function() { return rmStats.getInt('.');}
                      
                    }
                  }
                );
        }
    },
    {
    label: "Path Depth Timers (seconds/depth - wallclock)",
    value: function() {
        var rayDepth = 0;
        var threads = rmStats.getFloat("/options/threads");
        return rmStats.renderChart(
                  {
                    label: "",
                    type: "histogram",
                    xAxisTitle: "Path Depth",
                    yAxisTitle: "Time (sec)",
                    data: {
                      rows: rmStats.getArray("/RIS/plugins/integrator/stats/pathDepthTimer"),
                      label: function() { return rmStats.getAttr("label");},
                      value: function() {
                          var vertexTime = rmStats.getFloat('.');
                          rayDepth += 1;
                          return vertexTime/threads;
                      }
                    }
                  }
                );
        }
    },
    {
    label: "Ray Count at Depth",
    value: function() {
        var rayDepth = 0;
        var threads = rmStats.getFloat("/options/threads");
        return rmStats.renderChart(
                  {
                    label: "",
                    type: "histogram",
                    xAxisTitle: "Path Depth",
                    yAxisTitle: "Ray count",
                    data: {
                      rows: rmStats.getArray("/RIS/plugins/integrator/stats/pathRayCounts"),
                      label: function() { return rmStats.getAttr("label");},
                      value: function() { return rmStats.getInt('.');}                              
                    }
                  }
                );
        }
    }
  ]
}
