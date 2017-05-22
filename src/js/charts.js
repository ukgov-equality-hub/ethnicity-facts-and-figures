$(document).ready(function () {

  // demo highcharts configuaration for bar charts

  if($(".chart").length) {
    Highcharts.chart('chart', {
      colors: ['#85AFD0'],
      chart: {
        type: 'bar',
        marginBottom: true,
        marginLeft: 160
      },
      title: {
        text: ''
      },
      xAxis: {
        categories: ['Indian', 'Pakistani', 'Other Asian', 'Black', 'Chinese', 'Mixed', 'White', 'Other'],
        title: {
          text: null
        }
      },
      yAxis: {
        min: 0,
        max: 15,
        title: {
          text: 'unemployment rate (%)',
          align: 'high'
        },
        labels: {
          overflow: 'justify'
        }
      },
      labels: {
        style: {
          fontFamily: "nta"
        }
      },
      plotOptions: {
        bar: {
          pointWidth: 40, 
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
            formatter: function() {return this.y + '%'},
            inside: true,
            rotation: 0
          }
        }
      },
      credits: {
        enabled: false
      },
      series: [{
        name: 'unemployment rate',
        data: [10, 10, 5, 10, 10, 10, 5, 9]
      }]
    });
  }

});