**

# 🧭 Full User & Admin Front-End Workflow (Final Functional Blueprint v2)

---

# 🧍‍♂️ USER FLOW

---

### 1️⃣ Landing Page (/)

Goal: Entry point for new and existing users.

User sees:

- Headline: “Your AI-Powered Career Growth Platform.”  

- Quick overview: Resume updater, auto job apply, skill gap analyzer, GitHub integration.  

- Buttons:  

- Start Now / Get Started → goes to authentication flow.  

- Learn More → scrolls to overview.  

---

### 2️⃣ Authentication Page (/auth)

Goal: Secure login/signup portal.

- Tabs: Sign In | Create Account  

- Options: Email & Password OR OAuth (Google / GitHub / LinkedIn).  

- After login:  

- New user → onboarding.  

- Existing user → dashboard.  

---

### 3️⃣ Onboarding Flow (/onboarding)

Goal: Collect user preferences, integrations, and keys.

Step 1: Profile Setup

- Name, Email, LinkedIn, GitHub username.  

Step 2: Career Questionnaire

- Roles/fields targeted (multi-select).  

- Minimum target LPA.  

- Preferred job locations (optional).  

Step 3: GitHub Integration

- Connect GitHub → fetch repositories.  

Step 4: API & Token Setup

- Enter Gemini AI API Key (required).  

- Optional: LinkedIn / Naukri / Indeed / Gmail tokens.  

Step 5: Review & Finish

- Summary of all details.  
  Button: “Finish & Go to Dashboard.”

✅ Redirects to /dashboard.

---

### 4️⃣ User Dashboard (/dashboard)

Goal: Central hub for user control and quick status.

Top Cards:

- Job Search Status (Active/Paused based on toggle)  

- Verified Certificates  

- Projects Synced  

- Resume Versions (x/10)  

- Skill Gap Alerts  

Navigation Sidebar:  
Dashboard, Projects, Resumes, Job Control, Reports, Notifications, Settings.

Actions:

- “Go to Projects”  

- “View Reports”  

- “Manage Job Search”  

---

### 5️⃣ Projects Page (/projects)

Goal: Manage GitHub integrations and video intros.

View:

- List of synced repositories.  

- Each row:  

- Repo name + link  

- AI-generated description  

- “Record / Upload Video” (iframe popup for 20–30 sec video)  

- Status (✅ Uploaded / ⚠️ Missing)  

Behavior:

- When a new project is detected → user gets notification: “New project found! Record intro video now.”  

- Option to regenerate AI description.  

---

### 6️⃣ Resume & Document Page (/resumes)

Goal: Manage resumes, tailoring, and documents.

Tabs:

1. AI Resume Builder (with limitations)  
- Can create up to 5–10 resume types (configurable limit).  

- Each resume tied to a specific role type.  

- Only text-level modifications allowed (e.g., changing wording, skills).  

- Resume automatically updated when new GitHub project is detected.  

- Generate → Preview → Download PDF.  

- Option: “Auto-tailor for next job search.”  
3. Certificates & Document Upload  
- Upload educational/experience certificates.  

- Status displayed: Pending / Verified / Rejected (based on admin action).  

---

### 7️⃣ Job Control Panel (/job-control)

Goal: Manage automation preferences.

What user sees:

- Toggles:  

- ✅ Start / Stop Job Search  

- ✅ Enable / Disable Auto-Apply  

- Dropdowns:  

- Select portals (LinkedIn, Naukri, Indeed)  

- Filter by Role, Location, Min LPA, Company Type  

- Button: “Save & Activate”  

(Note: ❌ Removed “real-time status indicator” — toggles themselves show active state.)

---

### 8️⃣ Reports Page (/reports)

Goal: View and receive job-related insights.

User sees:

- Application Summary Chart (daily/weekly).  

- Resume Performance Stats (success vs usage).  

- Skill Gap Analytics.  

- Export as CSV/PDF.  

Additional Feature:

- Reports are automatically emailed to the user daily or weekly.  

---

### 9️⃣ Notifications Page (/notifications)

Goal: Show all important updates.

Types:

- New GitHub project detected → “Record video”.  

- Certificate verification updates.  

- Skill gap insights.  

- Resume updates.  

- Job apply summaries.  

Actions:

- Mark read/unread.  

- Click → go to related page.  

---

### 🔟 Settings Page (/settings)

Goal: Manage preferences, integrations, and privacy.

Tabs:

1. Career Preferences  
- Change roles, target LPA, preferred locations.  
3. API Keys & Tokens  
- Update Gemini API Key.  

- Manage LinkedIn / Gmail / Naukri tokens.  
5. GitHub Integration  
- Reconnect GitHub account.  
7. Notifications & Privacy  
- Toggle email/push alerts.  
9. Account  
- Logout / Delete / Re-run onboarding.  

---

# 🧑‍💼 ADMIN FLOW

---

### 1️⃣ Admin Login Page (/admin/login)

Goal: Secure admin authentication.

- Email, Password (with 2FA optional).  

- On success → /admin/dashboard.  

---

### 2️⃣ Admin Dashboard (/admin/dashboard)

Goal: Overview of the entire system.

Top Metrics:

- Total Users  

- Active Job Searches  

- Pending Certificates  

- API Key Expiry Alerts  

Sidebar:  
Dashboard, Users, Control, Notifications, API Management, Reports.

---

### 3️⃣ User Management (/admin/users)

Goal: View and manage all users in one place.

List View:

- Name, Email, Target Role, Job Search Status, GitHub Linked, Verified Docs Count.  

- Actions:  

- Suspend / Activate  

- Open Resume & Activity Summary  

- Manage Certificates  

Certificate Management (Nested Route):

- Route: /admin/users/:userid/certificates  

- Table:  

- Document Type | Upload Date | OCR Extract | Status | Action  

- Buttons: Approve / Reject / View Document  

- Optionally add rejection notes.  

So now:

- Removed separate /admin/certificates route.  

- All certificate actions happen inside /admin/users/:userid/certificates.  

---

### 4️⃣ Control Mechanism (/admin/control)

Goal: Manage automation per user or globally.

Features:

- Search User → Pause / Resume / Stop All Job Searches.  

- Global “Emergency Stop” for all automations.  

- Activity log with timestamps.  

---

### 5️⃣ Notifications Management (/admin/notifications)

Goal: Send or track notifications to users.

Actions:

- Create new notification (to all users or specific ones).  

- View past notifications (GitHub video alerts, certificate results, API reminders).  

---

### 6️⃣ API Key Management (/admin/api-management)

Goal: Manage unofficial API keys dynamically.

UI Layout:

- Table listing APIs: LinkedIn, Naukri, Indeed, etc.  

- For each:  

- Current Key (masked)  

- Expiry Timer (3 days)  

- “Update Key” button → opens textbox for new key input.  

- Save → Key instantly refreshed system-wide.  

- Reminder setup for key expiry.  

---

### 7️⃣ Reports & Analytics (/admin/reports)

Goal: Platform-wide analytics.

Charts:

- Total Jobs Applied (per user / global).  

- Resume Versions & Success Rate.  

- Certificate Verification Statistics.  

Actions:

- Export CSV / PDF.  

- View daily or weekly summary.  

---

✅ Final Flow Summary (v2)

|              |                                                                              |                                                                    |
| ------------ | ---------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Area         | User                                                                         | Admin                                                              |
| Entry        | Landing → Auth → Onboarding                                                  | Admin Login                                                        |
| Main         | Dashboard (Projects, Resumes, Job Control, Reports, Notifications, Settings) | Dashboard (Users, Control, Notifications, API Management, Reports) |
| Resume       | Limit 5–10 types; auto-update when new GitHub project                        | Can view resume stats per user                                     |
| Certificates | Upload → Admin verifies                                                      | Verification under /admin/users/:userid/certificates               |
| Control      | Toggles for Start/Stop                                                       | Pause/Resume for users or globally                                 |
| API Mgmt     | Gemini key + integrations                                                    | Dynamic unofficial API update every 3 days                         |
| Reports      | Emailed + viewable                                                           | System-wide analytics                                              |

---

Would you like me to now convert this workflow into a clickable visual sitemap diagram (showing all pages, routes, and navigation arrows)?  
It would make it much easier to explain this to your dev/design team.

**
