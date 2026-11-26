# SSLG Obsidian Vault Design

**Date:** 2026-11-04  
**Status:** Approved design, pending written-spec review  
**Workspace:** SSLG MEMOS

## Purpose

Turn the SSLG document collection into a readable, activity-centered Obsidian vault while preserving every original Word and PDF record. A reader must be able to start at one homepage, follow an activity through its related records, browse by document type or date, and open the complete source document from every summary note.

The vault will also support later AI training and analysis by maintaining explicit, machine-readable relationships between each derivative summary and its unchanged source document. Generated summaries must never be confused with original source text.

## Current State

- The vault root contains 93 Word/PDF records: 74 DOCX files and 19 PDF files.
- Checksum analysis found 76 unique root Word/PDF files, meaning 17 redundant exact copies.
- Additional material already exists in `_DUPLICATES_TO_DELETE`; its contents will not be assumed to be exact duplicates without verification.
- Eight PNG images exist in `OM_SSLG_2026_001`.
- No SSLG Markdown notes or navigation structure exist yet.
- Obsidian Bases, backlinks, outgoing links, properties, Canvas, and other relevant core features are already enabled.
- `Scheduler_v1-main` is a separate application and is outside the SSLG record-organization scope.
- This workspace is not a git repository, so design and implementation artifacts cannot be committed to git here.

## Approved Decisions

1. Keep original documents unchanged and add linked Markdown notes rather than converting every document into Markdown.
2. Use an activity-centered primary structure, supplemented by document-type and chronological dashboards.
3. Archive superseded revisions and exact duplicates; delete nothing.
4. Give every logical record a compact summary note with its original document as the final and most prominent section.
5. Use native Obsidian features only; no third-party plugins are required.
6. Flag uncertain primary-version choices and uncertain relationships for review instead of guessing.

## Vault Architecture

```text
START HERE.md
01 Dashboards/
  Activity Dashboard.md
  Document Library.md
  Timeline.md
  Review Queue.md
  SSLG Records.base
02 Activities/
  Activity Name/
    Activity Name.md
    Notes/
      Record summary notes.md
    Sources/
      Original DOCX and PDF files
03 Governance/
  SSLG policies, committees, and internal memoranda
04 External Memoranda/
  National, division, and cluster references
05 General Records/
  Meetings and requests not tied to one activity
80 Assets/
  Images and supporting attachments
90 Archive/
  Revisions/
  Duplicates/
  Archive Index.md
99 Templates/
  Activity Template.md
  Record Template.md
Scheduler_v1-main/
  Existing separate application, unchanged
docs/superpowers/specs/
  Design and planning artifacts
```

Each activity has one hub note. Its related source documents live in that activity's `Sources` folder, and their summary notes live in `Notes`. Governance, external memoranda, and general records follow the same note-to-source pairing principle without being forced into an unrelated activity.

Dashboards are filtered views of notes and properties, not duplicate copies of records.

## Activity Hub Design

Each activity hub contains:

1. **At a glance:** activity title, date or date range, venue, status, organizers, and a short source-derived description.
2. **Activity trail:** proposal, meeting notices and letters, related memoranda, and completion report in reading order.
3. **Outcomes and follow-up:** outcomes, challenges, actions, and recommendations when present in the source documents.
4. **Related governance:** links to policies or memoranda that explicitly govern the activity.
5. **Original files:** direct access to the record notes and their original documents.
6. **Missing stages:** absent records or uncertain relationships identified clearly, never filled with invented content.

An activity trail connects records by documented titles, dates, subjects, and explicit references. Document numbering alone is not sufficient evidence for a relationship because related records can use different numbering sequences.

## Record Note Design

Each logical record receives one Markdown summary note with this reading order:

1. Title and document number
2. Prominent link to the parent activity or collection
3. At-a-glance metadata
4. Short source-derived summary
5. Key details relevant to the record type
6. Related records
7. Revision history and alternative current formats
8. **Original document** as the final section

The summary is derivative navigation content. It must be labeled as a summary and kept separate from quotations and the original attachment. Missing information remains blank or is marked `Not stated in source`; it is never inferred as fact.

### Source Attachment Rules

- Embed PDFs in the final **Original document** section for in-app reading.
- Attach DOCX files through a prominent direct Obsidian link because Obsidian does not natively preview DOCX files.
- When a logical record has both a current DOCX and a current PDF, keep one record note and present both in the final section. Label the editable source and signed/exported PDF accurately; do not create competing record notes merely for different formats.
- Preserve exact source filenames in metadata even if display titles are cleaned up.
- Store a vault-relative `source_path` so AI tooling can resolve the original file without relying on the summary title.
- Do not embed generated text inside the source documents or alter their formatting.

## Metadata

Record notes use consistent Obsidian properties:

- `type: record`
- `record_type`: proposal, completion-report, memorandum, meeting-notice, excuse-letter, request, or governance-policy
- `record_id`: exact document identifier when present
- `date`: ISO-formatted issuance date of the record
- `event_date`: ISO-formatted activity or meeting date when it differs from the issuance date
- `school_year`: for example, `2026-2027`
- `activity`: wikilink to the parent activity, when applicable
- `status`: draft, final, signed, reference, or needs-review
- `source_file`: exact source filename
- `source_path`: vault-relative path to the source
- `source_format`: DOCX or PDF
- `related`: wikilinks to related record notes
- `tags`: a small controlled set led by `sslg`

Activity hubs use `type: activity`, `start_date`, optional `end_date`, `school_year`, and `status` with values `planned`, `ongoing`, `completed`, or `needs-review`. Timeline views distinguish record issuance dates from activity or meeting dates.

For records with both DOCX and PDF representations, the note uses a structured list of source entries rather than pretending that the two files are unrelated or overwriting one source path with another.

## Navigation and Visual Design

`START HERE.md` is the main entry point and links to the activity dashboard, document library, timeline, governance collection, external memoranda, and review queue.

The visual system uses native Markdown and Obsidian elements:

- Consistent heading hierarchy
- Callouts for orientation, warnings, and review notes
- Compact tables for metadata and activity trails
- Wikilinks for navigation and backlinks
- Native Bases tables for filtering and sorting
- PDF embeds at the end of record notes

No decorative system should obscure the source documents or require a community plugin. The original document remains the most substantial resource in every record note.

## Primary Versions and Archive Rules

A primary logical record is selected using signed/official copies, explicit `revised` or `proofread` labels, document content, and coherent chronology. Filesystem modification time is supporting evidence, not sole proof that a version is authoritative.

- Superseded DOCX/PDF versions move to `90 Archive/Revisions` while retaining their original filenames.
- Verified byte-for-byte copies move to `90 Archive/Duplicates`.
- The pre-existing `_DUPLICATES_TO_DELETE` material moves into the Archive as preserved staging material; it is not deleted or automatically treated as verified duplicate content.
- `Archive Index.md` maps original paths to current paths, identifies the related primary record where known, and records SHA-256 checksums.
- If two versions conflict and neither can be selected responsibly, retain both, choose no silent winner, and place the logical record in the Review Queue.
- No move may overwrite an existing destination file.

## Relationship and Review Rules

Relationships must be supported by source evidence such as matching activity titles, explicit memorandum references, dates, or subjects. Uncertain links appear in `Review Queue.md` with the reason for uncertainty and links to the candidate records.

Typical review cases include:

- Conflicting memorandum numbers or dates across revisions
- A proposal and completion report whose relationship is plausible but not explicit
- Missing activity stages
- A current DOCX/PDF pair whose contents differ materially
- A file whose label suggests a revision but whose content indicates a different logical record

The Review Queue is part of the delivered structure, not a hidden implementation scratch area.

## Scope Boundaries

- Do not edit, rebuild, move, or reorganize `Scheduler_v1-main`.
- Do not delete any SSLG record, duplicate, revision, or pre-existing staging material.
- Do not rewrite official documents to fix apparent spelling, numbering, or formatting issues.
- Do not invent dates, relationships, outcomes, approvals, or version authority.
- Do not add community plugins or external services.
- Do not publish or upload the documents.

## Verification and Acceptance Criteria

The organization is complete only when all applicable checks pass:

1. **Preservation:** every original DOCX/PDF and supporting image is accounted for by path and checksum; source bytes are unchanged.
2. **No loss or overwrite:** baseline and final inventories reconcile, including archived material and the pre-existing duplicate-staging folder.
3. **Coverage:** every primary logical record has one summary note and every note resolves to its original source document or documents.
4. **Source placement:** the final section of every record note is **Original document**, with PDF embeds and DOCX attachment links as applicable.
5. **Link integrity:** all internal wikilinks, source links, embeds, and activity-trail links resolve within the vault.
6. **Relationship accuracy:** sampled activity trails match source titles, dates, subjects, and explicit references; uncertain cases appear in the Review Queue.
7. **Dashboard coverage:** activity, record-type, chronological, and needs-review views return the intended notes without including the Scheduler application.
8. **Template consistency:** new activity and record notes can be created from the templates with the same metadata and source-attachment structure.
9. **Obsidian rendering:** homepage, callouts, tables, PDF embeds, and Bases views are checked in Obsidian where app access is available. Any visual check that cannot be performed must be reported explicitly rather than claimed as successful.
10. **AI traceability:** a tool can use note metadata to locate the unchanged source file and distinguish derivative summaries from original material.

The resulting vault should let a new reader begin at `START HERE.md`, understand an activity as a connected sequence of records, and reach the complete original formatting with one final scroll or click.
