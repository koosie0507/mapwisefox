---
title: Screen a primary-study list
description: Import an Excel primary-study list, make screening decisions, and resume your survey.
tags:
- web
- excel
- screening
---

# Screen a primary-study list

You can use MapwiseFox Web to screen an Excel primary-study list one record at a time. This workflow prepares a workbook, imports it, records decisions, and resumes incomplete work.

## Prepare the workbook

Create an Excel `.xlsx` workbook with one row per primary study. The first non-empty row in the worksheet is the header row. Headers must be non-empty and unique. Do not leave blank rows between records.

At minimum, provide `title` and `authors` columns. MapwiseFox can also show these fields when matching columns are present: `doi`, `abstract`, `keywords`, `publicationDate`, `publicationVenue`, `url`, `hasPdf`, `pdfUrl`, and `referencingEvidence`.

Use the standard field names as headers, or map a standard field to your own header during import. For example, map `publicationDate` to `Year` and `publicationVenue` to `Source title`.

The application creates screening columns when they are absent. By default, they are `include` and `exclude_reason`. Your operator can change these names with `MWF_WEB_DECISION_COLUMN` and `MWF_WEB_EXCLUSION_REASON_COLUMN` before you import the workbook.

| title | authors | abstract | Year | Source title |
| --- | --- | --- | --- | --- |
| A study of example systems | A. Researcher; B. Reviewer | An abstract for the study. | 2025 | Journal of Examples |

!!! note
    Existing decision cells may contain `include`, `exclude`, or be blank. A blank decision is undecided. Any other value prevents import.

## Optionally define criteria

Upload a JSON selection-criteria file with the workbook to show your rules in the screening panel. Each criterion has a short `label`, which is saved as an exclusion reason, and a reader-facing `description`.

```json title="selection-criteria.json"
{
  "review_topic": "example systems",
  "additional_context": "Assess the title and abstract.",
  "inclusion_criteria": [
    {"label": "in scope", "description": "Studies an example system."}
  ],
  "exclusion_criteria": [
    {"label": "secondary study", "description": "Is a review or mapping study."}
  ]
}
```

If you do not upload criteria, you can still include a record. You can exclude a record by clearing the default inclusion criterion. An exclusion always needs at least one reason.

## Import the survey

1. Open the web application and select **Import a survey**.
2. Choose the `.xlsx` workbook.
3. Optionally choose `selection-criteria.json`.
4. Enter a **Worksheet name** when the primary-study list is not on the first worksheet.
5. Under **Field mappings**, add a mapping for every workbook header that differs from a standard field name.
6. Select **Upload**.

The survey list shows the selected worksheet, completed records, and remaining records. Select the pencil icon for the survey to begin.

## Review and decide

The screening view shows a record's title, bibliographic details, abstract, keywords, and links when available. Check or clear the inclusion and exclusion criteria, then select **Include** or **Exclude** to save the decision.

An exclusion saves its selected criterion labels in the exclusion-reason column. An inclusion writes `include` to the decision column and clears its exclusion reasons. After saving, the view moves to the next undecided record when one exists.

Use the navigation controls to move to the first, previous, next, or last record. Use the dashed-circle control for the first undecided record and the fast-forward control for the next undecided record. You can also enter a zero-based record index in **Go to**.

## Track and resume work

Return to the survey list at any time. Its progress bar shows completed records and the number remaining. When you reopen a survey without a record index, MapwiseFox opens the first undecided record. This lets you resume screening after closing the browser or restarting the service.

The imported workbook retains your decisions. Back up or export that workbook from the configured uploads directory when you need a copy outside the application.

## Delete a survey

On the survey list, select the trash icon, then confirm **Yes**. This deletes the uploaded workbook and its MapwiseFox survey metadata.

!!! warning
    Deleting a survey is permanent in the application. It does not restore the workbook to its state before screening.
