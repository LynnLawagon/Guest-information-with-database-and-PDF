//Const
const toggleBtn = document.getElementById("toggle-btn");
const inputFile = document.getElementById("input-file");
const previewImg = document.getElementById("preview-img");
const camera = document.getElementById("camera");
const snapBtn = document.getElementById("snap-btn");
const dropText = document.getElementById("drop-text");
const loading = document.getElementById("loading-indicator");

const idTypeInput = document.getElementById("id-type");
const firstNameInput = document.getElementById("first-name");
const middleNameInput = document.getElementById("middle-name");
const lastNameInput = document.getElementById("last-name");
const dobInput = document.getElementById("dob");
const genderInput = document.getElementById("gender");
const contactInput = document.getElementById("contact");
const addressInput = document.getElementById("address");

let cameraActive = false, stream = null, currentImgPath = "";
let tmModel, maxPredictions;

// Load TM model
async function loadTMModel() {
    const URL = "/static/my_model/";
    tmModel = await tmImage.load(URL + "model.json", URL + "metadata.json");
    maxPredictions = tmModel.getTotalClasses();
    console.log("TM model loaded");
}
loadTMModel();

// Predict ID type using TM
async function predictIDType(img) {
    if (!tmModel) return "";
    const prediction = await tmModel.predict(img);
    return prediction.reduce((a, b) => a.probability > b.probability ? a : b, {probability:0}).className;
}

// Update form fields
function updateFields(data, imgSrc){
    firstNameInput.value = data.First_name || "";
    middleNameInput.value = data.Middle_name || "";
    lastNameInput.value = data.Last_name || "";
    dobInput.value = data.Date_of_birth || "";
    genderInput.value = data.Gender || "";
    contactInput.value = data.Contact || "";
    addressInput.value = data.Address || "";
    idTypeInput.value = data.ID_type || "";
    currentImgPath = data.Img_path || "";
    previewImg.src = imgSrc;
    previewImg.style.display = "block";
    camera.style.display = "none";
    snapBtn.style.display = "none";
    dropText.textContent = "Upload your ID here";
    toggleBtn.textContent = "Use Camera";
    stopCamera();
    cameraActive = false;
}

//file upload
inputFile.addEventListener("change", async () => {
    const file = inputFile.files[0];
    if (!file) return;
    loading.style.display = "flex";

    const img = new Image();
    img.src = URL.createObjectURL(file);
    img.onload = async () => {
        try {
            const idType = await predictIDType(img);
            const formData = new FormData();
            formData.append("file", file);
            const res = await fetch("/upload", { method:"POST", body: formData });
            const data = await res.json();
            data.ID_type = idType;
            updateFields(data, img.src);
        } catch(err) {
            alert("Error scanning upload: " + err);
        } finally {
            loading.style.display = "none";
        }
    };
});

//camera snap
snapBtn.addEventListener("click", async () => {
    if (!camera.videoWidth || !camera.videoHeight) {
        alert("Camera not ready yet");
        return;
    }
    loading.style.display = "flex";

    const canvas = document.createElement("canvas");
    canvas.width = camera.videoWidth;
    canvas.height = camera.videoHeight;
    canvas.getContext("2d").drawImage(camera, 0, 0, canvas.width, canvas.height);
    const dataURL = canvas.toDataURL("image/png");

    const img = new Image();
    img.src = dataURL;
    img.onload = async () => {
        try {
            const idType = await predictIDType(img);
            const res = await fetch("/scan", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({image: dataURL})
            });
            const data = await res.json();
            data.ID_type = idType;
            updateFields(data, dataURL);
        } catch(err) {
            alert("Error scanning snap: " + err);
        } finally {
            loading.style.display = "none";
        }
    };
});

// Toggle camera
toggleBtn.addEventListener("click", () => {
    cameraActive = !cameraActive;
    if(cameraActive){
        previewImg.style.display = "none";
        camera.style.display = "block";
        snapBtn.style.display = "block";
        dropText.textContent = "Point your ID to the camera";
        toggleBtn.textContent = "Use Upload";
        startCamera();
    } else {
        previewImg.style.display = "block";
        camera.style.display = "none";
        snapBtn.style.display = "none";
        dropText.textContent = "Upload your ID here";
        toggleBtn.textContent = "Use Camera";
        stopCamera();
    }
});

// Start camera
function startCamera(){
    navigator.mediaDevices.getUserMedia({video:true})
        .then(s => {
            stream = s;
            camera.srcObject = s;
            camera.play();
        })
        .catch(err => alert("Camera error: " + err));
}

// Stop camera
function stopCamera(){
    if(stream){
        stream.getTracks().forEach(t => t.stop());
        camera.srcObject = null;
    }
}

//Preview click to upload
previewImg.parentElement.addEventListener("click", () => {
    if(!cameraActive) inputFile.click();
});

// Save form
document.getElementById("save-btn").addEventListener("click", async () => {
    const payload = {
        ID_type: idTypeInput.value,
        First_name: firstNameInput.value,
        Middle_name: middleNameInput.value,
        Last_name: lastNameInput.value,
        Date_of_birth: dobInput.value,
        Gender: genderInput.value,
        Contact: contactInput.value,
        Address: addressInput.value,
        Img_path: currentImgPath
    };
    const res = await fetch("/save_guest", { 
        method: "POST", 
        headers: {"Content-Type":"application/json"}, 
        body: JSON.stringify(payload) 
    });
    const data = await res.json();
    alert(data.status === "success" ? "Guest saved!" : "Failed to save guest");
});