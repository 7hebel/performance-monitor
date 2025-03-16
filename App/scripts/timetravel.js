let REALTIME_MODE = true;
let travelModeCluster = null;
let travelModeDumps = null;
let travelModeMinute = null;
let travelModeSecond = null;
let travelModeTicker = null;


function switchTimeTravelMode() {
    if (!gotPerfComposition) return;
    
    REALTIME_MODE = !REALTIME_MODE;
    if (REALTIME_MODE) {
        document.getElementById("performanceTimingName").textContent = "Realtime";
        document.getElementById("performanceHistoryBtn").className = "fa-solid fa-clock-rotate-left";
        document.documentElement.style.setProperty("--perf-timing-color", "#97c47e");
        gotPerfComposition = false;

        hideTimeTravelPanel();
        clearPerformancePage();
        resetTicker();

        _sendMessageToServer(EV_REQUEST_COMPOSITION);
        console.log("Exit time travel mode");
    } else {
        document.getElementById("performanceTimingName").textContent = "Time Travel mode";
        document.getElementById("performanceHistoryBtn").className = "fa-solid fa-arrow-left";
        document.documentElement.style.setProperty("--perf-timing-color", "#ca6565");

        fetchAndApplyHistoryPoints();
        console.log("Entered time travel mode");
    }
}


function fetchAndApplyHistoryPoints() {
    const options = {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    };

    fetch(HTTP_PROTO + "://" + API_ADDRESS + "/perf-history/points", options)
        .then(response => response.json())
        .then(historyPoints => {
            setupTimeTravelPanel(historyPoints);

        })
        .catch(error => {
            console.error('Error while fetching performanceHistoryPoints', error);
            switchTimeTravelMode();
        });
}


function hideTimeTravelPanel() {
    const panel = document.getElementById("performanceTimetravelPanel");
    const datesContainer = document.getElementById("timetravelDate");
    const hoursContainer = document.getElementById("timetravelHours");
    panel.setAttribute("hidden", "1");

    Array.from(hoursContainer.children).forEach(opt => {
        if (opt.value != 0) opt.remove();
    })
    Array.from(datesContainer.children).forEach(opt => {
        if (opt.value != 0) opt.remove();
    })

}


function setupTimeTravelPanel(historyPoints) {
    const panel = document.getElementById("performanceTimetravelPanel");
    const datesContainer = document.getElementById("timetravelDate");
    const hoursContainer = document.getElementById("timetravelHours");

    panel.setAttribute("hidden", "0");

    Object.keys(historyPoints).forEach(date => {
        const option = document.createElement("option");
        option.textContent = date;
        option.value = date;
        datesContainer.appendChild(option);
    })

    datesContainer.onchange = (e) => {
        Array.from(hoursContainer.children).forEach(opt => {
            if (opt.value != 0) opt.remove();
        })
        if (datesContainer.value == 0) return;

        historyPoints[datesContainer.value].forEach(clusterData => {
            const option = document.createElement("option");
            option.textContent = clusterData.timeinfo;
            option.value = clusterData.cluster + "|" + clusterData.hour;
            hoursContainer.appendChild(option);
        })
    }

    hoursContainer.onchange = (e) => {
        const data = e.target.value;
        const hour = data.split("|")[1];
        document.getElementById("timetravelCurrentHour").innerText = hour;
        updateTimetravelMinute(0);
        updateTimetravelSecond(0);
    }
}

function resetTicker() {
    clearInterval(travelModeTicker);
    travelModeMinute = null;
    updateTimetravelMinute(0);
    updateTimetravelSecond(0);
}

function queryTravelData() {
    resetTicker();

    const cluster = document.getElementById("timetravelHours").value.split("|")[0];
    if (cluster == 0) return;

    const options = {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    };

    fetch(HTTP_PROTO + "://" + API_ADDRESS + "/perf-history/query-cluster/" + cluster, options)
        .then(response => response.json())
        .then(clusterData => {
            clearPerformancePage(true);
            clusterData.composition.forEach(data => {
                addMonitorHeader(data.categoryId, data.targetTitle);
                buildDataPage(data.categoryId, data.targetTitle, data.productInfo, data.color, data.metrics);
            });

            travelModeCluster = cluster;
            travelModeDumps = clusterData.dumps;
            travelModeTicker = setInterval(timetravelTick, 1000);

        })
        .catch(error => {
            console.error('Error while fetching clusterData: ' + cluster, error);
            switchTimeTravelMode();
        });
}


function updateTimetravelSecond(s) {
    travelModeSecond = s;
    if (s < 10) s = `0${s}`;
    document.getElementById("timetravelCurrentSecond").textContent = s;
    const percent = (s / 60) * 100;
    document.documentElement.style.setProperty("--perf-timetravel-progress", `${percent}%`);
}

function dumpNumberFromMinute(m) {
    return (travelModeCluster * 60) + m;
}

function updateTimetravelMinute(m) {
    travelModeMinute = m;
    if (m < 10) m = `0${m}`;
    document.getElementById("timetravelCurrentMinute").textContent = m;
}

function previousTimetravelMinute() {
    if (travelModeMinute > 0) {
        updateTimetravelMinute(--travelModeMinute);
        updateTimetravelSecond(0);
    }
}

function nextTimetravelMinute() {
    if (travelModeMinute < 60) {
        updateTimetravelMinute(++travelModeMinute);
        updateTimetravelSecond(0);
    } 
}

function timetravelTick() {
    if (REALTIME_MODE) return resetTicker();

    if (travelModeSecond == 60) {
        if (travelModeMinute == 59) return resetTicker();

        updateTimetravelSecond(0);
        updateTimetravelMinute(travelModeMinute + 1);
    }

    const currentDumpNumber = dumpNumberFromMinute(travelModeMinute);
    const currentDump = travelModeDumps[currentDumpNumber];

    // Skip not registered dumps.
    if (currentDump === undefined || Object.keys(currentDump).length == 0) {
        for (testMinute = travelModeMinute; testMinute < 60; testMinute++) {
            let testDump = travelModeDumps[dumpNumberFromMinute(testMinute)];
            if (testDump !== undefined && Object.keys(testDump).length > 0) {
                updateTimetravelSecond(0);
                updateTimetravelMinute(testMinute);
                return;
            }
        }

        console.warn("No more data to time travel to.");
        resetTicker();
    }

    // Apply dump's value based on current second.
    Object.entries(currentDump).forEach(
        ([id, values]) => {
            const approxValueIndex = Math.min(Math.round((travelModeSecond / 60) * values.length), values.length - 1);
            const value = values[approxValueIndex];

            const element = document.getElementById(id);
            if (element === null) updateChart(id, value);
            else document.getElementById(id).textContent = value;
        }
    )

    updateTimetravelSecond(++travelModeSecond);
}

