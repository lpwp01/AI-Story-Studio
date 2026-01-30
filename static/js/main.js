/**
 * AI Creative Studio - Professional JS Logic (v4.0 - 2025)
 * Features: Video (with Voice Selection), Image Generation, & Gallery Publishing
 */

// Global state to track last generated file for the Publish Modal
let lastGeneratedFile = "";
let lastGeneratedType = ""; // 'photo' or 'video'

// --- 1. VIDEO GENERATION LOGIC ---
async function generateVideo() {
    const prompt = document.getElementById('prompt');
    const voiceSelect = document.getElementById('voiceSelect'); // Naya: Voice Dropdown
    const genBtn = document.getElementById('genBtn');
    const progressContainer = document.getElementById('progressContainer');
    const loaderFill = document.getElementById('loaderFill');
    const stepText = document.getElementById('stepText');
    const statusMsg = document.getElementById('statusMsg');
    const result = document.getElementById('result');
    const player = document.getElementById('videoPlayer');
    const downloadBtn = document.getElementById('downloadBtn');

    if (!prompt.value || prompt.value.trim().length < 10) {
        return alert("Please enter a longer story (at least 2 sentences)!");
    }

    // UI Reset
    genBtn.style.display = "none";
    progressContainer.style.display = "block";
    result.style.display = "none";
    loaderFill.style.width = "5%";

    const scenes = prompt.value.split('.').filter(s => s.trim().length > 5);
    const totalSteps = Math.min(scenes.length, 5);
    
    let currentStep = 0;
    stepText.innerText = `Step 0 / ${totalSteps}`;
    statusMsg.innerText = "Connecting to Neural Voice Servers...";

    // Progress Simulation
    const progressInterval = setInterval(() => {
        if (currentStep < totalSteps) {
            currentStep++;
            let percent = (currentStep / (totalSteps + 1)) * 100;
            loaderFill.style.width = percent + "%";
            stepText.innerText = `Step ${currentStep} / ${totalSteps}`;
            statusMsg.innerText = `Generating Visuals and Natural Voice for Scene ${currentStep}...`;
        }
    }, 15000);

    let formData = new FormData();
    formData.append('prompt', prompt.value);
    formData.append('voice', voiceSelect.value); // Naya: Selected voice bhej rahe hain

    try {
        const resp = await fetch('/generate-video', { method: 'POST', body: formData });
        const data = await resp.json();
        
        clearInterval(progressInterval);

        if (data.video_url) {
            loaderFill.style.width = "100%";
            stepText.innerText = "Finishing!";
            statusMsg.innerText = "Your cinematic movie is ready ✨";

            // Store for publishing
            lastGeneratedFile = data.video_url;
            lastGeneratedType = 'video';

            setTimeout(() => {
                progressContainer.style.display = "none";
                result.style.display = "block";
                
                player.src = data.video_url + "?t=" + new Date().getTime();
                
                // Update Download Link
                const filename = data.video_url.split('/').pop();
                if(downloadBtn) downloadBtn.href = `/download/${filename}`;
                
                player.play();
                genBtn.style.display = "inline-block";
            }, 1000); 
        } else {
            throw new Error(data.error || "Server failed");
        }
    } catch (err) {
        clearInterval(progressInterval);
        alert("Error: " + err.message);
        genBtn.style.display = "inline-block";
        progressContainer.style.display = "none";
    }
}

// --- 2. IMAGE GENERATION LOGIC ---
async function generateImage() {
    const prompt = document.getElementById('imgPrompt');
    const genBtn = document.getElementById('genImgBtn');
    const loader = document.getElementById('imgLoader');
    const resultDiv = document.getElementById('imageResult');
    const outputImg = document.getElementById('outputImg');
    const downloadBtn = document.getElementById('downloadImgBtn');

    if (!prompt.value) return alert("Please describe the image!");

    // UI Reset
    if(genBtn) genBtn.disabled = true;
    if(loader) loader.style.display = "block";
    if(resultDiv) resultDiv.style.display = "none";

    let formData = new FormData();
    formData.append('prompt', prompt.value);

    try {
        const resp = await fetch('/generate-image', { method: 'POST', body: formData });
        const data = await resp.json();

        if (data.image_url) {
            console.log("Image received: ", data.image_url);
            
            // Simple Logic: Direct source set karein
            const finalPath = data.image_url + "?t=" + new Date().getTime();
            outputImg.src = finalPath;

            // Wait logic ko hata kar seedha dikhayein
            // Kyunki logs dikha rahe hain ki browser ne image fetch kar li hai
            if(loader) loader.style.display = "none";
            if(resultDiv) resultDiv.style.display = "block";
            
            // Download link set karein
            if(downloadBtn) {
                const filename = data.image_url.split('/').pop();
                downloadBtn.href = `/download/${filename}`;
            }

            // Global variable update karein taaki Publish kaam kare
            lastGeneratedFile = data.image_url;
            lastGeneratedType = 'photo';

            if(genBtn) genBtn.disabled = false;

        } else {
            alert("API Error: " + data.error);
            if(loader) loader.style.display = "none";
            if(genBtn) genBtn.disabled = false;
        }
    } catch (err) {
        console.error("Fetch Error:", err);
        alert("Server connection failed!");
        if(loader) loader.style.display = "none";
        if(genBtn) genBtn.disabled = false;
    }
}
// --- 3. GALLERY PUBLISH LOGIC ---

function openPublishModal() {
    const modal = document.getElementById('publishModal');
    if (modal) modal.style.display = 'flex';
}

function closePublishModal() {
    const modal = document.getElementById('publishModal');
    if (modal) modal.style.display = 'none';
}

async function submitToGallery() {
    const title = document.getElementById('pubTitle').value;
    const desc = document.getElementById('pubDesc').value;
    const tags = document.getElementById('pubTags').value;
    const pubBtn = document.querySelector('.btn-confirm-publish');

    if (!title || !desc) {
        return alert("Please enter at least Title and Description!");
    }

    if (!lastGeneratedFile) {
        return alert("No file generated to publish!");
    }

    pubBtn.disabled = true;
    pubBtn.innerText = "Publishing...";

    let formData = new FormData();
    formData.append('type', lastGeneratedType);
    formData.append('title', title);
    formData.append('description', desc);
    formData.append('tags', tags);
    formData.append('file_url', lastGeneratedFile);

    try {
        const resp = await fetch('/publish', { method: 'POST', body: formData });
        const data = await resp.json();

        if (data.success) {
            alert("Success! Your " + lastGeneratedType + " is now live in the Public Gallery. ✨");
            closePublishModal();
        } else {
            alert("Publishing failed: " + data.error);
        }
    } catch (err) {
        alert("Server Error while publishing!");
    } finally {
        pubBtn.disabled = false;
        pubBtn.innerText = "Publish Now ✨";
    }
}

// --- 4. UI ENHANCEMENTS ---

// Navbar link active effects
document.querySelectorAll('.nav-links a, .dropbtn').forEach(link => {
    link.addEventListener('mouseenter', () => {
        link.style.transform = "scale(1.05)";
    });
    link.addEventListener('mouseleave', () => {
        link.style.transform = "scale(1)";
    });
});

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById('publishModal');
    if (event.target == modal) {
        closePublishModal();
    }
}
