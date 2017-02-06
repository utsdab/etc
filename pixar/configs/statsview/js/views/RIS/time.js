//MAIN PAGE Container
view = { 
  columns: 1,
  children: [
  // column 1
    {
          width:8,
          value: function() {
                return rmStats.format({
                                              style: "note",
                                              value: "Note: Timers are not independent and may sum to more than total render time."
                                         });
          },
        },
    {
          width:8,
          note: "Times are expressed as total time spent in CPU.\
          This differs from Wall Clock time, i.e the time \
          a render actually takes.",

          value: function() {
                return rmStats.renderTable({
                                              style: "timer_nototal",
                                              expandable: false,
                                              rows: rmStats.getTimeStats(),
                                              removeZeros: true
                                         });
          },
        },
        {
          width:8,
          label: "CPU Utilization Estimate",
          note: "CPU utilization assumes no other processes are running.  \
                           Other factors such as hyperthreading, I/O, CPU frequency \
                           variation, etc; could bring this number down.",
          value: function() {
                    return rmStats.format({
                         style: "string",
                         textstyle: "large",
                         value: "( CPU time = " + rmStats.format({value: rmStats.getCPUTime(),
                                                                      style: "seconds"}) + " / " + rmStats.getThreads() +
                              " Threads ) / ( Clock time =  " + rmStats.format({value: rmStats.getWallTime(),
                                                                      style: "seconds"}) + " ) = " +
                              rmStats.format({
                                             value: (rmStats.getCPUTime() / rmStats.getThreads()) / 
                                                    rmStats.getWallTime(),
                                             style: "percent"
                                        }) + " Utilization.",
          })}
        }
      ]
};