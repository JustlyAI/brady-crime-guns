# Workbench

## Project Overview

This is a workspace for the Workbench project.

This is the central workstation for AIF Of Cousnel, our AI-driven law office that collaborates with top law firms on complex commercial litigation. Here, we are pioneering innovative partnerships and redefining legal practice by combining deep legal expertise, advanced software development, and cutting-edge AI systems. Our work is focused on seamlessly integrating these strengths to transform how law is practiced and delivered.

We are developing a litigation-focused AI agent designed to function as an elite junior associate in the Big Law tradition.

Our work in this project covers the full spectrum of software development, paired programming, and collaborative professional tasks. We focus on preserving and creating valuable artifacts, scripts, and reusable workflows. Our aim is to continuously transform each project into a repeatable and autonomous system.

We primarily use Claude Agent SDK >= 0.1.4+ for the project (with claude sonnet latest as the model).

The claude-agent-sdk-python package is available at https://github.com/anthropics/claude-agent-sdk-python.

Look for rules in the .cursor/rules directory.

See README.md at root for more information.

While reporting on implementation details is favored (in markdown), keep reports concise and to the point.

Ignore the following folders unless specifically requested:

- output/ (ignore the contents of this folder unless specifically requested)
- knowledge/ (ignore the contents of this folder unless specifically requested)
- sessions/ (ignore the contents of this folder unless specifically requested)
- .deprected/ (old and unused files)
- .notebooks/ (ignore the contents of this folder unless specifically requested)
- .pytest_cache/ or other cache directories (ignore the contents of this folder unless specifically requested)
  -.cursor/ (ignore the contents of this folder unless a file is passed to you to read)
  -.docs/ (ignore the contents of this folder unless a file is passed to you to read)
  -.plans/ (ignore the contents of this folder unless a file is passed to you to read)

I work on Mac M2 silicon using cursor/visual studio code. This impacts how Docker images are created (buildx) and other consequences you must consider.

## Project-Specific Guidelines

- Do not change existing model names in scripts (gpt-4o, gpt-4o-mini, o1-mini, o1-preview, claude-4-5-sonnet-20241022, etc.)
- Keep tests simple and executable without mocks
- Always import Python libraries at the top of the file

You work with a brilliant partner, Maite, a specialized legal assistant who is often available for legal-domain consultations at port 8003.
