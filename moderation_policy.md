# Content Rules & Moderation Policy Draft

## Core Philosophy
**"Critique Actions, Protect Safety"**
The platform adheres to a philosophy of unbridled expression regarding opinions, quality, and behavior, while strictly enforcing safety relative to physical harm, privacy, and legal defamation. We permit harsh language; we strictly forbid dangerous conduct.

---

## 1. Content Rules (The Red Lines)

### A. Violence & Physical Harm (Zero Tolerance)
*   **Prohibited**: Any incitement to violence, specific threats, or wishing physical harm or death upon individuals or groups. Encouraging self-harm is strictly banned.
*   **Allowed**: Expressing intense dislike, anger, or hatred towards a person's actions, work, or public persona.
*   **Context Rule**: *Intent to Harm*. Does the post call for *action*?
    *   ✅ "I hate [Entity] and hope they go bankrupt." (Wish for failure/non-physical harm)
    *   ❌ "I hope [Entity] gets hit by a car." (Wish for physical harm)
    *   ❌ "Someone needs to take [Entity] out." (Call to violence)

### B. Harassment & Private Information (Doxing)
*   **Prohibited**: Publishing non-public personally identifiable information (PII) such as home addresses, private phone numbers, or family details of non-public figures (**Doxing**). Directed campaigns to contact an individual off-platform (brigading).
*   **Allowed**: Discussion of public information, public social media posts, and professional history.
*   **Context Rule**: *Public vs. Private Interest*.
    *   ✅ Discussing a CEO's public salary or past failed ventures.
    *   ❌ Posting the CEO's home address or photos of their children.

### C. Defamation vs. Harsh Opinion
*   **Prohibited**: False claims of fact that can damage reputation (Libel).
    *   ❌ "[Person] stole money from the charity fund." (Factual claim requiring proof)
    *   ❌ "[Person] is a pedophile." (Unsubstantiated criminal accusation)
*   **Allowed**: Negative opinions, insults, and hyperbolic characterizations.
    *   ✅ "[Person] is a scam artist and a thief at heart." (Hyperbolic opinion on character)
    *   ✅ "[Person] is the worst executive in the industry and incompetent." (Subjective opinion on ability)

---

## 2. Contextual Nuance Guidelines (The "Is it Allowed?" Test)

The moderation team (and AI) applies the **"Statement of Feeling" vs. "Call to Action"** test.

| Scenario | Statement (Action) | Verdict | Reason |
| :--- | :--- | :--- | :--- |
| **Hatred** | "I hate [X] because they are a liar." | **ALLOWED** | Expression of opinion/feeling. |
| **Hatred** | "[X] deserves to die for lying." | **BANNED** | Glorification/wishing of death. |
| **Action** | "Everyone should stop buying [X]'s product." | **ALLOWED** | Call to boycott (commercial action). |
| **Action** | "Everyone should spam [X]'s personal email." | **BANNED** | Call to harassment (brigading). |
| **Critique** | "[X] looks like a slob in that suit." | **ALLOWED** | Harsh personal insult (subjective). |
| **Critique** | "[X] is a convicted felon." (If false) | **BANNED** | Defamation (factual claim). |
| **Critique** | "[X] is a convicted felon." (If true) | **ALLOWED** | Statement of public fact. |

---

## 3. Anonymous Moderation Strategy

Since the platform operates without user accounts, moderation relies on **Session Identity** and **Community Consensus**.

### A. Identification Without Accounts
1.  **Session Hashing**: Every post includes a hidden hash derived from IP + UserAgent + DailySalt. This allows moderators to ban a "source" temporarily without needing a persistent account.
2.  **Tripcodes (Optional)**: Users *may* use a secure tripcode if they wish to verify their own identity across posts, but it is not required for posting.

### B. The "Report & Hiding" Mechanism (Community Filter)
Since we allow harsh content, we cannot rely solely on AI.
1.  **Report Threshold**: If a post receives **N** reports (e.g., 5) for "Illegal Content" or "Doxing," it is auto-hidden immediately and queued for human review.
2.  **"Click to View" Blurring**: If a post is reported for "Offensive" (but not illegal), it is blurred. Users must click to reveal it. This protects the ecosystem from spam while not deleting controversial opinions.

### C. Admin Tools & Non-Deletion Policy
1.  **Red Warning Labels (No Deletion)**: Content is **never deleted**, even if it violates rules or is spam. Instead, violating posts are "blocked" from standard view and replaced with a **Red Warning Label** stating the reason (e.g., "Blocked: Incitement to Violence").
2.  **Searchable & Revealable**:
    *   Blocked posts remain in the database and are indexed.
    *   Users can specifically search for blocked content or click the warning label to reveal the original text.
    *   *Exception*: Content may only be hard-deleted if legally compelled by court order or severe illegality (e.g., CSAM), but platform policy is preservation.
3.  **Thread Locking**: If a specific topic spirals, the thread becomes read-only, but all posts remain visible (or labeled).
