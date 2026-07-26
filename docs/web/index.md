---
title: Web screening
description: Screen primary-study lists in a browser and save decisions to an Excel workbook.
tags:
- web
- screening
- systematic-review
---

# Web

MapwiseFox Web helps you screen a primary-study list in a browser. You upload an Excel workbook, review each record's evidence, and save include or exclude decisions back to that workbook.

The tool is useful during the study-selection stage of a Systematic Literature Review (SLR) or Systematic Mapping Study (SMS). It combines the FastAPI service and the React web interface into one application.

## What you can do

- Import an `.xlsx` primary-study list and choose its worksheet.
- Map workbook headers to the evidence fields shown during screening.
- Review titles, abstracts, authors, keywords, dates, and available source links.
- Include a record or exclude it with one or more reasons.
- Use an optional criteria file to show your inclusion and exclusion rules.
- See completion and remaining-record counts, then resume at the first undecided record.
- Delete a survey when you no longer need its workbook.

## Start screening

Follow [Screen a primary-study list](getting-started/usage.md) for a complete workflow. For local runs, deployment, and authentication settings, see [Operations and configuration](operations.md).

!!! warning
    Decisions are written to the uploaded workbook. Keep an original copy of your primary-study list before importing it.
