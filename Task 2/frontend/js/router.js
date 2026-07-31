import { APP_ROUTES as ROUTES, DEFAULT_ROUTE } from './config.js';

function getCurrentRoute() {
  const hash = window.location.hash.replace('#', '');
  return ROUTES.includes(hash) ? hash : DEFAULT_ROUTE;
}

function activateNav(page, navLinks) {
  navLinks.forEach(link => {
    const isActive = link.dataset.page === page;
    link.classList.toggle('active', isActive);
    link.setAttribute('aria-current', isActive ? 'page' : 'false');
  });
}

export function initRouter({ navLinks, pageSections, onRouteChange }) {
  const route = getCurrentRoute();
  setRoute(route, navLinks, pageSections, onRouteChange);

  window.addEventListener('hashchange', () => {
    const nextRoute = getCurrentRoute();
    setRoute(nextRoute, navLinks, pageSections, onRouteChange);
  });

  navLinks.forEach(link => {
    link.addEventListener('click', event => {
      event.preventDefault();
      const page = link.dataset.page;
      if (page) {
        window.location.hash = page;
      }
    });
  });
}

function setRoute(page, navLinks, pageSections, onRouteChange) {
  Object.entries(pageSections).forEach(([key, section]) => {
    if (!section) return;
    section.classList.toggle('hidden', key !== page);
  });
  activateNav(page, navLinks);
  if (onRouteChange) {
    onRouteChange(page);
  }
}
