/**
 * Created by Tom.Ridd on 05/05/2017.
 */

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
        chart: {
            type:'bar',
            height: 600
        },
        title: {
            text: chartObject.title.text
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
        credits: {
            enabled: false
        },
        legend: {
            enabled: (chartObject.series.length > 1)
        },
        plotOptions: {
            bar: {
            pointWidth: 45,
            dataLabels: {
              enabled: true,
              color: '#000',
              align: 'left',
              style: {
                textOutline: false,
                fontSize: "16px",
                fontFamily: "nta",
                fontWeight: "400"
              },
              formatter: function() {
                return this.y > 0.0001 ? this.y : 'Sample size too small'
              },
              inside: true,
              rotation: 0
            }
          },
          series: {
            states: {
                hover: {
                    enabled: false
                }
            }
          }
        },
        tooltip: barChartTooltip(chartObject),
        series: chartObject.series
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
    return Highcharts.chart(container_id, {

        title: {
            text: chartObject.title.text
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
        tooltip: lineChartTooltip(chartObject),
        credits: {
            enabled: false
        },
        series: chartObject.series
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
        series: chartObject.series
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
