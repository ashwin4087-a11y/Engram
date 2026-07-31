# Frontend Architecture

## Folder Structure
- `frontend/`
  - `css/` — all CSS style sheets separated by scope.
  - `js/` — vanilla ES module JavaScript source.
    - `core/` — centralized configuration and shared constants.
    - `components/` — reusable UI component modules.
    - `pages/` — page-level modules responsible for rendering and page state.
    - `services/` — backend service wrappers and API logic.
    - `utils/` — shared helpers such as formatting utilities.
    - `api.js` — centralized HTTP fetch layer.
    - `app.js` — application bootstrap and routing integration.
    - `router.js` — hash-based page routing.

## Component Hierarchy
- `app.js` bootstraps the application and initializes routing.
- `router.js` handles hash-based navigation and page visibility.
- Page modules in `js/pages/` expose `mount()` and `refresh()` semantics.
- Services in `js/services/` abstract backend API requests.
- `api.js` centralizes HTTP request handling.
- `core/Config.js` stores all backend routes, polling intervals, and feature flags.

## Routing
- The app uses hash routing with route names like `#dashboard`, `#calibration`, and `#analytics`.
- `router.js` activates the current page section and syncs active navigation styling.
- Page visibility is controlled with `hidden` CSS toggles.

## State Flow
- `app.js` holds runtime page state and polling interval management.
- Each page module refreshes its own data using service APIs.
- Backend health status is propagated through shared UI state functions.

## Service Layer
- Every backend endpoint is wrapped in a service module.
- Services call `api.js` rather than fetching directly from the page.
- This keeps API contract changes localized and the page code focused on UI.

## API Communication
- All URLs are centralized in `js/core/Config.js`.
- `api.js` builds request URLs and handles JSON parsing.
- Pages and services avoid hardcoded endpoints.
