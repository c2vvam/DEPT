# GEMINI General Guidelines

## Guidelines
(Always keep the following in mind and act accordingly.)

- [MANDATORY] Before starting any coding task, you MUST use the `view_file` tool to read the contents of security.md and any other rules in the `.agents/` folder, and apply them strictly.
- If you need to make extensive changes, always ask the human for permission before proceeding.
- If my request is unclear, please don't infer or execute it. Instead, ask me to clarify what I meant.
- **never try to read .env file**

## Codebase Structure

- Explore the directory directly to understand its structure before starting work.

## Security

- Please refer to (.agents/security.md) for security guidelines.
- In case of folder rule conflicts, the order of priority is security.md -> GEMINI.md -> general conventions.

## Code Style

- Python: Write code as if `mypy --strict` is enabled—annotate types (both argument and return types) for all function signatures, avoid using `Any`, and use `TYPE_CHECKING` for type-only references. Do not run `mypy` locally (it is too slow); the CI runs checks on every PR. While the current project-wide configuration is not fully in strict mode, all new code must comply with this.
- Python Imports: Keep imports at the module's top level, not inside functions, methods, or conditional statements. Inline imports hide dependency structures during static analysis, degrade hot path performance due to repeated lookups, and mask circular reference issues instead of resolving them. Deferring imports is permitted only to:
  1. Break an absolutely unavoidable circular reference (prefer restructuring the code first).
  2. Reference types under `TYPE_CHECKING`.
  3. Exclude heavy or optional dependencies from the import path so they load only when executed. In this case, add a comment on the import line with a valid justification.
  Do not unconditionally ignore rules without reason.
- Frontend: TypeScript is mandatory. Always declare explicit return types.
- Frontend: All buttons or form submissions that trigger network requests must prevent duplicate submissions.
- CSS: Use Tailwind utility classes instead of inline styles.
- Error Handling: Explicitly handle errors by utilizing typed errors.
- Naming Conventions: Use descriptive names. Use camelCase for JS/TS and snake_case for Python.
- Comments: Keep comments short or single-line by default. Explain *why* something was done rather than *what* it does. Only write them if a future reader would be confused without access to this PR or chat history.
- Comments: Do not record change history or chat context within the code—avoid notes like "previously did X, but now doing Y," "changed per request/PR," "the reason is...," or "AI:"/"agent:". This information belongs in commit messages and PR descriptions.
- Comments: When refactoring or moving code, preserve existing comments unless they become completely obsolete.
- Python Testing: Do not add doc comments (docstrings).
- Python: Do not create empty `__init__.py` files.
- Markdown: Use semantic line breaks. Do not use hard wrapping.

## Consistent Code Structure

- Organize code using consistent rules for each file.
- Check for unused variables and consider the overall quality of the code.

## Domain-Driven App Separation

- Avoid putting all features into a single, massive app. It is ideal to create multiple small apps based on functional units and keep coupling low enough for each app to operate independently. This makes it easier to separate specific features into microservices or reuse the code later.

## git

Git-related tasks will be handled directly by the human, so you do not need to do anything related to Git.