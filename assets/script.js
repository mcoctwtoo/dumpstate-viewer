var jsonObj = {};
// var fetchedData = {};
var jsonViewer = new JSONViewer();

document.querySelector("#json").appendChild(jsonViewer.getContainer());

var loadJsonBtn = document.querySelector("button.load-json");
var collapseBtn = document.querySelector("button.collapse");
var expandBtn = document.querySelector("button.expand");
var searchBtn = document.querySelector("input#search");

loadJsonBtn.addEventListener("click", async function () {
  jsonObj = await fetchDataAsync();
  jsonViewer.showJSON(jsonObj);
});

collapseBtn.addEventListener("click", function () {
  jsonViewer.showJSON(jsonObj, null, 1);
});

expandBtn.addEventListener("click", function () {
  jsonViewer.showJSON(jsonObj);
});

searchBtn.addEventListener('keyup', function(e) {
  if (e.keyCode === 13) {
    result = filterResult(searchBtn.value, jsonObj);
    jsonViewer.showJSON(result);
    return false;
  }
});

async function fetchDataAsync() {
  // fetchedData = {};
  try {
    const response = await fetch('http://127.0.0.1:5500/output.json');
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    const data = await response.json();
    // console.log("data");
    // fetchedData = data;
    return data;

  } catch (error) {
    console.error('There was a problem with your fetch operation:', error);
    return {}
  }
}



function chunkArray(array, size) {
  const result = [];
  for (let i = 0; i < array.length; i += size) {
    const chunk = array.slice(i, i + size);
    result.push(chunk);
  }

  return result;
}


function filterResult (val, obj) {
  val = val.toLowerCase();
  result = {}

  match = {}
  totalMatch = 0;

  if ("noOfDevices" in obj)
    result["noOfDevices"] = obj["noOfDevices"];
  if ("devices" in obj)
    result["devices"] = {}

  Object.keys(obj["devices"]).forEach(deviceId => {
    match[deviceId] = 0;
    if ("devices" in obj)
      result["devices"][deviceId] = {}

    if ("characteristics" in obj.devices[deviceId])
      result.devices[deviceId]["characteristics"] = {}

    let xx = result.devices[deviceId]["characteristics"]

    Object.keys(obj.devices[deviceId]["characteristics"]).forEach(c => {
      cl = c.toLowerCase();
      cobj = obj.devices[deviceId]["characteristics"][c];

      keyIndex = cl.indexOf(val) >= 0;
      valueIndex = false;
      if (typeof cobj == typeof val) {
        valueIndex = cobj.indexOf(val) >= 0;
      }


      //  todo - handle physical camera..

      if (keyIndex) {   // search in key...
        match[deviceId]++;
        totalMatch++;
        xx[c] = cobj;
      } else if (valueIndex) {  // search single value
        match[deviceId]++;
        totalMatch++;
        xx[c] = cobj;
      } else if (typeof cobj == typeof {} && "values" in cobj) {  // search in values []
        for (cv in cobj.values) {
          if (cv.toLowerCase().indexOf(val) >= 0 ) {
            match[deviceId]++;
            totalMatch++;
            xx[c] = cobj.values;
            continue;
          }
        }
      }
    })
  });

  console.log("returning...", match, totalMatch);


  return result;

}