(function() {
  'use strict';

  const isMobile = () => window.innerWidth <= 768;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── CSRF Token ──
  function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  // ── Mobile Menu ──
  function initMobileMenu() {
    const hamburger = document.getElementById('hamburger');
    const menu = document.getElementById('mobileMenu');
    if (!hamburger || !menu) return;

    const toggle = () => {
      const open = menu.classList.toggle('open');
      hamburger.classList.toggle('is-active', open);
      document.body.classList.toggle('menu-open', open);
      hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
    };

    hamburger.addEventListener('click', toggle);

    window.closeMobileMenu = () => {
      menu.classList.remove('open');
      hamburger.classList.remove('is-active');
      document.body.classList.remove('menu-open');
      hamburger.setAttribute('aria-expanded', 'false');
    };

    menu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => window.closeMobileMenu());
    });
  }

  // ── Smooth Scroll ──
  function getNavOffset() {
    return parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-height')) || 72;
  }

  function isPortfolioPage() {
    return !!document.getElementById('hero');
  }

  function sectionFromPathname() {
    const parts = window.location.pathname.replace(/\/$/, '').split('/');
    const segment = parts[parts.length - 1] || 'home';
    if (segment === 'home') return 'hero';
    const valid = ['hero', 'about', 'education', 'projects', 'contact'];
    return valid.includes(segment) ? segment : null;
  }

  function setActiveNav(section) {
    document.querySelectorAll('.nav-section-link').forEach(link => {
      link.classList.toggle('is-active', link.dataset.section === section);
    });
  }

  function scrollToSection(selector) {
    const target = document.querySelector(selector);
    if (!target) return;
    const top = target.getBoundingClientRect().top + window.scrollY - getNavOffset();
    window.scrollTo({ top, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
  }

  function navigateToSection(section, url, { replace = false } = {}) {
    if (!section || !document.getElementById(section)) return;
    scrollToSection(`#${section}`);
    setActiveNav(section);
    if (url) {
      const state = { section };
      if (replace) {
        history.replaceState(state, '', url);
      } else {
        history.pushState(state, '', url);
      }
    }
  }

  function initSectionNavigation() {
    if (!isPortfolioPage()) return;

    const activeFromServer = document.body.dataset.activeSection;

    const legacyHash = window.location.hash.slice(1);
    if (legacyHash && document.getElementById(legacyHash)) {
      const legacyLink = document.querySelector(`.nav-section-link[data-section="${legacyHash}"]`);
      const legacyUrl = legacyLink ? legacyLink.getAttribute('href') : window.location.pathname;
      requestAnimationFrame(() => navigateToSection(legacyHash, legacyUrl, { replace: true }));
    } else if (activeFromServer) {
      const link = document.querySelector(`.nav-section-link[data-section="${activeFromServer}"]`);
      const url = activeFromServer === 'hero'
        ? document.querySelector('.nav-logo')?.getAttribute('href') || window.location.pathname
        : link?.getAttribute('href');
      requestAnimationFrame(() => {
        navigateToSection(activeFromServer, url || window.location.pathname, { replace: true });
      });
    } else {
      const current = sectionFromPathname();
      if (current) setActiveNav(current);
    }

    document.querySelectorAll('.section-link, .nav-section-link').forEach(anchor => {
      anchor.addEventListener('click', e => {
        const section = anchor.dataset.section;
        const href = anchor.getAttribute('href');
        if (!section || !document.getElementById(section)) return;

        if (isPortfolioPage()) {
          e.preventDefault();
          navigateToSection(section, href);
          if (typeof window.closeMobileMenu === 'function') window.closeMobileMenu();
        }
      });
    });

    window.addEventListener('popstate', e => {
      if (!isPortfolioPage()) return;
      const section = e.state?.section || sectionFromPathname();
      if (section && document.getElementById(section)) {
        scrollToSection(`#${section}`);
        setActiveNav(section);
      }
    });
  }

  function initScrollSpy() {
    if (!isPortfolioPage()) return;

    const sections = ['about', 'education', 'projects', 'contact'];
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('section-in-view');
            const id = entry.target.id;
            if (sections.includes(id)) {
              setActiveNav(id);
            }
          } else {
            entry.target.classList.remove('section-in-view');
          }
        });
      },
      { rootMargin: '-40% 0px -45% 0px', threshold: 0.01 }
    );

    ['hero', ...sections].forEach(id => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
  }

  function initScrollProgress() {
    const bar = document.getElementById('scroll-progress');
    if (!bar) return;

    const update = () => {
      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      bar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    };

    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  function initBackToTop() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;

    const homeUrl = document.querySelector('.nav-logo')?.getAttribute('href') || '/home/';

    window.addEventListener('scroll', () => {
      btn.hidden = window.scrollY < 400;
    }, { passive: true });

    btn.addEventListener('click', () => {
      if (isPortfolioPage()) {
        navigateToSection('hero', homeUrl);
      } else {
        window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
      }
    });
  }

  // ── Contact Form ──
  function initContactForm() {
    const form = document.getElementById('contact-form');
    if (!form) return;

    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.getElementById('btn-text');
    const successEl = document.getElementById('form-success');
    const errorEl = document.getElementById('form-error');

    const showFeedback = (el, show) => {
      if (!el) return;
      if (show) {
        el.removeAttribute('hidden');
        el.classList.add('is-visible');
      } else {
        el.setAttribute('hidden', '');
        el.classList.remove('is-visible');
      }
    };

    [successEl, errorEl].forEach(el => showFeedback(el, false));

    form.addEventListener('submit', async e => {
      e.preventDefault();

      if (submitBtn) submitBtn.disabled = true;
      if (btnText) btnText.textContent = 'Sending...';
      showFeedback(successEl, false);
      showFeedback(errorEl, false);

      const formData = new FormData(form);

      try {
        const postUrl = form.getAttribute('action') || window.location.pathname;
        const response = await fetch(postUrl, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
          },
          body: formData,
        });

        const data = await response.json().catch(() => ({}));
        document.querySelectorAll('.form-field-error').forEach(el => el.remove());

        if (response.ok && data.success) {
          form.reset();
          if (successEl && data.message) {
            successEl.textContent = `✓ ${data.message}`;
          }
          showFeedback(successEl, true);
        } else {
          if (data.errors) {
            Object.entries(data.errors).forEach(([name, message]) => {
              const input = form.querySelector(`[name="${name}"]`);
              if (!input) return;
              const row = input.closest('.form-row');
              if (!row) return;
              const err = document.createElement('span');
              err.className = 'form-field-error';
              err.textContent = message;
              row.appendChild(err);
            });
          }
          const fallback = response.status === 403
            ? 'Security check failed. Refresh and try again.'
            : 'Something went wrong. Please try again.';
          errorEl.textContent = `✗ ${data.error || fallback}`;
          showFeedback(errorEl, true);
        }
      } catch {
        errorEl.textContent = '✗ Network error. Check your connection and try again.';
        showFeedback(errorEl, true);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (btnText) btnText.textContent = 'Send Message →';
      }
    });
  }

  // ── GSAP Animations ──
  function initGSAPAnimations() {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
      document.querySelectorAll('.reveal').forEach(el => {
        el.classList.add('is-visible');
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    document.querySelectorAll('.title-line .line-inner').forEach(line => {
      gsap.to(line, {
        y: '0%',
        duration: 1.2,
        ease: 'power4.out',
        delay: 0.15,
        stagger: 0.08,
      });
    });

    document.querySelectorAll('.reveal').forEach((el, index) => {
      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 0.85,
        ease: 'power3.out',
        delay: Math.min(index * 0.04, 0.3),
        scrollTrigger: {
          trigger: el,
          start: 'top 90%',
          toggleActions: 'play none none none',
        },
        onComplete: () => el.classList.add('is-visible'),
      });
    });

    const navbar = document.getElementById('navbar');
    if (navbar) {
      ScrollTrigger.create({
        start: 80,
        onUpdate: self => {
          navbar.classList.toggle('scrolled', self.scroll() > 80);
        },
      });
    }

    requestAnimationFrame(() => ScrollTrigger.refresh());
  }

  // ── Mouse Parallax ──
  function initParallax() {
    if (prefersReducedMotion || isMobile()) return;
    const hero = document.getElementById('hero');
    if (!hero || typeof gsap === 'undefined') return;

    let raf = null;

    hero.addEventListener('mousemove', e => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        const rect = hero.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;

        const orbs = hero.querySelectorAll('.hero-orb');
        orbs.forEach((orb, i) => {
          const speed = 1 + i * 0.4;
          gsap.to(orb, {
            x: x * 25 * speed,
            y: y * 25 * speed,
            duration: 0.8,
            ease: 'power2.out',
          });
        });

        const title = hero.querySelector('.hero-title');
        if (title) {
          gsap.to(title, {
            x: x * 10,
            y: y * 6,
            duration: 0.6,
            ease: 'power2.out',
          });
        }

        raf = null;
      });
    });
  }

  // ── Loader ──
  function initLoader() {
    const loader = document.getElementById('loader');
    if (!loader) {
      document.body.classList.remove('loading');
      document.body.classList.add('loaded');
      initGSAPAnimations();
      initParallax();
      return;
    }

    if (prefersReducedMotion || typeof gsap === 'undefined') {
      loader.remove();
      document.body.classList.remove('loading');
      document.body.classList.add('loaded');
      initGSAPAnimations();
      initParallax();
      return;
    }

    const tl = gsap.timeline({
      defaults: { ease: 'power3.out' },
      onComplete: () => {
        loader.remove();
        document.body.classList.remove('loading');
        document.body.classList.add('loaded');
        initGSAPAnimations();
        initParallax();
      },
    });

    const nameEl = document.getElementById('loader-name');
    if (nameEl) {
      tl.to(nameEl, { opacity: 1, y: 0, duration: 0.8 });
    }

    const bar = document.getElementById('loader-bar');
    if (bar) {
      tl.to(bar, { width: '100%', duration: 1.4, ease: 'power2.inOut' }, 0.2);
    }

    const counter = document.getElementById('loader-counter');
    if (counter) {
      tl.to({ val: 0 }, {
        val: 100,
        duration: 1.4,
        ease: 'power2.inOut',
        onUpdate() {
          counter.textContent = String(Math.floor(this.targets()[0].val)).padStart(3, '0');
        },
      }, 0.2);
    }

    tl.to(loader, { opacity: 0, duration: 0.6 }, 1.6);
    tl.set(loader, { display: 'none' });
  }

  // ── Footer Year ──
  function initFooterYear() {
    const yearEl = document.getElementById('year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
  }

  // ── MODAL FUNCTIONS (FIXED) ──

  /**
   * Open project modal with project data
   * @param {number|string} projectId - The ID of the project to display
   */
  window.openProjectModal = function(projectId) {
    const modal = document.getElementById('projectModal');
    if (!modal) {
      console.error('Modal element not found');
      return;
    }
    
    // Get project data
    const data = window.projectData ? window.projectData[projectId] : null;
    if (!data) {
      console.error('Project data not found for ID:', projectId);
      
      // Show error in modal
      const titleEl = document.getElementById('modalTitle');
      const descEl = document.getElementById('modalDescription');
      if (titleEl) titleEl.textContent = 'Project Not Found';
      if (descEl) descEl.textContent = 'Sorry, the project data could not be loaded.';
      
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
      document.body.classList.add('modal-open');
      return;
    }
    
    console.log('📊 Opening project:', data.project_name || data.name);
    
    // ── Populate modal with project data ──
    const badgeEl = document.getElementById('modalBadge');
    const titleEl = document.getElementById('modalTitle');
    const descEl = document.getElementById('modalDescription');
    
    if (badgeEl) badgeEl.textContent = data.category || 'Project';
    if (titleEl) titleEl.textContent = data.project_name || data.name || 'Project';
    if (descEl) descEl.textContent = data.full_description || data.description || 'No description available.';
    
    // ── Gallery ──
    const gallery = document.getElementById('modalGallery');
    const imageCountEl = document.getElementById('modalImageCount');

    if (gallery) {
      gallery.innerHTML = '';
      const images = data.images || [];

      if (imageCountEl) {
        imageCountEl.textContent = images.length
          ? `${images.length} ${images.length === 1 ? 'Image' : 'Images'}`
          : '';
      }

      if (images.length > 0) {
        images.forEach(function(img, index) {
          const item = document.createElement('div');
          item.className = 'modal-gallery-item';
          item.innerHTML = `
            <img
              src="${img.url}"
              alt="${data.project_name || data.name} screenshot ${index + 1}"
              loading="lazy"
              decoding="async"
            >
            ${
              img.caption
                ? `<div class="gallery-caption">${img.caption}</div>`
                : ''
            }
          `;
          gallery.appendChild(item);
        });
      } else {
        gallery.innerHTML = `
          <div class="gallery-empty">
            <span class="gallery-empty-icon" aria-hidden="true">⌨</span>
            <span>No screenshots available</span>
          </div>
        `;
      }
    }
    
    // ── Tech Stack ──
    const techStack = document.getElementById('modalTechStack');
    if (techStack) {
      techStack.innerHTML = '';
      
      const technologies = data.technology || data.technologies || [];
      
      if (technologies && Array.isArray(technologies) && technologies.length > 0) {
        const validTechs = technologies.filter(tech => tech && tech.trim());
        if (validTechs.length > 0) {
          validTechs.forEach(tech => {
            techStack.innerHTML += `<span class="tech-tag">${tech}</span>`;
          });
        } else {
          techStack.innerHTML = `<span class="tech-tag" style="opacity:0.5;">No technologies listed</span>`;
        }
      } else {
        techStack.innerHTML = `<span class="tech-tag" style="opacity:0.5;">No technologies listed</span>`;
      }
    }
    
    // ── Details Grid ──
    const details = document.getElementById('modalDetails');
    if (details) {
      let detailsHTML = `
        <div class="modal-detail-item">
          <span class="detail-label">Category</span>
          <span class="detail-value">
            ${data.category || 'Web Development'}
          </span>
        </div>
      `;

      if (data.project_year || data.year) {
        detailsHTML += `
          <div class="modal-detail-item">
            <span class="detail-label">Year</span>
            <span class="detail-value">
              ${data.project_year || data.year || 'N/A'}
            </span>
          </div>
        `;
      }

      details.innerHTML = detailsHTML;
    }
    
    // ── Actions ──
    const actions = document.getElementById('modalActions');
    if (actions) {
      actions.innerHTML = '';
      
      const github = data.github_url || data.githubUrl || '';
      const live = data.live_url || data.liveUrl || '';
      
      if (github) {
        actions.innerHTML += `
          <a href="${github}" target="_blank" rel="noopener noreferrer" class="modal-btn modal-btn-secondary">
            <svg width="18" height="18" viewBox="0 0 16 16" fill="none">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" fill="currentColor"/>
            </svg>
            View on GitHub
          </a>
        `;
      }
      
      if (live) {
        actions.innerHTML += `
          <a href="${live}" target="_blank" rel="noopener noreferrer" class="modal-btn modal-btn-primary">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M1 17L17 1M17 1H4M17 1V14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            View Live Project
          </a>
        `;
      }
      
      if (!github && !live) {
        actions.innerHTML = `
          <span style="font-family: var(--font-mono); font-size: 13px; color: var(--text-muted);">
            No external links available for this project.
          </span>
        `;
      }
    }
    
    // ── Open Modal ──
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    document.body.classList.add('modal-open');
  };

  /**
   * Close project modal
   * @param {Event} [event] - Optional click event
   */
  window.closeProjectModal = function(event) {
    // If event is provided and it's a click on the overlay
    if (event && event.target === event.currentTarget) {
      // Close the modal
    } else if (event) {
      // Don't close if clicking inside modal content
      return;
    }
    
    const modal = document.getElementById('projectModal');
    if (!modal) return;
    
    modal.classList.remove('active');
    document.body.style.overflow = '';
    document.body.classList.remove('modal-open');
  };

  // ── Initialize Project Cards ──
  function initProjectCards() {
    const projectsList = document.getElementById('projectsList');
    if (!projectsList) return;

    function openFromCard(card) {
      const projectId = card.dataset.projectId;
      if (projectId) {
        window.openProjectModal(parseInt(projectId, 10));
      }
    }

    projectsList.addEventListener('click', function(e) {
      // Check if clicked on the card link button
      const button = e.target.closest('.project-card-link');
      if (button) {
        e.stopPropagation();
        const projectId = button.dataset.projectId;
        if (projectId) {
          window.openProjectModal(parseInt(projectId, 10));
        }
        return;
      }

      // Check if clicked on the card itself
      const card = e.target.closest('.project-card');
      if (card) {
        openFromCard(card);
      }
    });

    // Keyboard support for accessibility
    projectsList.addEventListener('keydown', function(e) {
      const card = e.target.closest('.project-card');
      if (!card) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openFromCard(card);
      }
    });
  }

  // ── Keyboard Support (Global) ──
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const modal = document.getElementById('projectModal');
      if (modal && modal.classList.contains('active')) {
        window.closeProjectModal();
      }
    }
  });

  // ── Click outside to close (Global) ──
  document.addEventListener('click', function(e) {
    const modal = document.getElementById('projectModal');
    if (modal && modal.classList.contains('active')) {
      // Close only if clicking the overlay background, not the modal content
      if (e.target === modal) {
        window.closeProjectModal(e);
      }
    }
  });

  // ── Boot ──
  function init() {
    initMobileMenu();
    initSectionNavigation();
    initScrollSpy();
    initScrollProgress();
    initBackToTop();
    initContactForm();
    initFooterYear();
    initProjectCards();

    // Log project data status
    if (window.projectData) {
      console.log('✅ Project data available:', Object.keys(window.projectData).length, 'projects');
    } else {
      console.warn('⚠️ Project data not yet loaded, waiting...');
      setTimeout(function() {
        if (window.projectData) {
          console.log('✅ Project data loaded after delay:', Object.keys(window.projectData).length, 'projects');
        }
      }, 500);
    }

    // Initialize loader
    if (document.readyState === 'complete') {
      initLoader();
    } else {
      window.addEventListener('load', initLoader, { once: true });
    }

    // Safety timeout to remove loader if something goes wrong
    setTimeout(() => {
      if (document.getElementById('loader')) {
        const loader = document.getElementById('loader');
        loader.remove();
        document.body.classList.remove('loading');
        document.body.classList.add('loaded');
        initGSAPAnimations();
        initParallax();
      }
    }, 5000);
  }

  // Start everything
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();