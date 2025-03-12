// {
//    identifier: {
//        dataset: [],
//        componentChart: ApexChart(),       
//        previewChart: ApexChart()       
//    }
// }
const REGISTERED_CHARTS = {};

function __blankDataset() {
    var set = [];
    for (let i = 0; i < 60; i++) set.push(0);
    return set;
}


function generateChartComponent(identificator, title, color, componentEl, previewEl) {
    const componentOptions = {
        theme: { mode: 'dark' },
        title: {
            text: title,
            align: 'center',
            offsetY: 6,
            floating: false,
        },
        chart: {
            height: 400,
            fontFamily: 'Ubuntu Sans Mono',
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
            labels: { offsetX: -4 },
            min: 0,
            max: 100,
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
            fontFamily: 'Ubuntu Sans Mono',
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

    var componentChart = new ApexCharts(componentEl, componentOptions);
    var previewChart = new ApexCharts(previewEl, previewOptions);

    REGISTERED_CHARTS[identificator] = {
        dataset: __blankDataset(),
        componentChart: componentChart,
        previewChart: previewChart
    };
}

function initializeCharts() {
    Object.keys(REGISTERED_CHARTS).forEach(
        (identifier) => {
            REGISTERED_CHARTS[identifier].componentChart.render();
            REGISTERED_CHARTS[identifier].previewChart.render();
        }
    );
}

function updateChart(identificator, value) {
    const charts = REGISTERED_CHARTS[identificator];
    
    console.log(REGISTERED_CHARTS, identificator)

    charts.dataset.shift();
    charts.dataset.push(value);

    charts.componentChart.updateSeries([{data: charts.dataset}]);
    charts.previewChart.updateSeries([{data: charts.dataset}]);
}

