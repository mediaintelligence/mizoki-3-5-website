/* ============================================
   MIZ OKI 3.5 — Application JavaScript
   ============================================ */

(function () {
  'use strict';

  // ---- BLOG DATA ----
  const blogPosts = [
    {
      id: 1,
      title: "Why Threshold-Aware Decision Intelligence Changes Everything",
      category: "Decision Intelligence",
      date: "March 10, 2026",
      author: "MIZ OKI Team",
      readTime: "6 min read",
      excerpt: "The shift from reactive analytics to proactive, governed execution is redefining how enterprises compete. Threshold-aware intelligence is the catalyst.",
      content: `
        <p>For decades, enterprise decision-making has followed the same pattern: collect data, build dashboards, review reports, then decide. The problem is obvious to anyone who has lived it — by the time the decision is made, the window has moved.</p>

        <h3>The Latency Tax</h3>
        <p>Decision latency is not just an inconvenience. It is a measurable cost. When pricing decisions take 14 days instead of 14 minutes, revenue leaks through every gap between signal and action. Our data across enterprise deployments shows this leakage ranges from 18% to 35% of addressable revenue — a staggering figure that most organizations have simply accepted as the cost of doing business.</p>

        <blockquote>"The gap between knowing and doing is where enterprise value goes to die."</blockquote>

        <h3>What Threshold-Awareness Actually Means</h3>
        <p>Threshold-aware decision intelligence replaces the reactive cycle with continuous, governed loops. The system does not wait for a human to notice a trend in a dashboard. Instead, it monitors signals against predefined thresholds — confidence levels, risk boundaries, margin floors — and acts when conditions are met.</p>

        <p>This is not automation in the traditional sense. Traditional automation follows static rules. Threshold-aware systems evaluate context, weigh alternatives, and select actions based on causal understanding. The threshold is not a trigger — it is a governance boundary that determines whether the system acts autonomously, escalates for approval, or remains advisory.</p>

        <h3>The Governance Imperative</h3>
        <p>Speed without governance is reckless. Every autonomous action within a threshold-aware system carries a full decision trace: what was sensed, how it was reasoned about, what alternatives were considered, and why this specific action was selected. This is not a nice-to-have — it is what makes autonomous decision intelligence defensible to boards, regulators, and operators.</p>

        <p>The enterprises adopting this paradigm are not replacing human judgment. They are freeing it. When the system handles the 89% of decisions that fall within well-understood parameters, human expertise is concentrated on the 11% that actually requires creativity, negotiation, and strategic thinking.</p>

        <h3>The Shift Is Already Happening</h3>
        <p>Organizations that have deployed threshold-aware decision loops report decision latency reductions of 50 to 75 times, with operational cost savings of 22% to 41%. The payback period averages 3.2 months. These are not theoretical projections — they are measured outcomes from governed, traceable deployments.</p>

        <p>The question is no longer whether this shift will happen. It is whether your organization will lead it or respond to competitors who did.</p>
      `
    },
    {
      id: 2,
      title: "The SRPVDAL Framework: A New Standard for Enterprise AI Governance",
      category: "Framework",
      date: "March 6, 2026",
      author: "MIZ OKI Team",
      readTime: "7 min read",
      excerpt: "A deep dive into the 7-stage cognitive pipeline that ensures every autonomous decision is verified, governed, and traceable.",
      content: `
        <p>Enterprise AI has a governance problem. Models make predictions, but the path from prediction to action remains opaque, ungoverned, and untraceable in most deployments. SRPVDAL — Sense, Reason, Plan, Verify, Decide, Act, Learn — was designed to solve this.</p>

        <h3>Why Seven Stages?</h3>
        <p>Most AI systems collapse the entire decision process into a single step: input goes in, output comes out. This is fundamentally incompatible with enterprise governance requirements. Boards need to know why a decision was made. Regulators need to see the reasoning path. Operators need to understand what alternatives were considered and rejected.</p>

        <p>SRPVDAL decomposes the decision process into seven discrete, auditable stages. Each stage has defined inputs, outputs, and governance controls. Each stage produces artifacts that form the complete decision trace.</p>

        <blockquote>"A decision without a trace is a liability. A decision with a trace is an asset."</blockquote>

        <h3>The Verification Layer</h3>
        <p>The VERIFY stage is what separates SRPVDAL from conventional AI pipelines. Before any plan reaches the DECIDE stage, it faces a Devil's Advocate review — a structured challenge process where counter-arguments are generated and evaluated. This is not a rubber stamp. The verification layer has been shown to catch 23% of plans that would have produced suboptimal outcomes.</p>

        <p>Knowledge Graph constraint validation adds a second verification dimension. Every proposed action is checked against organizational constraints, regulatory requirements, and historical patterns. Plans that violate constraints are flagged, modified, or rejected before they reach execution.</p>

        <h3>Learning That Actually Closes the Loop</h3>
        <p>The LEARN stage captures outcomes and feeds them back into the system. Credibility scores for individual agents are updated based on the accuracy of their contributions. The Knowledge Graph evolves with every decision cycle. This creates a system that genuinely improves from reality, not from theoretical retraining on static datasets.</p>

        <p>The learning velocity metric — improvement rate over time — becomes a leading indicator of system maturation. Organizations typically see a 15-20% improvement in decision quality within the first 90 days of deployment.</p>

        <h3>Implementing SRPVDAL</h3>
        <p>SRPVDAL is not a theoretical framework. It is an operational architecture that connects to existing enterprise systems through a plug-in layer. ERP, CRM, data warehouses, and cloud infrastructure connect at the SENSE stage. Actions execute through existing workflows at the ACT stage. No rip-and-replace required.</p>

        <p>The framework is designed to be incrementally adopted. Organizations typically start with advisory mode — the system runs the full loop but presents recommendations rather than executing. As confidence builds and governance policies mature, autonomy levels increase. The system grows with the organization's readiness.</p>
      `
    },
    {
      id: 3,
      title: "Autonomous Doesn't Mean Uncontrolled: The Case for Governed AI",
      category: "Governance",
      date: "March 2, 2026",
      author: "MIZ OKI Team",
      readTime: "5 min read",
      excerpt: "Enterprise AI autonomy and governance are not opposing forces. Here's why the best autonomous systems are also the most governed.",
      content: `
        <p>The word "autonomous" triggers alarm bells in enterprise boardrooms. It shouldn't. Properly governed autonomous systems are not only safer than manual decision-making — they are more accountable.</p>

        <h3>The Manual Decision Problem</h3>
        <p>Consider how most enterprise decisions are made today. A signal appears in a dashboard. Someone notices it — maybe days later. They email a colleague. A meeting is scheduled. A decision is made verbally. An action is taken. There is no trace of the reasoning, no record of alternatives considered, and no systematic learning from the outcome.</p>

        <p>This is the status quo that autonomous decision intelligence replaces. Every single decision in a governed autonomous system produces a complete, immutable trace. Every signal that was sensed, every reasoning path that was explored, every alternative that was considered and rejected, every confidence score, every risk assessment — all logged, all auditable.</p>

        <blockquote>"Autonomy without governance is unacceptable. Governance without autonomy is inefficient. The enterprise needs both."</blockquote>

        <h3>The Three Modes of Governance</h3>
        <p>Governed autonomous systems operate in three modes, configurable by policy: Advisory mode presents recommendations but takes no action. Approval mode executes actions only after explicit human authorization. Autonomous mode executes within defined thresholds without human intervention. The key insight is that these modes are not system-wide settings — they are configurable per decision type, per domain, per risk level.</p>

        <p>A pricing adjustment within a 3% margin might run autonomously. A supplier switch above $1M might require VP approval. A regulatory filing always goes through compliance review. The governance policy captures these nuances and enforces them consistently — something manual processes struggle to achieve.</p>

        <h3>The Override Metric</h3>
        <p>One of the most telling metrics in a governed autonomous system is override frequency — how often humans intervene, and why. This metric serves as a continuous calibration signal. High override rates in a specific domain suggest the system's thresholds need adjustment. Low override rates with positive outcomes confirm that governance boundaries are well-calibrated.</p>

        <p>Over time, the override metric becomes a powerful organizational learning tool. It reveals where human expertise adds the most value and where autonomous execution delivers consistent, traceable results. Organizations that track this metric systematically report significant improvements in both efficiency and decision quality within the first quarter of deployment.</p>

        <p>The future of enterprise AI is not a choice between human control and autonomous execution. It is the intelligent integration of both, governed by policies that evolve with organizational learning.</p>
      `
    },
    {
      id: 4,
      title: "From Dashboards to Decision Loops: The Next Enterprise Shift",
      category: "Strategy",
      date: "February 25, 2026",
      author: "MIZ OKI Team",
      readTime: "6 min read",
      excerpt: "Traditional BI tells you what happened. Decision loops tell you what to do — and do it. Why the dashboard era is ending.",
      content: `
        <p>Business intelligence promised to make organizations data-driven. It delivered dashboards. After two decades and trillions of dollars in BI investment, the fundamental question remains: who turns the insight into action, and how fast?</p>

        <h3>The Dashboard Bottleneck</h3>
        <p>Dashboards are observation tools. They excel at showing what happened and, with good analytics, what is happening. But they stop at the boundary of action. The gap between the dashboard and the decision is filled with meetings, emails, approvals, and institutional friction. This gap is where value evaporates.</p>

        <p>The average enterprise decision moves through 4.7 handoffs between insight and action. Each handoff introduces delay, interpretation drift, and information loss. By the time the action is taken, the conditions that triggered the original insight may have changed entirely.</p>

        <blockquote>"Dashboards show you the fire. Decision loops put it out."</blockquote>

        <h3>What Decision Loops Actually Look Like</h3>
        <p>A decision loop is a continuous, closed-circuit process that moves from signal detection to execution to learning without breaking the chain. Unlike dashboards that present data for human interpretation, decision loops evaluate context, generate options, verify plans, and execute — all within a governed framework.</p>

        <p>The critical difference is continuity. A dashboard is a snapshot. A decision loop is a process. The SRPVDAL framework implements this as a seven-stage pipeline: Sense the signal, Reason about causes and options, Plan the response, Verify the plan against constraints, Decide based on confidence and risk, Act within governance boundaries, and Learn from the outcome to improve future cycles.</p>

        <h3>The Organizational Impact</h3>
        <p>Organizations that shift from dashboards to decision loops report a fundamental change in how teams operate. Analysts stop building reports and start configuring governance policies. Managers stop reviewing dashboards and start auditing decision traces. Executives stop asking "what happened" and start evaluating "what the system decided and why."</p>

        <p>This is not a marginal efficiency gain. It is a structural transformation in how operational intelligence flows through the enterprise. The organizations making this shift are reducing decision latency by 50 to 75 times while simultaneously improving traceability and governance — outcomes that the dashboard model was never designed to deliver.</p>

        <p>The BI industry created the foundation. Decision intelligence builds the structure on top. The question for enterprise leaders is not whether dashboards were valuable — they were. The question is whether they are sufficient for the velocity and complexity of modern business. The answer, increasingly, is no.</p>
      `
    },
    {
      id: 5,
      title: "How Knowledge Graphs Power Causal Decision-Making",
      category: "Technology",
      date: "February 18, 2026",
      author: "MIZ OKI Team",
      readTime: "7 min read",
      excerpt: "A technical deep-dive into how Knowledge Graph architectures enable causal reasoning, long-term memory, and contextual decisions.",
      content: `
        <p>Machine learning models are powerful at pattern recognition. They are weak at causal reasoning. This distinction matters enormously in enterprise decision-making, where understanding why something happened is as important as predicting what will happen next.</p>

        <h3>Beyond Correlation</h3>
        <p>Traditional ML models identify correlations in data. A pricing model might learn that demand drops when prices increase — a useful but shallow insight. A causal model, powered by a Knowledge Graph, can trace the full chain: price increase reduces conversion rate, which reduces order volume, which triggers excess inventory, which eventually forces deeper markdowns that erode margins more than the original price increase generated.</p>

        <p>This causal chain is not learned from data alone. It is modeled explicitly in a Knowledge Graph that captures entities, relationships, and causal pathways. The graph represents organizational knowledge — the kind that lives in domain experts' heads and gets lost when they leave.</p>

        <blockquote>"Correlation tells you what happened together. Causation tells you what will happen if you act."</blockquote>

        <h3>The Memory Advantage</h3>
        <p>Enterprise decisions do not happen in isolation. A supply chain disruption in Q1 affects inventory positions in Q2, which constrains promotional planning in Q3. Traditional ML models treat each prediction as independent. A Knowledge Graph maintains temporal context — it remembers what happened, what decisions were made, and what outcomes resulted.</p>

        <p>This long-term memory enables compound reasoning. When a new signal arrives, the system does not just match it against current patterns. It evaluates it against the full history of related signals, decisions, and outcomes. The system can identify that a seemingly minor supply deviation matches a pattern that preceded a major disruption 18 months ago — context that no dashboard would surface.</p>

        <h3>Multi-Agent Reasoning on the Graph</h3>
        <p>MIZ OKI's Knowledge Graph serves as the shared substrate for multi-agent reasoning. Different specialized agents — demand, pricing, inventory, risk — query the same graph but apply different reasoning frameworks. When these agents disagree, the disagreement is productive because it is grounded in the same causal model. The debate is about interpretation, not about which data to trust.</p>

        <p>This architecture solves one of the hardest problems in enterprise AI: reconciling conflicting signals across domains. When the demand agent sees upward pressure but the risk agent sees supply constraints, the Knowledge Graph provides the causal framework to evaluate the trade-off. The system can explain not just what it decided, but why the trade-off was resolved in a specific direction.</p>

        <p>The Knowledge Graph is not a static database. It evolves with every decision cycle. New relationships are discovered. Causal pathways are validated or invalidated by outcomes. The graph becomes a living model of how the business actually works — not how someone thought it worked when they built the last dashboard.</p>
      `
    },
    {
      id: 6,
      title: "ROI of Decision Intelligence: Metrics That Actually Matter",
      category: "Metrics",
      date: "February 12, 2026",
      author: "MIZ OKI Team",
      readTime: "5 min read",
      excerpt: "Connecting platform metrics to business outcomes: how to measure the real value of autonomous decision systems.",
      content: `
        <p>Enterprise software has a measurement problem. Vendors promise ROI but deliver metrics that are disconnected from business outcomes. Decision intelligence must be held to a higher standard — its value should be measurable in the same units the business uses.</p>

        <h3>The Six Metrics That Matter</h3>
        <p>After hundreds of enterprise engagements, six metrics have emerged as the definitive indicators of decision intelligence value. They are not vanity metrics. They connect directly to P&L impact and governance quality.</p>

        <p><strong>Decision Latency</strong> measures time from signal detection to executed action. This is the primary velocity metric. Reductions of 50 to 75 times are typical across deployments. In revenue terms, every day of latency reduction recovers a quantifiable amount of leaked revenue.</p>

        <p><strong>Decision Confidence</strong> captures the confidence score and governance thresholds applied to each action. This metric prevents the system from acting on weak signals and provides the calibration data needed to tune autonomy boundaries.</p>

        <blockquote>"If you cannot measure the confidence of a decision, you cannot govern it."</blockquote>

        <p><strong>Override Frequency</strong> tracks how often humans intervene and, critically, why. A healthy system shows declining override rates over time as governance policies mature. Sudden spikes indicate changing conditions that require policy review.</p>

        <p><strong>Outcome Delta</strong> measures the difference between autonomous decisions and the baseline — either historical performance or a control group running under the old process. This is the most direct measure of value creation and typically shows 18% to 35% improvement in revenue-impacting decisions.</p>

        <h3>From Metrics to Business Case</h3>
        <p><strong>Learning Velocity</strong> quantifies the system's improvement rate over time. Organizations typically see a 15-20% improvement curve in decision quality during the first 90 days. This metric is particularly important for board presentations because it demonstrates compounding returns.</p>

        <p><strong>Audit Completeness</strong> measures the percentage of actions with full decision traces. In regulated industries, this metric is non-negotiable — anything below 100% is a compliance risk. Even in non-regulated environments, complete audit trails provide the transparency that builds organizational trust in autonomous systems.</p>

        <h3>Calculating Real ROI</h3>
        <p>The total annual value of decision intelligence combines three components: leakage recovery (revenue saved through faster, better decisions), cost savings (operational efficiency from automation), and risk reduction (avoided losses from governed execution). For a $50M revenue organization with 8% leakage and $20M in operational costs, the typical annual value ranges from $6M to $12M — with a payback period of approximately 3.2 months.</p>

        <p>These numbers are not projections. They are measured outcomes from deployed systems with complete decision traces. The metrics that matter are the ones that connect directly to business value, and decision intelligence is uniquely positioned to deliver them because every action is logged, traced, and measurable.</p>
      `
    }
  ];

  // ---- NAVIGATION ----
  const nav = document.getElementById('nav');
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobileMenu');
  const navLinks = document.querySelectorAll('.nav-links a, .mobile-menu a');

  // Scroll effect on nav
  if (nav) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    });
  }

  // Hamburger toggle
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('open');
      mobileMenu.classList.toggle('open');
      document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
    });
  }

  // Close mobile menu on link click
  document.querySelectorAll('.mobile-menu a').forEach(link => {
    link.addEventListener('click', () => {
      if (hamburger) {
        hamburger.classList.remove('open');
      }
      if (mobileMenu) {
        mobileMenu.classList.remove('open');
      }
      document.body.style.overflow = '';
    });
  });

  // Active nav link on scroll
  const sections = document.querySelectorAll('section[id]');
  function updateActiveLink() {
    const scrollPos = window.scrollY + 120;
    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');
      if (scrollPos >= top && scrollPos < top + height) {
        document.querySelectorAll('.nav-links a').forEach(a => {
          a.classList.remove('active');
          if (a.getAttribute('href') === '#' + id) {
            a.classList.add('active');
          }
        });
      }
    });
  }
  if (sections.length) {
    window.addEventListener('scroll', updateActiveLink);
  }

  // ---- SCROLL REVEAL ----
  const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  revealElements.forEach(el => revealObserver.observe(el));

  // ---- ANIMATED COUNTERS ----
  const counterElements = document.querySelectorAll('.metric-value[data-count]');
  let countersAnimated = false;

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !countersAnimated) {
        countersAnimated = true;
        animateCounters();
      }
    });
  }, { threshold: 0.3 });

  counterElements.forEach(el => counterObserver.observe(el));

  function animateCounters() {
    counterElements.forEach(el => {
      const target = parseFloat(el.dataset.count);
      const prefix = el.dataset.prefix || '';
      const suffix = el.dataset.suffix || '';
      const isDecimal = el.dataset.decimal === 'true';
      const duration = 2000;
      const start = Date.now();

      function step() {
        const elapsed = Date.now() - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = isDecimal
          ? (target * eased).toFixed(1)
          : Math.floor(target * eased);
        el.textContent = prefix + current + suffix;
        if (progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  // ---- ROI CALCULATOR ----
  const roiInputs = ['roi-revenue', 'roi-latency', 'roi-leakage', 'roi-opscost'];

  function parseNumber(str) {
    return parseFloat(str.replace(/[^0-9.]/g, '')) || 0;
  }

  function formatCurrency(num) {
    if (num >= 1e9) return '$' + (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return '$' + (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return '$' + (num / 1e3).toFixed(0) + 'K';
    return '$' + num.toFixed(0);
  }

  function calculateROI() {
    const revenue = parseNumber(document.getElementById('roi-revenue').value);
    const latency = parseNumber(document.getElementById('roi-latency').value);
    const leakage = parseNumber(document.getElementById('roi-leakage').value);
    const opsCost = parseNumber(document.getElementById('roi-opscost').value);

    // Leakage Recovery = Revenue × (Leakage% / 100) × 0.50 (50% recovery rate)
    const leakageRecovery = revenue * (leakage / 100) * 0.50;

    // Cost Savings = OpsCost × 0.31 (average 31% savings)
    const costSavings = opsCost * 0.31;

    // Total annual value
    const totalValue = leakageRecovery + costSavings;

    // Payback = (estimated annual platform cost / total value) × 12
    // Platform cost ~15% of total value for estimation
    const estimatedCost = totalValue * 0.15;
    const payback = totalValue > 0 ? (estimatedCost / totalValue) * 12 : 0;

    document.getElementById('roi-out-leakage').textContent = formatCurrency(leakageRecovery);
    document.getElementById('roi-out-savings').textContent = formatCurrency(costSavings);
    document.getElementById('roi-out-total').textContent = formatCurrency(totalValue);
    document.getElementById('roi-out-payback').textContent = payback > 0 ? payback.toFixed(1) + ' mo' : '—';
  }

  roiInputs.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', calculateROI);
      el.addEventListener('focus', function() { this.select(); });
    }
  });

  // Run initial calculation
  const hasRoiCalculator = roiInputs.every(id => document.getElementById(id)) &&
    document.getElementById('roi-out-leakage') &&
    document.getElementById('roi-out-savings') &&
    document.getElementById('roi-out-total') &&
    document.getElementById('roi-out-payback');

  if (hasRoiCalculator) {
    calculateROI();
  }

  // ---- BLOG ----
  function renderBlog() {
    const grid = document.getElementById('blogGrid');
    if (!grid) return;

    grid.innerHTML = blogPosts.map((post, i) => `
      <div class="card blog-card ${i === 0 ? 'featured' : ''} reveal ${i < 3 ? 'delay-' + (i + 1) : ''}" data-post-id="${post.id}">
        <div class="blog-category"><span class="badge">${post.category}</span></div>
        <h3>${post.title}</h3>
        <p class="blog-excerpt">${post.excerpt}</p>
        <div class="blog-meta">
          <span>${post.author}</span>
          <span class="dot"></span>
          <span>${post.date}</span>
          <span class="dot"></span>
          <span>${post.readTime}</span>
        </div>
      </div>
    `).join('');

    // Add click handlers
    grid.querySelectorAll('.blog-card').forEach(card => {
      card.addEventListener('click', () => {
        const postId = parseInt(card.dataset.postId);
        openBlogPost(postId);
      });
    });

    // Re-observe reveal elements
    grid.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));
  }

  function openBlogPost(id) {
    const post = blogPosts.find(p => p.id === id);
    if (!post) return;

    const modal = document.getElementById('blogModal');
    const content = document.getElementById('blogModalContent');

    if (!modal || !content) return;

    content.innerHTML = `
      <div class="blog-category"><span class="badge">${post.category}</span></div>
      <h2>${post.title}</h2>
      <div class="blog-meta">
        <span>${post.author}</span>
        <span class="dot"></span>
        <span>${post.date}</span>
        <span class="dot"></span>
        <span>${post.readTime}</span>
      </div>
      <div class="blog-modal-body">
        ${post.content}
      </div>
    `;

    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeBlogModal() {
    const modal = document.getElementById('blogModal');
    if (!modal) return;
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }

  const blogModalClose = document.getElementById('blogModalClose');
  const blogModal = document.getElementById('blogModal');
  if (blogModalClose) {
    blogModalClose.addEventListener('click', closeBlogModal);
  }
  if (blogModal) {
    blogModal.addEventListener('click', (e) => {
      if (e.target === e.currentTarget) closeBlogModal();
    });
  }

  // Close modal on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeBlogModal();
  });

  renderBlog();

  // ---- LOGIN FORM ----
  const loginForm = document.getElementById('loginForm');
  const passwordToggle = document.getElementById('passwordToggle');
  const loginPassword = document.getElementById('login-password');

  if (passwordToggle && loginPassword) {
    passwordToggle.addEventListener('click', () => {
      const type = loginPassword.type === 'password' ? 'text' : 'password';
      loginPassword.type = type;
      // Toggle eye icon
      const eyeIcon = document.getElementById('eyeIcon');
      if (eyeIcon) {
        if (type === 'text') {
          eyeIcon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
        } else {
          eyeIcon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
        }
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();
      window.open('https://miz-oki-command-center-ui-698171499447.us-central1.run.app/login', '_blank');
    });
  }

  // ---- SMOOTH SCROLL FOR HASH LINKS ----
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const top = target.offsetTop - 72;
        window.scrollTo({ top, behavior: 'smooth' });

        // Update URL hash without jump
        history.pushState(null, '', href);
      }
    });
  });

  // Handle initial hash on page load
  if (window.location.hash) {
    setTimeout(() => {
      const target = document.querySelector(window.location.hash);
      if (target) {
        const top = target.offsetTop - 72;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    }, 100);
  }

  // ---- SRPVDAL ANIMATION ----
  function animateSRPVDAL() {
    const nodes = document.querySelectorAll('.srpvdal-node circle:first-child');
    if (!nodes.length) return;
    let current = 0;

    setInterval(() => {
      nodes.forEach((node, i) => {
        if (i === current) {
          node.style.stroke = '#00D4FF';
          node.style.strokeWidth = '3';
          node.style.filter = 'drop-shadow(0 0 12px rgba(0, 212, 255, 0.6))';
        } else {
          node.style.stroke = '#00D4FF';
          node.style.strokeWidth = '2';
          node.style.filter = 'none';
        }
      });
      current = (current + 1) % nodes.length;
    }, 1500);
  }

  animateSRPVDAL();

})();
