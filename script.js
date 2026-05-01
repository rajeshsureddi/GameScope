document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const videoGrid = document.getElementById('video-grid');
    const claritySelect = document.getElementById('clarity-select');
    const artifactsSelect = document.getElementById('artifacts-select');
    const immersionSelect = document.getElementById('immersion-select');
    const platformBtns = document.querySelectorAll('#platform-filters .toggle-btn');
    const metadataVisualizationGrid = document.getElementById('metadata-visualization-grid');
    const metadataFileLinks = document.getElementById('metadata-file-links');

    // State
    let allVideos = [];
    let filters = { platform: 'all', clarity: 'all', artifacts: 'all', immersion: 'all' };

    const metadataImagePaths = [
        {
            path: 'images/good_results_visualizations/score_distribution_overall.png',
            caption: 'Figure 1: Overall MOS score distribution across all 4,048 GamingVQA clips, showing the frequency of perceptual quality ratings from crowdsourced subjective evaluations.'
        },
        {
            path: 'images/good_results_visualizations/score_distribution_train_vs_test.png',
            caption: 'Figure 2: MOS score distributions for the GamingVQA training and test splits, demonstrating balanced quality coverage across both subsets.'
        }
    ];

    const metadataOtherFiles = [];

    // Fetch Data
    fetch('data.json')
        .then(res => res.json())
        .then(data => {
            allVideos = data;
            initializeFilters(data);
            renderVideos(data);
            renderMetadataVisualizations();
        })
        .catch(err => {
            console.error('Failed to load data.json', err);
            videoGrid.innerHTML = `<div class="error-state">Failed to load dataset. JSON not found.</div>`;
            renderMetadataVisualizations();
        });

    function initializeFilters(data) {
        // Unique Clarities
        const clarities = [...new Set(data.map(d => d.most_common_clarity))].sort();
        clarities.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c;
            opt.textContent = c;
            claritySelect.appendChild(opt);
        });

        // Unique Artifacts
        const artifacts = [...new Set(data.map(d => d.most_common_artifacts))].sort();
        artifacts.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a;
            opt.textContent = a;
            artifactsSelect.appendChild(opt);
        });

        // Unique Immersion levels
        const immersionOrder = ['Low level of immersion', 'Moderate level of immersion', 'High level of immersion'];
        const immersions = [...new Set(data.map(d => d.most_common_immersion))]
            .sort((a, b) => immersionOrder.indexOf(a) - immersionOrder.indexOf(b));
        immersions.forEach(i => {
            const opt = document.createElement('option');
            opt.value = i;
            opt.textContent = i;
            immersionSelect.appendChild(opt);
        });
    }

    // Toggle Button Logic
    platformBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            platformBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filters.platform = btn.dataset.filter;
            applyFilters();
        });
    });

    // Select Logic
    claritySelect.addEventListener('change', (e) => {
        filters.clarity = e.target.value;
        applyFilters();
    });

    artifactsSelect.addEventListener('change', (e) => {
        filters.artifacts = e.target.value;
        applyFilters();
    });

    immersionSelect.addEventListener('change', (e) => {
        filters.immersion = e.target.value;
        applyFilters();
    });

    function applyFilters() {
        const filtered = allVideos.filter(v => {
            if (filters.platform !== 'all' && v.user_type !== filters.platform) return false;
            if (filters.clarity !== 'all' && v.most_common_clarity !== filters.clarity) return false;
            if (filters.artifacts !== 'all' && v.most_common_artifacts !== filters.artifacts) return false;
            if (filters.immersion !== 'all' && v.most_common_immersion !== filters.immersion) return false;
            return true;
        });
        renderVideos(filtered);
    }

    function renderVideos(videos) {
        if (videos.length === 0) {
            videoGrid.innerHTML = `<div class="empty-state">No videos match the selected filters.</div>`;
            return;
        }

        videoGrid.innerHTML = videos.map(v => {
            // Platform badge
            const platformClass = v.user_type === 'ps5' ? 'tag ps5' : 'tag ugc';
            const platformLabel = v.user_type.toUpperCase();

            // Format metrics
            const mos = parseFloat(v.MOS).toFixed(2);

            return `
            <div class="video-card">
                <div class="video-player-wrapper">
                    <video controls preload="metadata" muted>
                        <source src="${v.relative_path}" type="video/mp4">
                    </video>
                </div>
                <div class="card-info">
                    <div class="card-tags">
                        <span class="${platformClass}">${platformLabel}</span>
                        <span class="tag meta">${v.most_common_clarity}</span>
                        <span class="tag meta">${v.most_common_artifacts}</span>
                        <span class="tag meta">${v.most_common_immersion}</span>
                    </div>
                    <div class="card-title" title="${v.File.split('/').pop()}">${v.content_type || 'Unknown Content'}</div>
                    <div class="card-metrics">
                        <span class="metric" title="MOS Score"><i class="fa-solid fa-star"></i> MOS: ${mos}</span>
                        <span class="metric" title="Resolution"><i class="fa-solid fa-expand"></i> ${v.width}x${v.height}</span>
                        <span class="metric" title="Framerate"><i class="fa-solid fa-clock"></i> ${v.framerate} fps</span>
                        <span class="metric" title="Total Frames"><i class="fa-solid fa-film"></i> ${v.nb_frames}</span>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }

    function renderMetadataVisualizations() {
        if (metadataVisualizationGrid) {
            metadataVisualizationGrid.innerHTML = metadataImagePaths.map(({ path, caption }) => {
                const figLabel = caption.match(/^(Figure \d+)/)[1];
                return `
                    <article class="viz-card">
                        <a href="${path}" target="_blank" rel="noopener">
                            <img src="${path}" alt="${figLabel}" loading="lazy">
                        </a>
                        <div class="viz-card-body">
                            <p class="viz-card-caption">${caption}</p>
                        </div>
                    </article>
                `;
            }).join('');
        }

        if (metadataFileLinks) {
            metadataFileLinks.innerHTML = metadataOtherFiles.map(path => {
                const fileName = path.split('/').pop();
                return `<a class="metadata-file-link" href="${path}" target="_blank" rel="noopener">${fileName}</a>`;
            }).join('');
        }
    }

    // Auto-pause others when one plays
    document.addEventListener('play', function (e) {
        var videos = document.getElementsByTagName('video');
        for (var i = 0, len = videos.length; i < len; i++) {
            if (videos[i] != e.target) {
                videos[i].pause();
            }
        }
    }, true);
});
