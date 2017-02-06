
//MAIN PAGE Container
view =
{
 //label: "Memory",
  columns: 2,
  children: [ 
    {
      width: 8,
      note: "Peak resident memory is sampled at a frequency that does not match peak allocation in each category. Therefore unaccounted memory is only an estimation.",
      value: function() {
        
        return rmStats.renderTable({
          style: "memory",
          expandable: false,
          rows: rmStats.getMemoryStats(),
          removeZeros: true
        });
      }
    },
    {
      width: 4,
      height: 500,
      value: function() {
          return rmStats.renderChart({
            type:"verticalBar",
            data:{
              rows: rmStats.getMemoryStats({removeZeros:true, sort:true}),  //combine any < 5% into "other"
              label: function() {return rmStats.getDesc() + " - " + rmStats.format({
                                                      value:rmStats.getValue('.'),
                                                      style: 'bytes'});},
              value: function() {return rmStats.getValue('.');},
              
            }
          });
        }
    }
  ]

}
