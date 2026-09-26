/**
 * useScrollAnimations
 * -------------------
 * Shared GSAP + ScrollTrigger utility functions for ClearanceX.
 * Import and call inside a gsap.context() block for automatic cleanup.
 */

import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

/** Whether the user has asked for reduced motion */
export const prefersReducedMotion =
  typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false;

/** Is the current viewport mobile-sized? */
export const isMobile = () =>
  typeof window !== 'undefined' && window.innerWidth < 768;

/**
 * Standard section reveal: fade-up animation tied to ScrollTrigger.
 */
export function revealSection(
  el: gsap.TweenTarget,
  opts: {
    y?: number;
    duration?: number;
    delay?: number;
    start?: string;
    ease?: string;
  } = {}
) {
  if (prefersReducedMotion) {
    gsap.set(el, { opacity: 1, y: 0 });
    return;
  }
  const dist = isMobile() ? 30 : (opts.y ?? 50);
  gsap.fromTo(
    el,
    { opacity: 0, y: dist },
    {
      opacity: 1,
      y: 0,
      duration: opts.duration ?? 0.9,
      delay: opts.delay ?? 0,
      ease: opts.ease ?? 'power3.out',
      scrollTrigger: {
        trigger: el as Element,
        start: opts.start ?? 'top 88%',
        toggleActions: 'play none none none',
      },
    }
  );
}

/**
 * Stagger reveal for a container's children.
 */
export function revealStagger(
  container: Element | null,
  children: string,
  opts: {
    y?: number;
    scale?: number;
    stagger?: number;
    duration?: number;
    start?: string;
    ease?: string;
  } = {}
) {
  if (!container) return;
  const nodes = container.querySelectorAll(children);
  if (!nodes.length) return;
  if (prefersReducedMotion) {
    gsap.set(nodes, { opacity: 1, y: 0, scale: 1 });
    return;
  }
  const dist = isMobile() ? 20 : (opts.y ?? 40);
  gsap.fromTo(
    nodes,
    { opacity: 0, y: dist, scale: opts.scale ?? 1 },
    {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: opts.duration ?? 0.75,
      stagger: opts.stagger ?? 0.1,
      ease: opts.ease ?? 'power3.out',
      scrollTrigger: {
        trigger: container,
        start: opts.start ?? 'top 88%',
        toggleActions: 'play none none none',
      },
    }
  );
}

/**
 * Card stagger reveal — slight scale from 0.97→1.
 */
export function revealCards(
  container: Element | null,
  cardSelector: string = '.anim-card',
  opts: { stagger?: number; start?: string } = {}
) {
  if (!container) return;
  const nodes = container.querySelectorAll(cardSelector);
  if (!nodes.length) return;
  if (prefersReducedMotion) {
    gsap.set(nodes, { opacity: 1, y: 0, scale: 1 });
    return;
  }
  const dist = isMobile() ? 18 : 30;
  gsap.fromTo(
    nodes,
    { opacity: 0, y: dist, scale: 0.97 },
    {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.65,
      stagger: opts.stagger ?? 0.09,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: container,
        start: opts.start ?? 'top 88%',
        toggleActions: 'play none none none',
      },
    }
  );
}

/**
 * Horizontal slide-in from left or right.
 */
export function revealHorizontal(
  el: gsap.TweenTarget,
  direction: 'left' | 'right' = 'left',
  opts: { distance?: number; duration?: number; start?: string } = {}
) {
  if (prefersReducedMotion) {
    gsap.set(el, { opacity: 1, x: 0 });
    return;
  }
  const dist = (isMobile() ? 24 : (opts.distance ?? 60)) * (direction === 'right' ? 1 : -1);
  gsap.fromTo(
    el,
    { opacity: 0, x: dist },
    {
      opacity: 1,
      x: 0,
      duration: opts.duration ?? 0.85,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: el as Element,
        start: opts.start ?? 'top 85%',
        toggleActions: 'play none none none',
      },
    }
  );
}
