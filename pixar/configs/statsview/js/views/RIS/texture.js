var haveTexture = rmStats.getArray("/texture/textureFiles");
if (haveTexture.length)
{
view = {  //MAIN PAGE Container
           //label: "Textures",
    children: [



    // row 1
    {
        columns: 2,
        children: [
            {
                label: "Cache",
                value: function() {
                    var cacheUsed = rmStats.getValue("/texture/textureTileCache/size");
                    var cacheSize = rmStats.getInt("/options/textureMemory")*1024; //kb -> bytes
                    var rows = [["Size", rmStats.format({value: cacheSize, style:"bytes"})],
                                ["Used", rmStats.format({value: cacheUsed, style:"bytes"})],
                                ["% Used", rmStats.format({value: cacheUsed/(cacheSize), style:"percent"})],
                                ["I/O Bytes:", rmStats.format({value: rmStats.getValue("/texture/textureTileCache/bytesRead"),
                                    format: "bytes"})],
                                ["I/O Time:", rmStats.toString("/texture/textureTileCache/readTime")],
                                ];
                                
                    return rmStats.renderSimpleTable(rows);
                }
            },
/*
            {
                value: function() {

                    var totalTime = readTime + decompressTime;
                    var rows = [["Read Time", rmStats.format({value: readTime, style:"seconds"}), 
                                rmStats.format({value: readTime/totalTime, style:"percent"})],
                                ["Decompress Time", rmStats.format({value: decompressTime, style:"seconds"}), 
                                rmStats.format({value: decompressTime/totalTime, style:"percent"})]];
                    return rmStats.renderTable({
                        rows: rows,
                        headers: ["", "Time", "Percent Total"],
                        totalRow: ["Total Time", rmStats.format({value: totalTime, style:"seconds"}), "100.0%"]
                    });
                }
            },
 */
            {
                label: "Filter Widths",
                value: function() {
                    return rmStats.renderChart(
                              {
                                type: "histogram",
                                xAxisTitle: "Filter Width",
                                yAxisTitle: "Samples",
                                data: {
                                  rows: rmStats.getArray("/texture/textureFiltering/filterWidthHist"),
                                  label: function() { return rmStats.getAttr("label");},
                                  value: function() { return rmStats.getInt('.');}
                                }
                              }
                            );
                }

            },             
/*
            {
                value: function() {
                    var rows = rmStats.find("/texture/textureTileCache/int");
                                
                    return rmStats.renderTable({
                        rows: rows,
                        headers: ['Name', 'Value'],
                        columns: [
                            function() { return rmStats.getName();},
                            function() { return rmStats.getInt(".");},
                        ],
                    });
                }
            }
*/
        ]
    },

    // row 2
    {
        columns: 1,
        children: [
        // col 1
        {
        label: "Files",
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
                        }),
                        "100.0 %"
                    ]
                    
                }
            );

            }
        },
        // col 2
        ]
    },
  ]
}

} else {
    view = { label: "No Textures Used" }
}
