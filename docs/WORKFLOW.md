# OutreachAI Workflow

## Complete workflow

```text
USER
  ↓
Send LinkedIn/company information
  ↓
Validate input
  ↓
Identify company/person
  ↓
Research using permitted information
  ↓
Normalize data
  ↓
Check duplicates
  ↓
AI analysis
  ↓
Identify opportunity
  ↓
Personalize
  ↓
Generate Email + LinkedIn
  ↓
User reviews
  ↓
User sends manually
  ↓
Mark as Sent
  ↓
SQLite + Excel
  ↓
Follow-up date
  ↓
Response?
  ├─ No → Follow-up
  └─ Yes → Replied → Interested? → Meeting / Closed
```

## Detailed stages

### 1. Find company

Identify a relevant company or professional.

### 2. Submit

Send a LinkedIn URL, company URL, name, or pasted information.

### 3. Research

Use only permitted/public/authorized information.

### 4. Understand

AI creates a concise profile.

### 5. Identify opportunity

Possible opportunities include internship, live project, mentorship, workshop, company visit, industry collaboration, and campus hiring.

### 6. Personalize

Use a verified company-specific detail and connect it to the student's objective.

### 7. Draft

Create email and LinkedIn versions.

### 8. Review

User reviews before sending.

### 9. Send

User manually sends externally.

### 10. Track

Record outreach in SQLite and Excel.

### 11. Follow up

Store and surface the follow-up date.

### 12. Record outcome

Replied, Interested, Meeting Scheduled, Not Interested, or Closed.

### 13. Analyze

Measure outreach volume, responses, interest, meetings, and follow-ups.
