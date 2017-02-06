view = 
{
  //MAIN PAGE Container
  //label: "Overview",
  children: [  // a  list of the items under the above label
    // Row 1
    {
      columns: 4,
      children: [
        {
          label: "Performance",   
          value: function() {
            rows =
            [
              // Time and memory
              ["Time:", //rmStats.renderLines([
                        rmStats.format({value: rmStats.getFloat('/time/timers/totaltime'), 
                                        style: "time",
                                        textStyle: "bold"}),
                        /*" (user: " + rmStats.format({value: rmStats.getFloat('/time/timers/totaltime/user'), 
                                                    style: "time", 
                                                    textStyle: "bold"})
                        + " system: " + rmStats.format({value: rmStats.getFloat('/time/timers/totaltime/system'), 
                                                    style: "time", 
                                                    textStyle: "bold"}) + ")"])*/],
              ["Memory:", rmStats.format({value:rmStats.toString('/memory/systemMem/peakResidentSize'), 
                                            textStyle: "bold"})],
              ["Threads:", rmStats.getInt("/options/threads")],
              ["Utilization:", rmStats.format({
                  value: (rmStats.getCPUTime() / rmStats.getThreads()) / rmStats.getWallTime(),
                  style: "percent"})],
              //"Serial time:",
              //"Parallel time:",
              //"Machine: name, # procs, memory capacity"            
            ];
            return rmStats.renderSimpleTable(rows);
          }
        },
        {
        label:'Time',
        value: function() {
              return rmStats.renderChart({
                type:"verticalBar",
                data:{
                  rows: rmStats.getTimeStats({removeZeros:true, combineThreshold: 0.03, sort:true}), //combine any < 5% into "other"
                  label: function() {return rmStats.getDesc() + " - " + rmStats.format({
                                                          value:rmStats.getValue('.'),
                                                          style: 'seconds'});},
                  value: function() {return rmStats.getValue('.');},
                  //style: "timer",
                }
              });
            }
        },
        {
        label:'Memory',
        value: function() {
            return rmStats.renderChart({
              type:"verticalBar",
              data:{
                rows: rmStats.getMemoryStats({removeZeros:true, combineThreshold: 0.03, sort:true}),  //combine any < 5% into "other"
                label: function() {return rmStats.getDesc() + " - " + rmStats.format({
                                                        value:rmStats.getValue('.'),
                                                        style: 'bytes'});},
                value: function() {return rmStats.getValue('.');},
                
              }
            });
          }
        },
        {
          label:'Render time heatmap',
          value: function() {
            return rmStats.renderHeatMap({data: rmStats.find("/RIS/rayHider/cpuTimeMap"),
                                scale: 0, colorMethod: 0});
          }
        },
      ]
    },

    // Row 2
    {
      columns: 3,
      children: [
        {
          width: 3,
          label: "Image and Samples",   
          value: function() {
            rows =
            [
              // Sampling Configuration
              ["Resolution:", rmStats.getInt("/options/xRes") + " x "
                          + rmStats.getInt("/options/yRes")], 
              ["Channels:", rmStats.getText("/options/displaylist/display_0/mode")],
              ["AOVs:", (rmStats.count("/options/displaylist") - 1)],
              ["Samples:", "min - " + rmStats.getInt("/options/minSamples") + "," +
                            " max - " + rmStats.getInt("/options/maxSamples")],
              ["", rmStats.format({
                                value: (rmStats.getInt("/options/maxSamples") *
                                      (1.0 - rmStats.getValue("/RIS/rayHider/adaptSkipped"))),
                                style: "float"}) + " avg"],
              ["Pixel Variance:", rmStats.getFloat("/options/pixelVariance")],
              ["Rendered:", rmStats.getRenderDate()],
              ["", rmStats.getRenderTime()], //
              ["Build ID:", rmStats.getBuildID()],
            ];
            return rmStats.renderSimpleTable(rows);
          }
        },        
        {
          width: 3,
          label: "Integrator",
          value: function() {
                var iName = rmStats.getName("/RIS/plugins/integrator/stats");
                rows =
                [
                  ["Name:", rmStats.format({value:iName, textStyle:"bold"})],
                ];


                if(iName == "PxrPathTracer" || iName == "PxrVCM") {
                  rows.push(["Max Path Length:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/maxPathLength")]);
                  rows.push(["Bxdf Samples:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/numBxdfSamples")]);
                  rows.push(["Light Samples:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/numLightSamples")]);
                }

                if(iName == "PxrPathTracer") {
                  var sampleMode = rmStats.getValue("/RIS/plugins/integrator/stats/parameters/sampleMode").trim(); //why is there whitspace in xml??
                  rows.push(["Sample Mode:", sampleMode]);
                  if (sampleMode == "Bxdf") {
                    rows.push(["Indirect Samples:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/numIndirectSamples")]);
                  } 
                  else {
                    rows.push(["Diffuse Samples:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/numDiffuseSamples")]);
                    rows.push(["Specular Samples:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/numSpecularSamples")]);
                    rows.push(["Subsurface Samples:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/numSubsurfaceSamples")]);
                    rows.push(["Refraction Samples:", rmStats.getValue("/RIS/plugins/integrator/stats/parameters/numRefractionSamples")]);
                  }
                }
                return rmStats.renderSimpleTable(rows);
              }
        },
        {
          width: 6,
          label: "Raytracing",
          value: function() {
            var raysByType = rmStats.getArray("/rayAccel/raysByType");
            var sum = rmStats.sum(raysByType, function() {return rmStats.getInt('.');});
            var pixels = ( rmStats.getFloat('/options/xRes') * 
                                  rmStats.getFloat('/options/yRes') *
                                  ( rmStats.getFloat('/options/cropRight') - rmStats.getFloat('/options/cropLeft') ) *
                                  ( rmStats.getFloat('/options/cropBottom') - rmStats.getFloat('/options/cropTop') ) );
            var samples = pixels * rmStats.getFloat('/options/xSamples') *
                                  rmStats.getFloat('/options/ySamples');

            return rmStats.renderTable(
              {
                rows: raysByType,
                headers: ["Ray Type", "# Rays", "Per Pixel", 
                          "% Total"],
                totalRow: ["Totals", 
                            rmStats.format({value:sum, style: "int"}),
                            rmStats.format({
                              value: sum/pixels,
                              style: 'float',  
                            }),
                            ""
                          ],
                columns: [
                  function() {return rmStats.getAttr('name');},
                  function() {return rmStats.toString('.');},
                  function() {return rmStats.format(
                    {
                      value:rmStats.getFloat('.') /pixels,
                      style:'float'
                    });
                  },
                  function() {
                    return rmStats.format(
                      {
                        value:rmStats.getFloat('.') / sum,
                        style:'percent'
                      });
                  }   
                ]
              }
            );
          }
        },

       //row 2
        /*    {
              note: "This chart shows how a progressive render incrementally refines.  \
                    If this line is flat, and adaptivity is enabled, try adjusting your PixelVariance.",
              value: function() {
                return rmStats.renderChart({
                  label: rmStats.getDesc("/RIS/rayHider/adaptActive"),
                  xAxisTitle: "Increment",
                  yAxisTitle: "Active Pixels",
                  type: "spline",
                  data: {
                      rows: rmStats.getArray("."),
                      value: function() { return [parseInt(rmStats.getAttr("label")), rmStats.getInt('.')];}
                    }
                });
              }
            }
          ]
        }    */


      ]
    },

    
    // Row 3
    {
      columns: 4,
      children: [
        {
          label: "Shading",
          value: function() {
            var sctx = rmStats.find("/RIS/sctx");
            //console.log(sctx);
            rows =
            [
              ["Time:", rmStats.toString("/RIS/sctx/sctxExecTime")],
              ["Memory:", rmStats.toString("/RIS/sctx/shadingMem")],
              ["Points/Shader Invoke:", rmStats.format({
                          value: rmStats.getInt("/RIS/sctx/numPts")/rmStats.getInt("/RIS/sctx/stcxExecCount"),
                          style: "float"})],
              //["Opacity cache hit rate:", "0.0%"],
            ];
            return rmStats.renderSimpleTable(rows);
          }
        },
        {
          label: "Lighting",
          value: function() {
            rows =
            [
              ["Material Eval Time:", rmStats.toString("/RIS/Lighting/lightingMaterialTime")],
              ["Light Sample Time:", rmStats.toString("/RIS/Lighting/lightingLightSampleTime")],
              ["Photon Sample Time:", rmStats.toString("/RIS/Lighting/lightingPhotonSampleTime")],
            ];
            return rmStats.renderSimpleTable(rows);
          }
        },  
        {
          label: "Texture",
          value: function() {
            // Texture 2D
            var hits2D = rmStats.getInt("/texture/textureTileCache/hits");
            var lookups2D = rmStats.getInt("/texture/textureTileCache/lookups");
            var cacheUsed2D = rmStats.getValue("/texture/textureTileCache/size");
            var cacheSize2D = rmStats.getInt("/options/textureMemory")*1024; //kb -> bytes
            var cacheUse2D = (cacheSize2D==0)? 0 : cacheUsed2D/cacheSize2D;
            var hitPercent2D = (lookups2D==0)? 0 : hits2D/lookups2D;
            // ptex
            var hitsPtex = rmStats.getInt("/texture/ptextureCache/ptxDHits");
            var lookupsPtex = hitsPtex + rmStats.getInt("/texture/ptextureCache/ptxDMisses");
            var cacheUsedPtex = rmStats.getInt("/texture/ptextureCache/ptxCacheMem/peak");
            var cacheSizePtex = rmStats.getInt("/options/ptextureMemory")*1024; //kb -> bytes
            var cacheUsePtex = (cacheSizePtex==0)? 0 : cacheUsedPtex/cacheSizePtex;
            var hitPercentPtex = (lookupsPtex==0)? 0 : hitsPtex/lookupsPtex;

            rows =
            [
              ["2D Cache Use:", rmStats.format({value: cacheUse2D, style: "percent"}) ],
              ["2D Cache Hit Rate:", rmStats.format({value: hitPercent2D, style: "percent"}) ],
              ["2D Filter Time:", rmStats.toString("/texture/textureFiltering/filterTime")],
              //["3D Cache Use:", "0.0%"],
              //["3D Cache Hit Rate:", "0.0%"],
              //["3D Filter Time:", rmStats.toString("/texture/textureFiltering/filterTime")],
              ["Ptex Cache Use:", rmStats.format({value: cacheUsePtex, style: "percent"})],
              ["Ptex Cache Hit Rate:", rmStats.format({value: hitPercentPtex, style: "percent"})],
              ["Ptex Filter Time:", rmStats.toString("/texture/PTex Filtering/ptexFilter")],
            ];
            return rmStats.renderSimpleTable(rows);
          }
        },
        {
          label: "Geometry",
          pushd: "/geometry",
          value: function() {
            rows =
            [
              ["RIB Polygon Count:", rmStats.format({value: (rmStats.getValue("polyRibPolyCount") +
                                                            rmStats.getValue("subdRibPolyCount") +
                                                            rmStats.getValue("curveRibStrandCount")),
                                                    style: "int"})],
              ["Tesselated Poly Count:", rmStats.format({value: (rmStats.getValue("polyTriCountOverall") +
                                                            rmStats.getValue("subdTriCountOverall") +
                                                            rmStats.getValue("curveTriCountOverall")),
                                                    style: "int"})],
              ["Procedurals:", rmStats.getInt("proceduralsMade")],
              ["Tesselation Cache Mem:", rmStats.toString("/rayGprim/gutCacheMem")]
            ];
            return rmStats.renderSimpleTable(rows);
          }
        }
      ]
    },

   /* {
      columns: 2,
      children:[
        {
        label:'Time',
        width: 5,
        value: function() {
              return rmStats.renderChart({
                type:"pie",
                data:{
                  rows: rmStats.getTimeStats({removeZeros:true, combineThreshold: 0.03, sort:true}), //combine any < 5% into "other"
                  label: function() {return rmStats.getDesc() + " - " + rmStats.format({
                                                          value:rmStats.getValue('.'),
                                                          style: 'seconds'});},
                  value: function() {return rmStats.getValue('.');},
                  //style: "timer",
                }
              });
            }
        },
        {
        label:'Memory',
        width: 7,
        value: function() {
            return rmStats.renderChart({
              type:"memoryBar",
              data:{
                rows: rmStats.getMemoryStats({removeZeros:true, combineThreshold: 0.03, sort:true}),  //combine any < 5% into "other"
                label: function() {return rmStats.getDesc() + " - " + rmStats.format({
                                                        value:rmStats.getValue('.'),
                                                        style: 'bytes'});},
                value: function() {return rmStats.getValue('.');},
                
              }
            });
          }
        }
      ]
    },
    */

    // Row 4
    /*{ 
      columns: 3,
      children: [
        {
          label:'Raytracing',
          columns: 2,
          children: [
            
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

        {
        label:'Geometry'
        },

        {
        label:'Most expensive'
        }
      ]
    }, // Row 4*/

    // Row 4
    


  ]
};
      
