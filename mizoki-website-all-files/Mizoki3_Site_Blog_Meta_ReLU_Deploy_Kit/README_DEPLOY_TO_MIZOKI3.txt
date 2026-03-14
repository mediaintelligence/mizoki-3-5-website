MIZOKI3.COM BLOG DEPLOY KIT — META ReLU POST
==================================================

This kit is structured to match the current mizoki3.com production site, which serves assets from:
- /assets/img/  (images)
- /assets/pdf/  (PDFs)

WHAT'S INCLUDED
---------------
1) Static blog pages (ready to drop into the site):
   - /blog/index.html
   - /blog/meta-relu-gate-go-deep-before-wide/index.html

2) Blog images (drop into your existing assets folder):
   - /assets/img/blog/meta-relu/01_relu_gate.png
   - /assets/img/blog/meta-relu/02_nonlinear_activation_curve.png
   - /assets/img/blog/meta-relu/03_learning_50_events.png
   - /assets/img/blog/meta-relu/04_compounding_feedback_loop.png
   - /assets/img/blog/meta-relu/05_budget_dilution_vs_concentration.png

3) LinkedIn/Open Graph preview image (correct 1.91:1 ratio):
   - /assets/img/blog/meta-relu/og_meta_relu_1200x627.png

4) Source Markdown (optional, for future generator):
   - /content/meta-relu-gate-go-deep-before-wide.md

DEPLOY STEPS (STATIC SITE)
--------------------------
A) Copy folders into your mizoki-site repo root (or the folder that deploys to mizoki3.com):
   - Copy: blog/            → (repo root)/blog/
   - Copy: assets/img/blog/ → (repo root)/assets/img/blog/

B) Add a “Blog” link to the top navigation across the site:
   - Add: <a href="/blog/">Blog</a>
   - Best practice: update your shared header template/partial if one exists.
     If nav is duplicated per page, update the following pages:
       /index.html (or home), /how-it-works.html, /platform.html, /security.html,
       /industries.html, /pricing.html, /case-studies.html, /resources.html, /roi-calculator.html

C) Confirm LinkedIn preview works:
   - The post page includes og:title / og:description / og:image / og:url
   - After deploy, run LinkedIn Post Inspector on:
     https://mizoki3.com/blog/meta-relu-gate-go-deep-before-wide/
   - If LinkedIn caches an old preview, Post Inspector will refresh it.

NOTES
-----
- The og:image is set to a 1200x627 image for best LinkedIn unfurl behavior.
- The embedded article images are 1200x675 and will render fine inside the post.
- If you already have a global CSS framework, you can remove the inline <style> blocks
  and instead apply your site styles to the /blog pages.

