# Contributing to UrbanLens AI

Thanks for your interest in contributing! This document outlines how to get started.

## Getting started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Urban-Lens.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Commit and push: `git push origin feature/your-feature-name`
6. Open a pull request

## Development setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Code style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow the existing ESLint config
- **Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)

## Pull request process

1. Update documentation if your change affects public APIs or behavior
2. Add tests for new functionality
3. Ensure CI passes before requesting review
4. Link any related issues in your PR description

## Code of conduct

Be respectful and constructive. This is a civic-tech project — we're here to help communities.

## Questions?

Open an issue for discussion before starting large changes.
