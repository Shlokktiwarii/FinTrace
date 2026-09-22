# ADR 0001: Use src Layout

## Status

Accepted

## Context

FinTrace is intended to be a production-style Python project.
The repository should separate source code from repository-level
files such as tests, scripts, documentation and configuration.

## Decision

Use the Python src layout:

src/
└── fintrace/

## Consequences

### Positive

- Prevents accidental imports from the repository root.
- Makes package installation behavior explicit.
- Separates application code from repository tooling.
- Provides a structure suitable for future packaging and deployment.

### Negative

- Slightly more verbose project structure.
- Developers must install the package in editable mode during local development.