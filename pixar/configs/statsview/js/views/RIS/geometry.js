//MAIN PAGE Container
view =
{
// rows  
children: [
    
    // first row
    {  
          //label: "Time",
          columns: 2,
          children: [
          	{
          		label: "GPrims by type",
          		pushd: "/geometry",
  				value: function() {
  					var rows = [["Procedurals", rmStats.getInt("proceduralsMade")],
  								["Polygons", rmStats.getInt("polyRibPolyCount")], 
  								["Subdiv Cage Polygons", rmStats.getInt("subdRibPolyCount")],
  								["Curve Strands", rmStats.getInt("curveRibStrandCount")]];
  					return rmStats.renderTable({
  						rows: rows,
  						headers: ["Type", "Count"],
  					});
  				}
  			},
  			{
          		label: "Raytrace counts",
          		pushd: "/geometry",
  				value: function() {
  					var data = [{label:"Polygons", data:[[0, rmStats.getInt("polyTriCountFine")],
  														[1, rmStats.getInt("polyTriCountMedium")],
  														[2, rmStats.getInt("polyTriCountCoarse"),]]},
  								{label:"Subdivs", data:[[0, rmStats.getInt("subdTriCountFine")],
  														[1, rmStats.getInt("subdTriCountMedium")],
  														[2, rmStats.getInt("subdTriCountCoarse"),]]},
  								{label:"Curves", data:[[0, rmStats.getInt("curveTriCountFine")],
  														[1, rmStats.getInt("curveTriCountMedium")],
  														[2, rmStats.getInt("curveTriCountCoarse"),]]},
  														];
  					return rmStats.renderChart({
  						label: "",
  						type: "stackedColumn",
  						xAxisTitle: "Refinement",
  						yAxisTitle: "Rays",
  						data: data,
  						xAxisLabels: ['Fine', 'Medium', 'Coarse']
  					});
  				}
  			}
          ]
    },

    // second row
  ]
}