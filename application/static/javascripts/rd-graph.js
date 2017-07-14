/**
 * Created by Tom.Ridd on 05/05/2017.
 */

function setColour(chartObject) {
    var colours = ['#2B8CC4', '#F44336', '#4CAF50', '#FFC107', '#9C27B0', '#00BCD4'];
    return chartObject.type === 'line' ? colours : chartObject.series.length === 4 ? ['#2B8CC4', '#4891BB', '#76A6C2', '#B3CBD9'] : chartObject.series.length === 3 ? ['#2B8CC4', '#76A6C2', '#B3CBD9'] : chartObject.series.length === 2 ? ['#2B8CC4', '#B3CBD9'] : colours;
}

function setHeight(chartObject, padding) {
  var bar = chartObject.series.length > 1 ? 30 : chartObject.type === 'small_bar' ? 25 : 33;
  var barPadding = 10;
  var seriesLength = 0;
  var padding = padding ? padding : 160;

  for ( var i = 0; i < chartObject.series.length; i++ ) {
    seriesLength += chartObject.series[i].data.length;
  }

  return ( seriesLength * bar ) + padding;
}

function drawChart(container_id, chartObject) {
    if(chartObject) {
        if (chartObject.type === 'bar') {
            return barchart(container_id, chartObject);
        } else if (chartObject.type === 'line') {
            return linechart(container_id, chartObject);
        } else if (chartObject.type === 'component') {
            return componentChart(container_id, chartObject);
        } else if (chartObject.type === 'panel_bar_chart') {
            return panelBarchart(container_id, chartObject);
        } else if (chartObject.type === 'panel_line_chart') {
            return panelLinechart(container_id, chartObject);
        }
    }
}

function barchart(container_id, chartObject) {
    adjustChartObject(chartObject);
    setDecimalPlaces(chartObject);

    return Highcharts.chart(container_id, {
        colors: setColour(chartObject),
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
            },
            labels: {
                style: {
                    textOverflow: 'none'
                }
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
                fontSize: chartObject.series.length <= 1 ? "17px" : "14px",
                fontFamily: "nta",
                fontWeight: "400"
              },
              formatter: function() {
                return this.y > 0.0001 ? formatNumberWithDecimalPlaces(this.y, chartObject.decimalPlaces) :
                    'Not enough data'
              },
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

function panelBarchart(container_id, chartObject) {

    var internal_divs = "<div class='small-chart-title'>" + chartObject.title.text + "</div>";
    for(var c in chartObject.panels) {
        internal_divs = internal_divs + "<div id=\"" + container_id + "_" + c + "\" class=\"chart-container column-one-third\"></div>";
    }
    $('#' + container_id).html(internal_divs);

    var charts = [];
    for(c in chartObject.panels) {
        var panel_container_id = container_id + "_" + c;
        var panelChart = chartObject.panels[c];
        charts.push(smallBarchart(panel_container_id, panelChart));
    };
    return charts;
}

function smallBarchart(container_id, chartObject) {
    adjustChartObject(chartObject);
    return Highcharts.chart(container_id, {
        colors: setColour(chartObject),
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
            },
            labels: {
                style: {
                    textOverflow: 'none'
                }
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
                fontSize: chartObject.series.length <= 1 ? "17px" : "14px",
                fontFamily: "nta",
                fontWeight: "400"
              },
              formatter: function() {
                return this.y > 0.0001 ? formatNumberWithDecimalPlaces(this.y, chartObject.decimalPlaces) : 'Not enough data'
              },
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


function panelLinechart(container_id, chartObject) {

    var internal_divs = "<div class='small-chart-title'>" + chartObject.title.text + "</div>";
    for(var c in chartObject.panels) {
        internal_divs = internal_divs + "<div id=\"" + container_id + "_" + c + "\" class=\"chart-container column-one-half\"></div>";
    }
    $('#' + container_id).html(internal_divs);

    var charts = [];
    for(c in chartObject.panels) {
        var panel_container_id = container_id + "_" + c;
        var panelChart = chartObject.panels[c];
        charts.push(smallLinechart(panel_container_id, panelChart));
    };
    return charts;
}

function smallLinechart(container_id, chartObject) {
    adjustChartObject(chartObject);

    var yaxis = {
        title: {
            text: chartObject.yAxis.title.text
        },
        labels: {
            format: chartObject.number_format.prefix + decimalPointFormat('value', chartObject.decimalPlaces) + chartObject.number_format.suffix
        }
    };

    for(var i = 0; i < chartObject.series.length; i++) {
        chartObject.series[i].marker = { symbol: 'circle' };
    }

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
        colors: setColour(chartObject),
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

function barChartTooltip(chartObject) {
    if(chartObject.series.length > 1)
    {
        return { pointFormat: '<span style="color:{point.color}">\u25CF</span> {series.name}: <b>'
        + chartObject.number_format.prefix
        + decimalPointFormat('point.y', chartObject.decimalPlaces)
        + chartObject.number_format.suffix + '</b><br/>' }
    } else {
        return { pointFormat: '<span style="color:{point.color}">\u25CF</span><b>'
        + chartObject.number_format.prefix
        + decimalPointFormat('point.y', chartObject.decimalPlaces)
        + chartObject.number_format.suffix + '</b><br/>'}
    }
}

function linechart(container_id, chartObject) {
    adjustChartObject(chartObject);
    setDecimalPlaces(chartObject);

    var yaxis = { 
        title: {
            text: chartObject.yAxis.title.text
        },
        labels: {
            format: chartObject.number_format.prefix + decimalPointFormat('value', chartObject.decimalPlaces) + chartObject.number_format.suffix
        }
    };

    for(var i = 0; i < chartObject.series.length; i++) {
        chartObject.series[i].marker = { symbol: 'circle' };
    }

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
        colors: setColour(chartObject),
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
    + chartObject.number_format.prefix
    + decimalPointFormat('point.y', chartObject.decimalPlaces)
    + chartObject.number_format.suffix + '</b><br/>' }
}

function decimalPointFormat(label, dp) {
    if(dp && dp > 0) {
        return '{' + label + ':.' + dp + 'f}';
    }
    return '{' + label + '}';
}

function componentChart(container_id, chartObject) {
    adjustChartObject(chartObject);
    setDecimalPlaces(chartObject);

    return Highcharts.chart(container_id, {
        chart: {
            type:'bar',
            height: setHeight(chartObject)
        },
        colors: setColour(chartObject),
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
        if(multiplier !== 1.0) {
            for(var s in chartObject.series) {
                for(var d in chartObject.series[s].data) {
                    var value = (multiplier * chartObject.series[s].data[d]);
                    chartObject.series[s].data[d] = Math.round(value * 100)/100;
                }
            }
        }
    }

    function setDecimalPlaces(chartObject) {
        var values = _.flatten(_.map(chartObject.series, function (series) { return series.data }));
        chartObject.decimalPlaces = seriesDecimalPlaces(values);
    }
