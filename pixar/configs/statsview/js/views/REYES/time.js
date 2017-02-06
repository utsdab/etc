view = {  //MAIN PAGE Container
          value: function() {
          	var timers = rmStats.find("/time/timers/*");
          	timers = rmStats.filter(timers, function() {
          		if(rmStats.getName() == 'totaltime')
          			return false;
          		else
          			return true;
          	});
          	var total = rmStats.find("/time/timers/totaltime");

          	return rmStats.renderTable({
          									style: "timer",
          									rows: timers,
          									totalRow: total,
                                                       collapse: true,
          								});
          },
       }