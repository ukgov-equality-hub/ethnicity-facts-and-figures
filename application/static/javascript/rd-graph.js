/**
 * Created by Tom.Ridd on 05/05/2017.
 */

function drawChart(container_id, chartObject) {
    console.log(chartObject);

    if(chartObject.type === 'bar') {
        return barchart(container_id, chartObject);
    } else if(chartObject.type === 'line') {
        return linechart(container_id, chartObject);
    } else if(chartObject.type === 'component') {
        return componentChart(container_id, chartObject);
    }
}

function barchart(container_id, chartObject) {
    return Highcharts.chart(container_id, {
        chart: {
            type:'bar'
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
        series: chartObject.series
    });}

function linechart(container_id, chartObject) {
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
        series: chartObject.series
    });}

function componentChart(container_id, chartObject) {
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
        series: chartObject.series
    });}