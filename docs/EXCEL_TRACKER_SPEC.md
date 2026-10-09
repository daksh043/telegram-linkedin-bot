# Excel Tracker Specification

## Workbook

`data/Outreach_Tracker.xlsx`

## Outreach Tracker

| Column | Description |
|---|---|
| ID | Unique outreach ID |
| Company | Company name |
| Contact Person | Person contacted |
| Role | Contact role |
| LinkedIn | LinkedIn URL |
| Email | Contact email |
| Industry | Company industry |
| Opportunity | Internship/project/etc. |
| Personalization Angle | Company-specific reason |
| Message | Drafted/sent message |
| Channel | Email/LinkedIn |
| Status | Current status |
| Date Added | Creation date |
| Date Contacted | Sent date |
| Follow-up Date | Planned follow-up |
| Response | Response summary |
| Notes | Additional notes |

## Status

```text
Not Contacted
Drafted
Sent
Replied
Interested
Follow-up
Meeting Scheduled
Not Interested
Closed
```

## Contacts

`Contact ID`, `Company ID`, `Company`, `Name`, `Role`, `LinkedIn`, `Email`, `Notes`

## Dashboard

`Total Companies`, `Total Contacts`, `Drafted`, `Sent`, `Replied`, `Interested`, `Meetings`, `Follow-ups`, `Not Interested`, `Closed`, `Response Rate`, `Interest Rate`

## Settings

`Student Name`, `College`, `Student Role`, `Default Follow-up Days`, `Last Updated`

SQLite remains the primary source of truth. Excel is the human-friendly tracker/export.
