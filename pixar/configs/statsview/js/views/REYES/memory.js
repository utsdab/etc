view = {  //MAIN PAGE Container
          //label: "Memory",
          columns: 2,
          children: [ 
            {
              value: function() {
                    var subsystems = rmStats.find("/memory/subsystems/memory");
                    var totalMem = rmStats.getInt("/memory/systemMem/peakResidentSize");
                    var subTotal = rmStats.getInt("/memory/subsystemMem/peak");

                    var totalRow = rmStats.find("/memory/systemMem/peakResidentSize");

                    var rows = subsystems.slice();
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
                var totalMem = rmStats.getInt("/memory/systemMem/peakResidentSize");
                var subTotal = rmStats.getInt("/memory/subsystemMem/peak");
                
                var rows = subsystems.slice();
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
       }