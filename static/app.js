document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('report-form');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const generateBtn = document.getElementById('generate-btn');
    const steps = document.querySelectorAll('.form-step');
    const indicators = document.querySelectorAll('.step');
    const loader = document.getElementById('loader');
    const resultSection = document.getElementById('result-section');
    const formSection = document.getElementById('form-section');
    const reportPreview = document.getElementById('report-preview');
    const downloadBtn = document.getElementById('download-btn');
    
    let currentStep = 0;
    let generatedContent = "";

    // Load saved API Key from localStorage
    const savedKey = localStorage.getItem('spp_api_key');
    if (savedKey) {
        document.getElementById('api_key').value = savedKey;
    }

    const updateStepper = () => {
        steps.forEach((step, idx) => {
            step.classList.toggle('active', idx === currentStep);
        });
        indicators.forEach((ind, idx) => {
            ind.classList.toggle('active', idx === currentStep);
        });

        prevBtn.hidden = currentStep === 0;
        nextBtn.hidden = currentStep === steps.length - 1;
        generateBtn.hidden = currentStep !== steps.length - 1;
    };

    nextBtn.addEventListener('click', () => {
        if (currentStep < steps.length - 1) {
            currentStep++;
            updateStepper();
        }
    });

    prevBtn.addEventListener('click', () => {
        if (currentStep > 0) {
            currentStep--;
            updateStepper();
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Save API Key
        localStorage.setItem('spp_api_key', data.api_key);

        const projectData = {};
        // Map all fields except the config ones
        for (let key in data) {
            if (!['api_key', 'provider', 'model'].includes(key)) {
                projectData[key] = data[key];
            }
        }

        const requestPayload = {
            provider: data.provider,
            model: data.model,
            api_key: data.api_key,
            data: projectData
        };

        loader.hidden = false;

        try {
            const resp = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestPayload)
            });

            if (!resp.ok) throw new Error(await resp.text());

            const result = await resp.json();
            generatedContent = result.content;
            
            reportPreview.innerText = generatedContent;
            
            loader.hidden = true;
            formSection.hidden = true;
            resultSection.hidden = false;
            window.scrollTo(0, 0);

        } catch (err) {
            loader.hidden = true;
            alert('Error: ' + err.message);
        }
    });

    downloadBtn.addEventListener('click', async () => {
        try {
            const resp = await fetch('/api/export-docx', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: generatedContent })
            });

            if (!resp.ok) throw new Error('Export failed');

            const { file_id } = await resp.json();
            window.location.href = `/api/download/${file_id}`;

        } catch (err) {
            alert('Export Error: ' + err.message);
        }
    });

    document.getElementById('restart-btn').addEventListener('click', () => {
        resultSection.hidden = true;
        formSection.hidden = false;
        currentStep = 0;
        updateStepper();
    });
});
