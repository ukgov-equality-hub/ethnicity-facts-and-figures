/**
 * Created by Tom.Ridd on 05/05/2017.
 */

function setHeight(chartObject, padding) {
  
  // a subjective value bein used to set how wide the bar appear when there is more than one series
  var multiplier = .66; 
  
  var bar = chartObject.series.length > 1 ? 52 * multiplier : 52;
  var barPadding = 10;
  var seriesLength = 0;
  var padding = padding ? padding : 80 + (chartObject.series.length * barPadding);

  for ( var i = 0; i < chartObject.series.length; i++ ) {
    seriesLength += chartObject.series[i].data.length;
  }

  return ( seriesLength * bar ) + padding;
}

function drawChart(container_id, chartObject) {
    if(chartObject.type === 'bar') {
        return barchart(container_id, chartObject);
    } else if(chartObject.type === 'line') {
        return linechart(container_id, chartObject);
    } else if(chartObject.type === 'component') {
        return componentChart(container_id, chartObject);
    }
}

function barchart(container_id, chartObject) {
    adjustChartObject(chartObject);
    return Highcharts.chart(container_id, {
        colors: ['#2B8CC4', '#F47738', '#28A197', '#F499BE', '#FFBF47', '#95C5E1', '#F9BB9B', '#93D0CB', '#F9CCDE', '#FFDFA3'],
        chart: {
            type:'bar',
            height: setHeight(chartObject)
        },
        title: {
            text: chartObject.title.text
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            title: {
                text: chartObject.yAxis.title.text
            }
        },
        yAxis: {
            title: {
                text: chartObject.xAxis.title.text
            }
        },
        credits: {
            enabled: false
        },
        legend: {
            enabled: (chartObject.series.length > 1)
        },
        plotOptions: {
            bar: {
            dataLabels: {
              enabled: true,
              color: ['#000','#fff'],
              align: 'left',
              style: {
                textOutline: false,
                fontSize: chartObject.series.length <= 1 ? "17px" : "15px",
                fontFamily: "nta",
                fontWeight: "400"
              },
              formatter: function() {
                return this.y > 0.0001 ? this.y : 'Not enough data'
              },
              inside: true,
              rotation: 0
            }
          },
          series: {
            pointPadding: chartObject.series.length > 1 ? 0 : .075,
            groupPadding: 0.1,
            states: {
                hover: {
                    enabled: false
                }
            }
          }
        },
        tooltip: barChartTooltip(chartObject),
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });}

function barChartTooltip(chartObject) {
    if(chartObject.series.length > 1)
    {
        return { pointFormat: '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>'
        + chartObject.number_format.prefix + '{point.y}' + chartObject.number_format.suffix + '</b><br/>' }
    } else {
        return { pointFormat: '<span style="color:{point.color}">\u25CF</span><b>'
        + chartObject.number_format.prefix + '{point.y}' + chartObject.number_format.suffix + '</b><br/>'}
    }
}

function linechart(container_id, chartObject) {
    adjustChartObject(chartObject);

    var yaxis = { 
        title: {
            text: chartObject.yAxis.title.text
        },
        labels: {
            format: chartObject.number_format.prefix + '{value}' + chartObject.number_format.suffix
        }
    };

    if(chartObject.number_format.min !== '') {
        yaxis['min'] = chartObject.number_format.min;
    }
    if(chartObject.number_format.max !== '') {
        yaxis['max'] = chartObject.number_format.max;
    }

    return Highcharts.chart(container_id, {
        chart: {
            marginTop: 20
        },
        colors: ['#2B8CC4', '#F47738', '#28A197', '#F499BE', '#FFBF47', '#95C5E1', '#F9BB9B', '#93D0CB', '#F9CCDE', '#FFDFA3'],
        title: {
            text: chartObject.title.text
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            title: {
                text: chartObject.xAxis.title.text
            }
        },
        yAxis: yaxis,
        tooltip: lineChartTooltip(chartObject),
        credits: {
            enabled: false
        },
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });}


function lineChartTooltip(chartObject) {
    return { pointFormat: '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>'
    + chartObject.number_format.prefix + '{point.y}' + chartObject.number_format.suffix + '</b><br/>' }
}

function componentChart(container_id, chartObject) {
    adjustChartObject(chartObject);
    return Highcharts.chart(container_id, {
        chart: {
            type:'bar'
        },
        title: {
            text:  chartObject.title.text
        },
        xAxis: {
            categories: chartObject.xAxis.categories,
            title: {
                text: chartObject.xAxis.title.text
            }
        },
        yAxis: {
            title: {
                text: chartObject.yAxis.title.text
            }
        },
        legend: {
            reversed: true
        },
        plotOptions: {
            series: {
                stacking: 'normal'
            }
        },
        tooltip: barChartTooltip(chartObject),
        credits: {
            enabled: false
        },
        series: chartObject.series,
        navigation: {
            buttonOptions: {
                enabled: false
          }
        }
    });}

    function adjustChartObject(chartObject) {
        var multiplier = chartObject.number_format.multiplier;
        if(multiplier != 1.0) {
            for(s in chartObject.series) {
                for(d in chartObject.series[s].data) {
                    var value = (multiplier * chartObject.series[s].data[d]);
                    chartObject.series[s].data[d] = Math.round(value * 100)/100;
                }
            }
        }
    }
