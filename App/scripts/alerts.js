const noNotificationsAlert = document.getElementById("noNotificationsAlert");
const trackersContainer = document.getElementById("alertsContainer");
const trackersCounter = document.getElementById("alertsCount");
const trackersPerCategory = {};


function askNotificationPermission() {
    Notification.requestPermission().then((permission) => {
        if (permission == "granted") noNotificationsAlert.remove();
    });
}

function checkNotificationsPerms() {
    if (!("Notification" in window)) {
        return noNotificationsAlert.querySelector("span").textContent = "This browser does not support notifications.";
    } else if (Notification.permission === "granted") {
        noNotificationsAlert.remove();
    }
}

function sendNotification(title, text) {
    new Notification(title, { body: text });
}

function fetchTrackableMetrics() {
    const options = {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    };

    fetch(HTTP_PROTO + "://" + API_ADDRESS + "/trackers/get-trackable", options)
        .then(response => response.json())
        .then(trackable => {
            const selectEl = document.getElementById("alertStatementMetric");
            
            Array.from(selectEl.children).forEach(child => {
                if (child.getAttribute("value") != "0") child.remove();
            })

            Object.entries(trackable).forEach(
                ([category, items]) => {
                    const categoryGroup = document.createElement("optgroup");
                    categoryGroup.label = category.toUpperCase();

                    items.forEach(item => {
                        const itemOption = document.createElement("option");
                        itemOption.value = category + "|" + item[0] + "|" + item[1];
                        itemOption.textContent = item[1];
                        categoryGroup.appendChild(itemOption);
                    })

                    selectEl.appendChild(categoryGroup);
                }
            )
        })
        .catch(error => {
            console.error('Error while fetching trackable metrics', error);
        });
}


function createNewTracker() {
    const errorLabel = document.getElementById("alertCreationError");
    const metricSelect = document.getElementById("alertStatementMetric");
    const metricValue = parseFloat(document.getElementById("alertStatementValue").value);
    const statementOp = (document.getElementById("alertCreationOpLt").checked) ? "<" : ">";
    
    if (metricSelect.value == "0") {
        errorLabel.textContent = "Select a metric to track.";
        return;
    }
    
    if (isNaN(metricValue)) {
        errorLabel.textContent = "Invalid limit value";
        return;
    }

    let [category, id, name] = metricSelect.value.split("|");
    category = category.toUpperCase();

    const options = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            trackedId: id,
            stmtOp: statementOp,
            limitValue: metricValue
        })
    };

    fetch(HTTP_PROTO + "://" + API_ADDRESS + "/trackers/create", options)
        .then(response => response.json())
        .then(result => {
            if (!result.status) {
                errorLabel.textContent = result.err_msg;
            } else {
                errorLabel.textContent = "";
                const triggerStmt = `${statementOp} ${metricValue} for a minute`;
                buildMetricTrackerEntry(id, category, name, triggerStmt);
                document.getElementById("alertStatementMetric").value = "0";
                document.getElementById("alertStatementValue").value = "";
            }
        })
        .catch(error => {
            console.error('Error while sending tracker create request', error);
        });
}

function sendRemoveTracker(trackedId) {
    _sendMessageToServer(EV_REMOVE_TRACKER, trackedId);
    document.getElementById(`tracker-container-${trackedId}`).remove();
    trackersCounter.textContent = parseInt(trackersCounter.textContent) - 1;
}

function buildMetricTrackerEntry(trackedId, category, name, triggerStmt) {
    category = category.toUpperCase();
   
    // If performance-copmosition has been received and initialized, categoryColors contain correct color.
    const initColor = (category in categoryColors) ? categoryColors[category] : "orange";
    const style = `--category-color: ${initColor}`;

    const trackedEl = document.getElementById(trackedId);
    const initValue = (trackedEl) ? trackedEl.textContent : "?";

    const elementId = `tracker-container-${trackedId}`;
    const entry = `
        <div class="trackedMetric" style="${style}" id="${elementId}">
            <div class="trackedMetricHeader">
                <span class="trackedMetricCategory">${category}</span>
                <span class="trackedMetricTitle">${name}</span>
                <i class="trackedMetricRemove fa-solid fa-eye-slash" onclick="sendRemoveTracker('${trackedId}')"></i>
            </div>
            <span class="trackedMetricCurrentValue" id="tracker-${trackedId}">${initValue}</span>
            <span class="trackedMetricTrigger">${triggerStmt}</span>
        </div>
    `;

    trackersContainer.innerHTML += entry;
    trackersCounter.textContent = parseInt(trackersCounter.textContent) + 1;
    if (category in trackersPerCategory) trackersPerCategory[category].push(elementId);
    else trackersPerCategory[category] = [elementId];
}

function fetchActiveTrackers() {
    const options = {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    };
    
    fetch(HTTP_PROTO + "://" + API_ADDRESS + "/trackers/get-active-trackers", options)
        .then(response => response.json())
        .then(tracked => {
            tracked.forEach(
                (trackerData) => {
                    buildMetricTrackerEntry(trackerData.trackedId, trackerData.category, trackerData.trackedName, trackerData.triggerStmt);
                }
            )
        })
        .catch(error => {
            console.error('Error while fetching trackable metrics', error);
        });
}

function trackerColor(ratio) {
    const color1 = [240, 144, 144];
    const color2 = [192, 237, 183];
    var w1 = ratio;
    var w2 = 1 - w1;
    const r = Math.round(color1[0] * w1 + color2[0] * w2);
    const g = Math.round(color1[1] * w1 + color2[1] * w2);
    const b = Math.round(color1[2] * w1 + color2[2] * w2);
    return `rgb(${r},${g},${b})`;
}

function handleTrackersUpdatePacket(updates) {
    Object.entries(updates).forEach(
        ([trackerId, approxData]) => {
            let {value, ratio} = approxData;

            let color = "red";
            if (ratio < 1) color = trackerColor(ratio) ;
            
            
            const trackerEl = document.getElementById(`tracker-${trackerId}`);
            if (trackerEl) {
                trackerEl.textContent = value;
                trackerEl.style = `color: ${color}`;

            }
        }
    )
}

checkNotificationsPerms();
