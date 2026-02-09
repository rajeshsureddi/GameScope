# GameScope

**GameScope** is a showcase of gaming video samples for visual quality assessment, featuring **PS5** (high-fidelity) and **UGC** (user-generated) content with multiple resolutions, codecs, and quality levels.

- **Repo:** https://github.com/rajeshsureddi/GameScope  
- **Live site:** https://rajeshsureddi.github.io/GameScope/

---

## Features

- **Video gallery** — Browse samples with filters by platform (PS5 / UGC), clarity, and artifacts
- **Data distribution** — Plot of clip counts by resolution
- **Metadata** — MOS, resolution, framerate, and quality attributes per sample
- **Responsive** — Works on desktop and mobile

---

## GitHub Pages setup

1. **Create a new repository** on GitHub named `GameScope` (or any name; the URL will be `https://<username>.github.io/<repo-name>/`).

2. **Push this folder** so that the **contents** of `gamescope_website` are at the **root** of the repo:
   ```bash
   cd /mnt/LIVELAB_NAS/rajesh/New_Gaming/gamescope_website
   git init
   git add .
   git commit -m "GameScope showcase"
   git remote add origin https://github.com/rajeshsureddi/GameScope.git
   git branch -M main
   git push -u origin main
   ```

3. **Enable GitHub Pages**
   - Repo → **Settings** → **Pages**
   - **Source**: Deploy from a branch
   - **Branch**: `main` (or `master`) → `/ (root)` → Save

4. After a minute or two, the site will be at:
   - **https://rajeshsureddi.github.io/GameScope/**

---

## Repository structure

```
GameScope/
├── index.html      # Main page
├── styles.css      # Styles
├── script.js       # Gallery logic
├── data.json       # Video metadata (paths, MOS, clarity, etc.)
├── images/
│   └── plot.png    # Distribution plot
├── videos/
│   ├── ps5/        # PS5 samples
│   └── ugc/        # UGC samples
├── .nojekyll       # So GitHub Pages doesn’t use Jekyll
└── README.md
```

Videos and `data.json` use **relative paths**, so they work on GitHub Pages without changes.
