const REGISTERED_CHARTS = {};

function __blankDataset() {
    var set = [];
    for (let i = 0; i < 60; i++) set.push(0);
    return set;
}


function generateChartMetric(identificator, title, color, metricEl, previewEl, _travelModeChart=false) {
    const metricOptions = {
        theme: { mode: 'dark' },
        title: {
            text: title,
            align: 'center',
            offsetY: 6,
            floating: false,
        },
        subtitle: {
            text: (!_travelModeChart) ? '60 seconds' : '',
            align: 'right',
            offsetY: 6,
            floating: false,
        },
        chart: {
            height: 400,
            fontFamily: 'Roboto Mono',
            type: "area",
            background: '#ffffff00',
            foreColor: 'var(--text-color)',
            toolbar: { show: false },
            zoom: { enabled: (_travelModeChart && !travelModePlaybackType) },
            animations: { enabled: false }
        },
        dataLabels: { enabled: false },
        series: [{ name: 'Value', data: __blankDataset() }],
        fill: {
            type: "gradient",
            gradient: {
                opacityFrom: 0.5,
                opacityTo: 0,
                type: 'diagonal2'
            },
        },
        xaxis: {
            type: "category",
            labels: { show: false },
            axisBorder: { show: false },
            axisTicks: { show: false },
            crosshairs: { show: (_travelModeChart && !travelModePlaybackType) },
        },
        tooltip: { 
            enabled: (_travelModeChart && !travelModePlaybackType),
            y: {
                formatter: function (value, { dataPointIndex, w }) {
                    return `${value}%<br><br>Top CPU usage:<br>${w.config.series[0].data[dataPointIndex].custom}`;
                },
                title: {
                    formatter: () => "",
                },

            }
        },
        yaxis: {
            labels: { offsetX: -4 },
            min: 0,
            max: (_travelModeChart && !travelModePlaybackType) ? undefined : 100,
        },
        stroke: { width: 2 },
        colors: ['var(--accent-color)'],
        grid: {
            show: true,
            borderColor: '#ffffff0f',
            padding: {
                top: 0,
                right: 12,
                bottom: 0,
                left: 8
            },
        },
    }

    const previewOptions = {
        chart: {
            height: 110,
            offsetY: 9,
            fontFamily: 'Roboto Mono',
            type: "area",
            background: '#ffffff00',
            foreColor: 'var(--text-color)',
            toolbar: { show: false },
            zoom: { enabled: false },
            animations: { enabled: false }
        },
        dataLabels: { enabled: false },
        series: [{ data: __blankDataset() }],
        fill: {
            type: "gradient",
            gradient: {
                opacityFrom: 0.5,
                opacityTo: 0,
                type: 'diagonal2'
            },
        },
        xaxis: {
            labels: { show: false },
            axisBorder: { show: false },
            axisTicks: { show: false },
            crosshairs: { show: false },
        },
        tooltip: { enabled: false },
        yaxis: {
            labels: { show: false },
            axisBorder: { show: false },
            axisTicks: { show: false },
            min: 0,
            max: 100,
        },
        stroke: { width: 2 },
        colors: [color],
        grid: {
            show: false,
            padding: {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0
            },
        },
        mounted() {
            this.$nextTick(() => {
                window.dispatchEvent(new Event('resize'));
            });
        }
    }

    var metricChart = new ApexCharts(metricEl, metricOptions);
    if (previewEl) var previewChart = new ApexCharts(previewEl, previewOptions);

    REGISTERED_CHARTS[identificator] = {
        dataset: __blankDataset(),
        metricChart: metricChart,
        previewChart: previewChart ?? null
    };
}

function initializeCharts() {
    Object.keys(REGISTERED_CHARTS).forEach(
        (identifier) => {
            REGISTERED_CHARTS[identifier].metricChart.render();
            REGISTERED_CHARTS[identifier].previewChart?.render();
        }
    );
}

function updateChart(identificator, value, noShift=false) {
    const charts = REGISTERED_CHARTS[identificator];
    if (!charts || value == undefined) return;

    try {
        if (!noShift) charts.dataset.shift();
        charts.dataset.push(value);
        
        charts.metricChart.updateSeries([{data: charts.dataset}]);
        charts.previewChart?.updateSeries([{data: charts.dataset}]);
    } catch {
        console.warn(`Failed to update chart: ${identificator}. Removing from register...`);
        delete REGISTERED_CHARTS[identificator];
    }
}

