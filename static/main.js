// Initialize Particles.js background
particlesJS("particles-js", {
    "particles": {
      "number": { "value": 80, "density": { "enable": true, "value_area": 800 } },
      "color": { "value": "#00f3ff" },
      "shape": { "type": "circle" },
      "opacity": { "value": 0.5, "random": true, "anim": { "enable": true, "speed": 1, "opacity_min": 0.1, "sync": false } },
      "size": { "value": 3, "random": true, "anim": { "enable": true, "speed": 2, "size_min": 0.1, "sync": false } },
      "line_linked": { "enable": true, "distance": 150, "color": "#00f3ff", "opacity": 0.2, "width": 1 },
      "move": { "enable": true, "speed": 1, "direction": "none", "random": true, "straight": false, "out_mode": "out", "bounce": false }
    },
    "interactivity": {
      "detect_on": "canvas",
      "events": { "onhover": { "enable": true, "mode": "grab" }, "onclick": { "enable": true, "mode": "push" }, "resize": true },
      "modes": { "grab": { "distance": 140, "line_linked": { "opacity": 0.5 } } }
    },
    "retina_detect": true
  });
  
  // State
  let currentWorldId = null;
  let autoRunInterval = null;
  
  // DOM Elements
  const setupView = document.getElementById('setup-view');
  const dashboardView = document.getElementById('dashboard-view');
  const seedInput = document.getElementById('seed-input');
  const dropZone = document.getElementById('drop-zone');
  const fileUpload = document.getElementById('file-upload');
  
  // File Upload Handlers
  if (dropZone && fileUpload) {
      dropZone.addEventListener('click', (e) => {
          if (e.target.id !== 'seed-input') {
              fileUpload.click();
          }
      });
      
      fileUpload.addEventListener('change', (e) => {
          if (e.target.files.length > 0) uploadFile(e.target.files[0]);
      });
      
      dropZone.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropZone.classList.add('drag-over');
      });
      
      dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
      
      dropZone.addEventListener('drop', (e) => {
          e.preventDefault();
          dropZone.classList.remove('drag-over');
          if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
      });
  }
  
  async function uploadFile(file) {
      const validExtensions = ['pdf', 'txt', 'md'];
      const ext = file.name.split('.').pop().toLowerCase();
      if (!validExtensions.includes(ext)) {
          alert("Unsupported file format. Please upload PDF, MD, or TXT.");
          return;
      }
      
      seedInput.value = "Extracting reality seed from document...";
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
          const res = await fetch('/api/world/parse_file', {
              method: 'POST',
              body: formData
          });
          
          if (!res.ok) throw new Error("Failed to parse file.");
          
          const data = await res.json();
          seedInput.value = data.parsed_text;
      } catch (err) {
          console.error(err);
          seedInput.value = "Error parsing document. Please try again or paste text manually.";
      }
  }
  
  const valEpoch = document.getElementById('val-epoch');
  const valPopulation = document.getElementById('val-population');
  const valStability = document.getElementById('val-stability');
  const valTech = document.getElementById('val-tech');
  const worldIdDisplay = document.getElementById('world-id-display');
  
  const cohortsList = document.getElementById('cohorts-list');
  const eventLog = document.getElementById('event-log');
  
  const btnSpawn = document.getElementById('btn-spawn');
  const btnEpoch1 = document.getElementById('btn-epoch-1');
  const btnEpoch10 = document.getElementById('btn-epoch-10');
  const btnAuto = document.getElementById('btn-auto');
  
  // Handlers
  btnSpawn.addEventListener('click', async () => {
      const text = seedInput.value.trim();
      let seedText = text || "A highly advanced cybernetic society plagued by scarcity.";
      
      btnSpawn.innerHTML = '<span class="btn-text">INITIALIZING...</span>';
      
      try {
          const res = await fetch('/api/world/spawn', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ seed_text: seedText })
          });
          const data = await res.json();
          currentWorldId = data.world_id;
          
          updateDashboard(data);
          
          setupView.classList.remove('active');
          setTimeout(() => {
              setupView.classList.add('hidden');
              dashboardView.classList.remove('hidden');
              dashboardView.classList.add('active');
              worldIdDisplay.innerText = currentWorldId.split('-')[0].toUpperCase();
          }, 500);
      } catch (err) {
          console.error(err);
          btnSpawn.innerHTML = '<span class="btn-text">ERROR: SPAWN FAILED</span>';
      }
  });
  
  btnEpoch1.addEventListener('click', () => advanceEpoch(1));
  btnEpoch10.addEventListener('click', () => advanceEpoch(10));
  
  btnAuto.addEventListener('click', () => {
      if (autoRunInterval) {
          clearInterval(autoRunInterval);
          autoRunInterval = null;
          btnAuto.innerText = "AUTO-RUN";
          btnAuto.classList.remove('active');
      } else {
          autoRunInterval = setInterval(() => advanceEpoch(1), 1500);
          btnAuto.innerText = "HALT";
          btnAuto.classList.add('active');
      }
  });
  
  async function advanceEpoch(steps) {
      if(!currentWorldId) return;
      try {
          const res = await fetch('/api/world/advance', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ world_id: currentWorldId, steps: steps })
          });
          const data = await res.json();
          updateDashboard(data);
      } catch (err) {
          console.error(err);
      }
  }
  
  function formatNumber(num) {
      if(num >= 1000000) return (num/1000000).toFixed(2) + 'M';
      if(num >= 1000) return (num/1000).toFixed(1) + 'K';
      return num;
  }
  
  function updateDashboard(data) {
      valEpoch.innerText = data.epoch;
      
      // Animate population change
      const currentPop = valPopulation.innerText;
      valPopulation.innerText = formatNumber(data.population);
      
      valStability.innerText = Math.round(data.stability * 100) + '%';
      valTech.innerText = data.tech_level.toFixed(2);
      
      // Update Cohorts
      cohortsList.innerHTML = data.cohorts.map(c => `
          <div class="cohort-item">
              <h4>${c.name}</h4>
              <p>Pop: ${formatNumber(c.population)}</p>
              ${Object.entries(c.traits).map(([trait, val]) => `
                  <div style="font-size:0.8rem; margin-top:5px; color:#8892b0;">${trait}: ${val.toFixed(2)}</div>
                  <div class="trait-bar"><div class="trait-fill" style="width: ${val*100}%; background: ${val > 0.7 ? 'var(--magenta)' : 'var(--cyan)'}"></div></div>
              `).join('')}
          </div>
      `).join('');
      
      // Update Events
      const newEventsHTML = data.recent_events.map(ev => {
          let badgeClass = 'impact-neutral';
          if(ev.impact > 0) badgeClass = 'impact-pos';
          else if (ev.impact < 0) badgeClass = 'impact-neg';
          
          return `
          <div class="event-item">
              <div class="event-time">EP ${ev.epoch}</div>
              <div class="event-body">
                  <span class="impact-badge ${badgeClass}">${ev.type.toUpperCase()}</span>
                  <p>${ev.message}</p>
              </div>
          </div>
          `;
      }).join('');
      
      eventLog.innerHTML = newEventsHTML;
      // Scroll to bottom
      eventLog.scrollTop = eventLog.scrollHeight;
  }
