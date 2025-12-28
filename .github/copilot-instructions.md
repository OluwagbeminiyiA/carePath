# CarePath Project Instructions

## Project Overview
CarePath is a Django-based API for hospital queue management. It uses Django REST Framework (DRF) for the API layer and `drf-spectacular` for documentation.

## Architecture & Core Patterns

### Models & Lifecycle
- **Library**: Uses `django-lifecycle` for model hooks.
- **Queue Logic**: The `Queue` model (`api/models.py`) contains critical business logic in `@hook` methods (`update_queue`, `delete_queue`) to automatically reorder queue numbers when a patient's status changes.
- **Constraints**: `Queue` enforces uniqueness on `hospital`, `queue_number`, and `time_joined`.

### Services & AI Integration
- **Library**: Uses `google-genai` (Google Gemini API) for AI features. **Do not use** the deprecated `google-generativeai` package.
- **Service Layer**: Encapsulate external API logic in `api/services.py` (e.g., `DrugValidityService`, `DrugAuthenticationService`).
- **Configuration**: API keys are managed via `python-decouple` (`config("GEMINI_API_KEY")`).

### API Views
- **Base Class**: Use `rest_framework.views.APIView` for granular control.
- **Documentation**: Every view method MUST be decorated with `@extend_schema` from `drf_spectacular.utils`.
- **File Uploads**: 
  - Use `parser_classes = (MultiPartParser, FormParser)`.
  - Explicitly define schema for file fields in `@extend_schema` to ensure Swagger UI renders a file picker:
    ```python
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {'file_field': {'type': 'string', 'format': 'binary'}},
            'required': ['file_field']
        }
    }
    ```
- **Caching**: Read-heavy endpoints (lists/details) use `@method_decorator(cache_page(60 * 60 * 2))` to cache responses for 2 hours.
- **Transactions**: Write operations involving queue position calculations (e.g., `JoinQueueView`, `QueueUpdateView`) MUST use `with transaction.atomic():` to ensure data integrity.

### Serializers
- **Computed Fields**: `HospitalSerializer` includes dynamic fields like `queue_count` and `estimated_waiting_time`.
- **Nested Representations**: `PatientDetailSerializer` returns the full `Hospital` object, not just the ID.

## Critical Workflows

### Development
- **Run Server**: `python manage.py runserver`
- **Environment**: Configuration is managed via `python-decouple` (`.env` file).
- **Database**: Default is SQLite (`db.sqlite3`).

### Testing
- **AI Mocking**: Tests for AI services (`api/tests.py`) must mock `google.genai.Client` using `unittest.mock` and `patch.dict('sys.modules', ...)` to avoid real API calls.
- **File Uploads**: Use `SimpleUploadedFile` and `BytesIO` to simulate image uploads in tests.

### Key Implementation Details
- **Queue Joining**: When a patient joins a queue (`JoinQueueView`), the system must lock the table rows (`select_for_update()`) to safely calculate the next `queue_number`.
- **Queue Updates**: Updating a patient's status triggers the `django-lifecycle` hooks to shift the queue. Do not manually reorder the queue in views; rely on the model hooks.
- **AI Analysis**: Returns raw JSON from the LLM and parses it. Handles `ImportError` for optional AI dependencies.

## Coding Standards
- **Imports**: Group imports by: Standard Library, Django, Third-party (DRF, google-genai, etc.), Local Apps.
- **Error Handling**: Return standard HTTP status codes (e.g., 400 for validation errors, 201 for creation). Wrap external API calls in try/except blocks.
- **Type Hinting**: Use type hints where possible, especially for utility functions.
