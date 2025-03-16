let processesTable = new DataTable("#processesTable", {
    data: [],
    paging: false,
    info: false,
    scrollResize: true,
    scrollY: 100,
    scrollCollapse: true,
    searching: false,
    layout: {
        topStart: null,
        topEnd: null
    },
    rowId: row => `proc-row-${row.pid}`,
    columns: [
        { 
            data: 'name', 
            className: "dt-head-center dt-td-name" 
        },
        { 
            data: 'pid',
            className: "dt-head-center dt-body-left dt-td-less-important",
            width: "100px"
        },
        {
            data: 'cpu_usage',
            className: "dt-head-center dt-body-center",
        },
        {
            data: 'mem_use_mb',
            className: "dt-head-center dt-body-center",
        },
        {
            data: 'threads', 
            width: "140px",
            className: "dt-head-center dt-body-center dt-td-less-important",
        },
        {
            data: 'started',
            width: "200px",
            className: "dt-head-center dt-body-center dt-td-less-important",
        },
        {
            className: "dt-head-center dt-body-center",
            data: null,
            width: "100px",
            defaultContent: '<button class="processKillBtn">kill</button>',
            targets: -1,
            sortable: false,
        }
    ]
})


function handleProcessesUpdatePacket(packet) {
    Object.entries(packet).forEach(
        ([pid, data]) => {
            const row = processesTable.row(`#proc-row-${pid}`);

            if (data.status === false) {
                if (row.data() !== undefined) row.remove().draw();
                return;
            }
            
            if (row.data() === undefined) return processesTable.row.add(data).draw();
            row.data(data).draw();
        }
    )
}

processesTable.on('click', 'button', function (e) {
    let data = processesTable.row(e.target.closest('tr')).data();
    _sendMessageToServer(EV_REQUEST_PROC_KILL, data.pid);
    console.log("Sent process kill request: ", data.pid);
});

