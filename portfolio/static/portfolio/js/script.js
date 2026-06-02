/**
 * Portfolio — main interactions & animations
 * Requires GSAP + ScrollTrigger (loaded before this file)
 */

(function () {
  "use strict";

  const prefersReducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  const isMobile = () => window.innerWidth <= 768;

  /* ── Utilities ─────────────────────────────────────────── */
  function getCsrfToken() {
    const input = document.querySelector("[name=csrfmiddlewaretoken]");
    if (input) return input.value;
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function bindInteractiveCursor(cursor) {
    if (!cursor) return;

    const interactiveSelector =
      "a, button, .project-row, .skill-tag, #education .edu-card, .contact-link, .form-submit, .hamburger, .nav-cv-btn, .nav-cta, input, textarea";

    document.querySelectorAll(interactiveSelector).forEach((el) => {
      el.addEventListener("mouseenter", () => cursor.classList.add("hover"));
      el.addEventListener("mouseleave", () => cursor.classList.remove("hover"));
    });

    document.addEventListener("mousedown", () => cursor.classList.add("click"));
    document.addEventListener("mouseup", () => cursor.classList.remove("click"));
  }

  function initCustomCursor() {
    const cursor = document.getElementById("cursor");
    const dot = cursor?.querySelector(".cursor-dot");
    const ring = cursor?.querySelector(".cursor-ring");

    if (!cursor || !dot || !ring || isMobile() || prefersReducedMotion) {
      document.body.classList.remove("custom-cursor");
      return;
    }

    document.body.classList.add("custom-cursor");

    const showCursor = () => cursor.classList.add("is-active");

    if (typeof gsap !== "undefined") {
      const setDotX = gsap.quickSetter(dot, "left", "px");
      const setDotY = gsap.quickSetter(dot, "top", "px");

      document.addEventListener("mousemove", (e) => {
        const x = e.clientX;
        const y = e.clientY;

        setDotX(x);
        setDotY(y);
        showCursor();

        gsap.to(ring, {
          left: x,
          top: y,
          duration: 0.35,
          ease: "power2.out",
          overwrite: true,
        });
      });

      document.addEventListener("mouseleave", () => {
        cursor.classList.remove("is-active", "hover", "click");
      });

      document.addEventListener("mouseenter", showCursor);
    } else {
      document.addEventListener("mousemove", (e) => {
        const x = e.clientX + "px";
        const y = e.clientY + "px";
        dot.style.left = x;
        dot.style.top = y;
        ring.style.left = x;
        ring.style.top = y;
        showCursor();
      });
    }

    bindInteractiveCursor(cursor);
  }

  /* ── Mobile menu ───────────────────────────────────────── */
  function initMobileMenu() {
    const hamburger = document.getElementById("hamburger");
    const menu = document.getElementById("mobileMenu");
    if (!hamburger || !menu) return;

    const toggle = () => {
      const open = menu.classList.toggle("open");
      hamburger.classList.toggle("is-active", open);
      document.body.classList.toggle("menu-open", open);
      hamburger.setAttribute("aria-expanded", open ? "true" : "false");
    };

    hamburger.addEventListener("click", toggle);

    window.closeMobileMenu = () => {
      menu.classList.remove("open");
      hamburger.classList.remove("is-active");
      document.body.classList.remove("menu-open");
      hamburger.setAttribute("aria-expanded", "false");
    };

    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => window.closeMobileMenu());
    });
  }

  function getNavOffset() {
    return parseInt(
      getComputedStyle(document.documentElement).getPropertyValue("--nav-height") || "72",
      10,
    );
  }

  function scrollToSection(selector) {
    const target = document.querySelector(selector);
    if (!target) return;

    const top =
      target.getBoundingClientRect().top + window.scrollY - getNavOffset();

    window.scrollTo({
      top,
      behavior: prefersReducedMotion ? "auto" : "smooth",
    });

    document.querySelectorAll(".nav-section-link").forEach((link) => {
      const active = link.dataset.section === selector.replace("#", "");
      link.classList.toggle("is-active", active);
    });
  }

  /* ── Section navigation (Django URLs + hash) ───────────── */
  function initSmoothScroll() {
    document.querySelectorAll(".nav-section-link[data-section]").forEach((anchor) => {
      anchor.addEventListener("click", (e) => {
        const section = anchor.dataset.section;
        if (!section) return;

        const target = document.getElementById(section);
        if (!target) return;

        e.preventDefault();
        const hash = `#${section}`;
        history.pushState(null, "", hash);
        scrollToSection(hash);
        if (typeof window.closeMobileMenu === "function") {
          window.closeMobileMenu();
        }
      });
    });

    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
      if (anchor.classList.contains("nav-section-link")) return;

      anchor.addEventListener("click", (e) => {
        const id = anchor.getAttribute("href");
        if (!id || id === "#") return;

        const target = document.querySelector(id);
        if (!target) return;

        e.preventDefault();
        scrollToSection(id);
      });
    });

    if (window.location.hash) {
      requestAnimationFrame(() => scrollToSection(window.location.hash));
    }
  }

  /* ── Contact form (AJAX) ───────────────────────────────── */
  function initContactForm() {
    const form = document.getElementById("contact-form");
    if (!form) return;

    const submitBtn = document.getElementById("submit-btn");
    const btnText = document.getElementById("btn-text");
    const successEl = document.getElementById("form-success");
    const errorEl = document.getElementById("form-error");

    const showFeedback = (el, show) => {
      if (!el) return;
      if (show) {
        el.removeAttribute("hidden");
        el.classList.add("is-visible");
      } else {
        el.setAttribute("hidden", "");
        el.classList.remove("is-visible");
      }
    };

    [successEl, errorEl].forEach((el) => showFeedback(el, false));

    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (submitBtn) submitBtn.disabled = true;
      if (btnText) btnText.textContent = "Sending…";
      showFeedback(successEl, false);
      showFeedback(errorEl, false);

      const formData = new FormData(form);

      try {
        const postUrl = form.getAttribute("action") || window.location.pathname;
        const response = await fetch(postUrl, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCsrfToken(),
          },
          body: formData,
        });

        const data = await response.json().catch(() => ({}));

        document.querySelectorAll(".form-field-error").forEach((el) => el.remove());

        if (response.ok && data.success) {
          form.reset();
          showFeedback(successEl, true);
        } else {
          if (data.errors) {
            Object.entries(data.errors).forEach(([name, message]) => {
              const input = form.querySelector(`[name="${name}"]`);
              if (!input) return;
              const row = input.closest(".form-row");
              if (!row) return;
              const err = document.createElement("span");
              err.className = "form-field-error";
              err.textContent = message;
              row.appendChild(err);
            });
          }
          if (data.error) {
            errorEl.textContent = `✗ ${data.error}`;
          }
          showFeedback(errorEl, true);
        }
      } catch {
        showFeedback(errorEl, true);
      } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (btnText) btnText.textContent = "Send Message →";
      }
    });
  }

  function revealElement(el, immediate) {
    gsap.to(el, {
      opacity: 1,
      y: 0,
      duration: immediate ? 0.6 : 0.85,
      ease: "power3.out",
      overwrite: true,
      onComplete: () => el.classList.add("is-visible"),
    });
  }

  function isInViewport(el) {
    const rect = el.getBoundingClientRect();
    return rect.top < window.innerHeight * 0.92;
  }

  /* ── GSAP scroll animations ────────────────────────────── */
  function initScrollAnimations() {
    document.querySelectorAll(".reveal").forEach((el) => {
      el.classList.remove("is-visible");
    });

    if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") {
      document.querySelectorAll(".reveal").forEach((el) => {
        el.classList.add("is-visible");
        el.style.opacity = "1";
        el.style.transform = "none";
      });
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    const titleLines = document.querySelectorAll(".title-line");
    if (titleLines.length) {
      gsap.from(titleLines, {
        yPercent: 110,
        stagger: 0.12,
        duration: 1,
        ease: "power4.out",
        delay: 0.1,
      });
    }

    document.querySelectorAll(".reveal").forEach((el) => {
      if (isInViewport(el)) {
        revealElement(el, true);
        return;
      }

      gsap.to(el, {
        opacity: 1,
        y: 0,
        duration: 0.85,
        ease: "power3.out",
        scrollTrigger: {
          trigger: el,
          start: "top 88%",
          toggleActions: "play none none none",
        },
        onComplete: () => el.classList.add("is-visible"),
      });
    });

    document.querySelectorAll("[data-count]").forEach((el) => {
      const target = parseInt(el.dataset.count, 10);
      if (Number.isNaN(target)) return;

      ScrollTrigger.create({
        trigger: el,
        start: "top 85%",
        once: true,
        onEnter: () => {
          gsap.to(
            { val: 0 },
            {
              val: target,
              duration: 1.5,
              ease: "power2.out",
              onUpdate() {
                el.textContent = Math.floor(this.targets()[0].val) + "+";
              },
            },
          );
        },
      });
    });

    const navbar = document.getElementById("navbar");
    if (navbar) {
      ScrollTrigger.create({
        start: 80,
        onUpdate: (self) => {
          navbar.classList.toggle("scrolled", self.scroll() > 80);
        },
      });
    }

    requestAnimationFrame(() => ScrollTrigger.refresh());
  }

  function showMainLayout() {
    document.body.classList.remove("loading");
    document.body.classList.add("loaded");

    const mainParts = ["#navbar", ".page-content", "footer"];
    if (typeof gsap !== "undefined") {
      gsap.set(mainParts, { opacity: 1, y: 0, clearProps: "opacity,transform,visibility" });
    } else {
      mainParts.forEach((sel) => {
        document.querySelectorAll(sel).forEach((el) => {
          el.style.opacity = "1";
          el.style.transform = "none";
          el.style.visibility = "visible";
        });
      });
    }
  }

  function finishPageLoad() {
    const loader = document.getElementById("loader");
    showMainLayout();

    if (loader) loader.remove();

    initScrollAnimations();
    bindInteractiveCursor();

    if (typeof ScrollTrigger !== "undefined") {
      requestAnimationFrame(() => ScrollTrigger.refresh());
    }
  }

  function skipLoader() {
    const loader = document.getElementById("loader");
    showMainLayout();
    if (loader) loader.remove();
    initScrollAnimations();
    bindInteractiveCursor();
  }

  /* ── Page loader ───────────────────────────────────────── */
  function initLoader() {
    const loader = document.getElementById("loader");
    const bar = document.getElementById("loader-bar");
    const counter = document.getElementById("loader-counter");
    const name = document.getElementById("loader-name");

    if (!loader) {
      skipLoader();
      return;
    }

    if (prefersReducedMotion || typeof gsap === "undefined") {
      skipLoader();
      return;
    }

    const loadTimeline = gsap.timeline({
      defaults: { ease: "power3.out" },
      onComplete: finishPageLoad,
    });

    if (name) {
      loadTimeline.to(name, { opacity: 1, y: 0, duration: 0.8 }, 0);
    }

    if (bar) {
      loadTimeline.to(bar, { width: "100%", duration: 1.4, ease: "power2.out" }, 0);
    }

    if (counter) {
      loadTimeline.to(
        { value: 0 },
        {
          value: 100,
          duration: 1.4,
          ease: "power2.out",
          onUpdate() {
            counter.textContent = String(
              Math.floor(this.targets()[0].value),
            ).padStart(3, "0");
          },
        },
        0,
      );
    }

    loadTimeline.to(loader, { scale: 1.02, duration: 0.2 }, 1.4);
    loadTimeline.to(
      loader,
      { yPercent: -100, duration: 0.85, ease: "power4.inOut" },
      1.55,
    );
  }

  /* ── Footer year ───────────────────────────────────────── */
  function initFooterYear() {
    const yearEl = document.getElementById("year");
    if (yearEl) yearEl.textContent = new Date().getFullYear();
  }

  /* ── Boot ──────────────────────────────────────────────── */
  function init() {
    initCustomCursor();
    initMobileMenu();
    initSmoothScroll();
    initContactForm();
    initFooterYear();

    const startLoader = () => {
      initLoader();
      /* Fallback if GSAP fails or CDN is blocked */
      setTimeout(() => {
        if (document.getElementById("loader")) {
          skipLoader();
        }
      }, 5000);
    };

    if (document.readyState === "complete") {
      startLoader();
    } else {
      window.addEventListener("load", startLoader, { once: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
