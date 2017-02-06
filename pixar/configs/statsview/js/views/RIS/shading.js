
//MAIN PAGE Container
view =
{  
//label: "Time",
//columns: 2,
children: [

    // row 1
    {
        columns: 2,
        children: [
        // column 1
          {

            children:[
              {  
                label: "Summary",
                value: function()
                  {
                    //var sctx = rmStats.find("/RIS/sctx");
                    //console.log(sctx);
                    rows =
                    [
                      ["Time:", rmStats.toString("/RIS/sctx/sctxExecTime")],
                      ["Bxdf Memory:", rmStats.toString("/RIS/sctx/shadingMem")],
                      ["Pattern Memory:", rmStats.toString("/RIS/ictx/patternMem")],
                      ["Points:", rmStats.getInt("/RIS/sctx/numPts")],
                      ["Invocations:", rmStats.getInt("/RIS/sctx/stcxExecCount")],
                      ["Points/Shader Invoke:", rmStats.format({
                                  value: rmStats.getInt("/RIS/sctx/numPts")/rmStats.getInt("/RIS/sctx/stcxExecCount"),
                                  style: "float"})],
                    ];
                    return rmStats.renderSimpleTable(rows);
                  }
              },

              // column 2
              {
                label: "Opacity Cache",
                value: function()
                {
                    rows =
                    [
                      ["Hit rate:", rmStats.format({
                        style: "percent",
                        value: rmStats.sum(rmStats.find("/rayGprim/radioCacheHits/*")) / 
                              rmStats.sum(rmStats.find("/rayGprim/radioCacheLookups/*")) })],
                      ["Size:", rmStats.format({style: "bytes", value: rmStats.getValue("/rayGprim/radioCacheMem")}) + " / " + rmStats.format({style: "bytes", value: rmStats.getValue("/options/opacityCacheMemory")*1000})],
                      ["Pattern Memory:", rmStats.toString("/RIS/ictx/patternMem")],
                    ];
                    return rmStats.renderSimpleTable(rows);
                }
              },       
            ]  
          },
          {
            label: "Nodes by type",
            value: function() {
              var nodes = rmStats.getArray("/RIS/RISNodes");

              return rmStats.renderTable(
                {
                  rows: nodes,
                  headers: ["Class", "Number", "Creation Time", "Memory"],
                  totalRow: ["Total", 
                              rmStats.sum(nodes, function() {return rmStats.getInt("memory/count");}),
                              rmStats.format({
                                  value:rmStats.sum(nodes, function() { 
                                      return rmStats.getFloat("creationTime/elapsed");}),
                                  style: "seconds"
                              }),
                              rmStats.format({
                                  value: rmStats.sum(nodes, function() {return rmStats.getValue("memory");}),
                                  style: "bytes"
                              }),
                            ],
                  columns: [
                    function() {return rmStats.getAttr('name');},
                    function() {return rmStats.getInt('memory/count');},
                    function() {return rmStats.toString("creationTime");},
                    function() {return rmStats.toString("memory");}
                  ],
                  
                }
              );
            }
          }
        ]
    },
    
    // row 2
    {
        columns: 2,
        children: [
        // column 1
        {
            children:[
            // row 1
            {
                label: "Bxdfs",
                note: "The begin time includes time to gather connected patterns, NOT computing samples.",
                value: function() {
                var bxdfs = rmStats.getArray("/RIS/plugins/bxdfs");
                var totalBxdfTime = rmStats.sum(bxdfs, function() { 
                                                return rmStats.getFloat("BeginBxdfTime/elapsed");});
                var totalBxdfBegins = rmStats.sum(bxdfs, function() { return rmStats.getInt("NumBeginBxdf");});

                var totalVolumeTime = rmStats.sum(bxdfs, function() { 
                                                return rmStats.getFloat("BeginVolumeTime/elapsed");});
                var totalVolumeBegins = rmStats.sum(bxdfs, function() { return rmStats.getInt("NumBeginVolume");});

                var totalOpacityTime = rmStats.sum(bxdfs, function() { 
                                                return rmStats.getFloat("BeginOpacityTime/elapsed");});
                var totalOpacityBegins = rmStats.sum(bxdfs, function() { return rmStats.getInt("NumBeginOpacity");});
                                
                return rmStats.renderTable(
                  {
                    rows: bxdfs,
                    headers: ["Name", "Bxdf Exec","Volume Exec", "Opacity Exec"],
                    totalRow: ["Total", 
                                rmStats.format( {
                                        value: totalBxdfTime,
                                        style: "seconds"
                                }),
                                rmStats.format( {
                                        value: totalVolumeTime,
                                        style: "seconds"
                                }),
                                rmStats.format( {
                                        value: totalOpacityTime,
                                        style: "seconds"
                                })
                              ],
                    columns: [
                      function() {return rmStats.getAttr('name');},
                      function() {return rmStats.format({
                                    value: rmStats.getFloat('BeginBxdfTime/elapsed')/totalBxdfTime,
                                    style: "percent"
                                  });},
                      function() {return rmStats.format({
                                    value: rmStats.getFloat('BeginVolumeTime/elapsed')/totalVolumeTime,
                                    style: "percent"
                                  });},
                      function() {return rmStats.format({
                                    value: rmStats.getFloat('BeginOpacityTime/elapsed')/totalOpacityTime,
                                    style: "percent"
                                  });}
                    ],
                    
                  }
                );
                }
            },
            // row 2
            {
                label: "Displacement Bounds",
                value: function() {
                  
                  return rmStats.renderTable(
                    {
                      rows: rmStats.getArray("/bounds/dispbounds"),
                      headers: ["Object Name", "Shader Name", "Bound", "Displacement Amount", "Ratio"],
                      columns: [
                        function() {return rmStats.toString('objectName');},
                        function() {return rmStats.toString('displacementShader');},
                        function() {return rmStats.getFloat('displacementBound');},
                        function() {return rmStats.getFloat('displacement');},
                        function() {return rmStats.getFloat('ratio');},
                      ]
                    }
                  );
                }
            }      
            ]
        },

        {
                label: "Patterns",
                note: "Depending on statslevel option to prman, these numbers may change.\nIf statslevel = 1 (default), a patterns time includes the upstream nodes.",
                value: function() {
                var patterns = rmStats.getArray("/RIS/plugins/patterns");

                var totalComputes = rmStats.sum(patterns, function() { 
                                                return rmStats.getInt("NumComputes");});
                var totalComputeTime = rmStats.sum(patterns, function() { 
                                      return rmStats.getFloat("ComputeTime/elapsed");});

                return rmStats.renderTable(
                  {
                    rows: patterns,
                    headers: ["Name", "Computes", "Compute Time"],
                    totalRow: ["Total", 
                                totalComputes,
                                rmStats.format( {
                                        value:totalComputeTime,
                                        style: "seconds"
                                })
                              ],
                    columns: [
                      function() {return rmStats.getAttr('name');},
                      function() {return rmStats.format({
                                    value: rmStats.getInt('NumComputes')/totalComputes,
                                    style: "percent"
                                  });},
                      function() {return rmStats.format({
                                    value: rmStats.getInt('ComputeTime')/totalComputeTime,
                                    style: "percent"
                                  });}
                    ],
                    
                  }
                );
                }
            },
        
        ]
    },
]
}
