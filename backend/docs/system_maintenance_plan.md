# System Maintenance & Cleanup Plan

## Goals

- Improve readability, modularity, and maintainability of the CRM + Justification system.
- Keep entry-points (main pages/routes) as orchestration-only, delegating to services/hooks/utils.
- Avoid destructive changes; prefer incremental, well-tested refactors.
- Remove or quarantine dead/legacy code only after verifying it is truly unused.

## High-level Architecture Notes

- Backend (FastAPI + SQLAlchemy):
  - Routes grouped under `app/routes`, but `justification.py` is a very large multi-purpose router (~1000+ lines).
  - Services under `app/services` hold business logic; some are large and multi-responsibility:
    - `crm.py` (~700 lines) mixes clients, snapshots, notes, and reminders.
    - `justification_forms.py` (~600 lines) handles PDFs, overlays, signatures, and field utilities.
    - `justification_packet.py` (~400 lines) orchestrates packet generation.
    - `justification_advice.py` (~380 lines) covers HTML building + PDF generation + static resources.
  - PDF utilities and path/file-name normalization logic are duplicated across multiple services/routes.

- Frontend (React + TypeScript, Vite):
  - Pages under `src/pages` and larger feature roots:
    - `pages/justification/JustificationPageRoot.tsx` (~700 lines) is a central orchestrator for the entire justification flow (clients, products, PDFs, signing).
    - `pages/crm/CrmPageRoot.tsx` (~650 lines) coordinates many CRM panels and actions.
  - Actions files already exist (`crmClients.ts`, `crmSnapshotsAndExport.ts`, `justNewProductsAndFormsActions.ts`, etc.), which is good, but root components still hold a lot of wiring and state.
  - Utility modules exist for dates (`utils/dateFormat.ts`) and API clients (`api/*.ts`).

## Main Weak Points & Candidates for Improvement

### 1. Oversized backend route: `app/routes/justification.py`

- Responsibilities mixed in one file:
  - Saving products CRUD and sync from CRM.
  - Existing/New products CRUD.
  - Form instances CRUD.
  - Advice HTML/PDF endpoints.
  - Kits and B1 download/upload/overlay endpoints.
  - Packet download/generation/signing endpoints.
- Risks:
  - Hard to navigate and reason about.
  - New endpoints are likely to be added here, making it worse.
- Plan:
  - Split router into feature-focused routers while keeping URLs stable:
    - `routes/justification_products.py` – saving/existing/new products + form instances.
    - `routes/justification_documents.py` – advice/B1/kits/packet PDFs (download + overlay + upload).
    - `routes/justification_signing.py` – client signing flows and callbacks.
  - Provide a small `routes/justification.py` that only imports and includes these sub-routers into the main FastAPI app (entry point = orchestrator only).

### 2. Oversized backend services

1. `app/services/crm.py` (~700 lines)
   - Mixes client CRUD, snapshots, notes, reminders, and report-related helpers.
   - Plan:
     - Introduce smaller service modules:
       - `services/crm_clients.py` – client CRUD and basic queries.
       - `services/crm_snapshots.py` – snapshot creation and retrieval.
       - `services/crm_notes.py` – notes.
       - `services/crm_reminders.py` – reminders.
     - Keep `crm.py` as a thin façade that re-exports functions or delegates to these modules, so routes do not break.

2. `app/services/justification_forms.py` (~600 lines)
   - Contains:
     - Data URL decoding, overlay generation, font registration.
     - Signature field detection and rectangle collection.
     - Signature application logic and form flattening.
   - Plan:
     - Extract generic PDF helpers into `services/pdf_utils.py` (or similar):
       - Overlay font registration.
       - Generic overlay creation.
       - Signature-rectangle collection helpers.
     - Keep justification-specific orchestration in `justification_forms.py` and simplify public surface.

3. `app/services/justification_advice.py` and `justification_packet.py`
   - `justification_advice.py` combines:
     - Jinja environment setup.
     - Static resources loading.
     - Client view model building.
     - HTML building + PDF generation, plus saving to disk.
   - `justification_packet.py` orchestrates packet generation from advice, B1, and kits.
   - Plan (medium term):
     - Extract a small `services/pdf_runtime.py` or `services/pdf_generation.py` to hold wkhtmltopdf lookup, temp file handling, and common PDF-generation utilities used by advice and others.
     - Keep advice-specific view-model logic in `justification_advice.py`.

### 3. Oversized frontend roots

1. `frontend/src/pages/justification/JustificationPageRoot.tsx` (~700 lines)
   - Holds view mode switching, data loading (clients, products, snapshots), and a lot of wiring between actions and components.
   - Plan:
     - Introduce dedicated hooks/helpers per concern, e.g.:
       - `useJustificationClientSelection` – managing selected client, filter, client details.
       - `useJustificationExistingProducts` – existing products state, selection, and CRUD wiring.
       - `useJustificationNewProducts` – new products and form instances.
       - `useJustificationReports` – actions for advice/B1/kits generation.
     - Keep `JustificationPageRoot` as a thin composition of these hooks and high-level layout.

2. `frontend/src/pages/crm/CrmPageRoot.tsx` (~650 lines)
   - Central place for CRM clients, snapshots, notes, and reminders.
   - Plan:
     - Similar to justification:
       - `useCrmClients` – client list/selection and create/new-client state.
       - `useCrmSnapshots` – snapshot handling and export actions.
       - `useCrmNotesReminders` – notes + reminders state and actions.
     - Entry component focuses on layout and orchestrating sub-hooks.

### 4. Repeated utility logic

- File-name sanitization and export-path utilities
  - Repeated patterns in `justification_advice.py`, `routes/justification.py`, and possibly packet services.
  - Plan:
    - Extract shared helpers into `app/utils/filepaths.py` or `app/utils/naming.py`.

- Date formatting
  - Already centralized in `frontend/src/utils/dateFormat.ts`, used by CRM and Justification UI.
  - Plan:
    - Keep all new date display/edit logic using these utilities only.
    - For backend-generated PDFs, ensure dates are formatted consistently in templates/services (already mostly DD/MM/YYYY).

### 5. Potentially unused or legacy code

- There are likely legacy helpers or old patterns in `app/services` and `frontend/src/pages/justification` from earlier iterations.
- Plan:
  - Add a later phase to run static tools (e.g., `vulture` for Python, TypeScript noUnusedLocals) to identify dead code.
  - For each candidate:
    - Confirm no imports or runtime references.
    - Move to a `legacy/` folder or delete only after manual confirmation.

## Phased Execution Plan

### Phase 0 – Safety & Baseline

- Keep existing automated checks:
  - Frontend: `npm run build` (TypeScript + bundler) – already runs clean.
  - Backend: add a quick syntax check step (e.g., `python -m compileall app`) before/after significant refactors.
- No behaviour changes in this phase beyond already-verified bug fixes.

### Phase 1 – Documentation & Inventory (this document)

- Maintain this `system_maintenance_plan.md` in `backend/docs` as the single source of truth for cleanup tasks.
- Update it when new weak points or refactors are identified.

### Phase 2 – Backend modularization (non-breaking)

1. Prepare router split for `app/routes/justification.py`:
   - Introduce new router modules (`justification_products`, `justification_documents`, `justification_signing`).
   - Move groups of endpoints without changing URL paths or response models.
   - Keep a thin `justification.py` that aggregates sub-routers.

2. Break down `app/services/crm.py` logically without changing the public API that routes import.

3. Extract PDF and path utility helpers into `app/utils` modules and refactor call sites.

### Phase 3 – Frontend modularization

1. Refactor `JustificationPageRoot.tsx`:
   - Extract custom hooks for client selection, existing products, new products, and report actions.
   - Ensure no business logic remains inline in the JSX tree beyond wiring.

2. Refactor `CrmPageRoot.tsx` similarly, keeping stateful logic in hooks and thin root components.

3. Ensure entry pages only initialize state and delegate to hooks/components, following your guideline.

### Phase 4 – Dead code and legacy cleanup

- Introduce static analysis steps (even if manual for now):
  - Python: run a tool like `vulture` or manual grep to find unreferenced functions/classes.
  - TypeScript: enable or review `noUnusedLocals`/`noUnusedParameters` where practical.
- For each candidate item:
  - Mark and review.
  - Remove only after confirming no usage.

### Phase 5 – Logging, errors, and DX

- Normalize logging patterns in backend services (e.g., reduce ad-hoc `[ADVICE-DEBUG]` logs or guard them behind a debug flag/env variable).
- Ensure consistent error messages and HTTP status codes across routers.
- Consider small helper utilities for recurring error patterns.

## Near-term Concrete Tasks

- [ ] Backend: design and implement non-breaking router split for `app/routes/justification.py`.
- [ ] Backend: introduce `app/utils/filepaths.py` and migrate repeated safe-name/path helpers.
- [ ] Backend: start extracting PDF-generation helpers into a shared utility module.
- [ ] Frontend: identify and extract at least one custom hook from `JustificationPageRoot.tsx`.
- [ ] Frontend: identify and extract at least one custom hook from `CrmPageRoot.tsx`.
- [ ] Tooling: add a lightweight backend syntax check command to the maintenance workflow.
