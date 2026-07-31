# Deployment

## Project Setup
1. Install backend dependencies in the `Task 2/backend` environment.
2. Navigate to the frontend folder and run `npm install` to install linting and formatting tools only.

## Development Workflow
- `npm run lint` — run ESLint against the frontend sources.
- `npm run format` — format frontend JS, CSS, MD, and JSON files with Prettier.

## Build / Run Instructions
- Backend: start the FastAPI app normally from `Task 2/backend`.
- Frontend: the FastAPI backend serves frontend assets automatically via static routes.
- No frontend bundling is required; the app uses native ES modules.

## Backend/Frontend Integration
- The frontend uses relative request paths from `js/core/Config.js` such as `/estimate` and `/metrics`.
- Backend assets like `/js/app.js` and `/css/globals.css` are served by FastAPI static routes.
- The `preview` stream is built from the same origin and handled by the backend.

## Deployment Considerations
- Keep the frontend lightweight: no bundler, no transpiler, no framework.
- Ensure `API_BASE_URL` in `frontend/js/core/Config.js` stays empty when served from the same origin.
- Use `npm run lint` and `npm run format` before committing frontend changes.
