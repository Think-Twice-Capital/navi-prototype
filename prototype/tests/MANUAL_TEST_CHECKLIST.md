# NAVI Prototype - Manual Test Checklist

Run these tests before deploying any changes to the prototype.

## How to Use This Checklist

1. Open `prototype/index.html` in a browser
2. Go through each test case below
3. Mark with `[x]` when passing, `[ ]` when failing
4. If a test fails, note the issue in the "Notes" section

---

## 1. Navigation Tests

### Test 1.1: Bottom Tab Navigation
- [ ] Stream tab is highlighted by default
- [ ] Clicking "Espaços" shows Spaces view
- [ ] Clicking "Ações" shows Actions view
- [ ] Clicking "Pulse" shows Pulse view
- [ ] Clicking "AI" shows AI view
- [ ] Clicking "Stream" returns to Stream view
- [ ] Active tab is visually highlighted (blue background)
- [ ] Only one tab is active at a time

### Test 1.2: Compose Bar Visibility
- [ ] Compose bar is visible on Stream view
- [ ] Compose bar is hidden on Spaces view
- [ ] Compose bar is hidden on Actions view
- [ ] Compose bar is hidden on Pulse view
- [ ] Compose bar is hidden on AI view

### Test 1.3: Space Detail Navigation
- [ ] Clicking a space card opens detail view
- [ ] Back button returns to Spaces grid
- [ ] All 8 spaces are clickable

---

## 2. Message Sending Tests

### Test 2.1: Send a Message
1. Go to Stream view
2. Type "Preciso comprar presente pra Clara" in compose bar
3. Tap send button

**Expected:**
- [ ] Message appears at top of Stream
- [ ] Message has "Filhos" badge (AI detected "Clara")
- [ ] Input clears after sending
- [ ] Toast appears showing space assignment

### Test 2.2: AI Space Detection
Test these messages and verify correct space detection:

| Message | Expected Space |
|---------|---------------|
| "Tem que pagar o DARF" | Casa |
| "Preciso passar no mercado" | Casa |
| "Uniforme da Clarinha" | Filhos |
| "Reunião às 15h" | Trabalho |
| "Te amo muito" | Nós |
| "Vamos assistir Netflix?" | Lazer |
| "Consulta do médico" | Saúde |
| "Passagem pra Lisboa" | Viagem |
| "Transferência bancária" | Finanças |

- [ ] All messages detected correctly

### Test 2.3: Toast Behavior
- [ ] Toast slides up from bottom after sending
- [ ] Toast shows correct space icon and name
- [ ] Toast has "Mudar" button
- [ ] Toast auto-dismisses after ~3 seconds
- [ ] Tapping toast dismisses it immediately

---

## 3. Space Change Tests

### Test 3.1: Change Space Assignment
1. Send a message
2. When toast appears, tap "Mudar"

**Expected:**
- [ ] Space selector modal slides up
- [ ] All 8 spaces are shown in grid
- [ ] Current space is highlighted

3. Select a different space

**Expected:**
- [ ] Modal closes
- [ ] Message badge updates to new space
- [ ] Confirmation toast appears

---

## 4. Message Group Interaction Tests

### Test 4.1: Tap to Expand
1. Go to Stream view
2. Tap on a message group

**Expected:**
- [ ] Action bar slides in at bottom of card
- [ ] Card has slight elevation/shadow

### Test 4.2: Action Bar Content
For groups with "Pendente" status:
- [ ] Shows "Marcar como feito" button
- [ ] Shows "Responder" button

For groups with "Feito" status:
- [ ] Shows only "Responder" button

### Test 4.3: Collapse on Outside Tap
1. Expand a message group
2. Tap on a different message group

**Expected:**
- [ ] First group collapses
- [ ] Second group expands
- [ ] Only one group expanded at a time

### Test 4.4: Mark as Done
1. Expand a pending message group
2. Tap "Marcar como feito"

**Expected:**
- [ ] Status chip changes to "Feito"
- [ ] Button text changes to "Concluído"
- [ ] Group collapses
- [ ] Undo toast appears

### Test 4.5: Undo Mark as Done
1. After marking done, tap "Desfazer" on toast

**Expected:**
- [ ] Status reverts to original
- [ ] Button reverts to "Marcar como feito"
- [ ] Toast disappears

### Test 4.6: Quick Reply
1. Expand a message group
2. Tap "Responder"

**Expected:**
- [ ] Compose bar gets focus
- [ ] Space context badge appears in compose bar
- [ ] Placeholder shows "Responder em [Space]..."

---

## 5. Task Swipe Tests (Actions View)

### Test 5.1: Swipe Right to Complete
1. Go to Actions view
2. Find a task in "Minhas Tarefas"
3. Swipe right on the task card

**Expected:**
- [ ] Green background reveals during swipe
- [ ] "Feito" text visible on green background
- [ ] If swiped >100px, task completes
- [ ] Task slides out and disappears
- [ ] Undo toast appears

### Test 5.2: Swipe Cancel
1. Start swiping a task right
2. Release before 100px threshold

**Expected:**
- [ ] Task snaps back to original position
- [ ] Task is not completed

### Test 5.3: Undo Task Complete
1. Complete a task via swipe
2. Tap "Desfazer" on toast

**Expected:**
- [ ] Task reappears in original position
- [ ] Toast disappears

---

## 6. AI Card Swipe Tests (AI View)

### Test 6.1: Swipe Right to Save
1. Go to AI view
2. Swipe right on an AI suggestion card

**Expected:**
- [ ] Card slides out to right
- [ ] "Sugestão salva" toast appears
- [ ] Card is removed from view

### Test 6.2: Swipe Left to Dismiss
1. Go to AI view
2. Swipe left on an AI suggestion card

**Expected:**
- [ ] Card slides out to left
- [ ] Card fades out
- [ ] Card is removed from view

---

## 7. Visual Feedback Tests

### Test 7.1: Button States
- [ ] Send button has press animation
- [ ] Nav items have active/hover states
- [ ] Action buttons have hover states

### Test 7.2: Transitions
- [ ] View switches have fade animation
- [ ] Toast slides smoothly
- [ ] Modal slides up smoothly
- [ ] Message groups expand/collapse smoothly

---

## 8. Edge Cases

### Test 8.1: Empty Message
1. Leave compose input empty
2. Tap send

**Expected:**
- [ ] Nothing happens (no empty message created)

### Test 8.2: Rapid Tab Switching
1. Rapidly tap between different nav tabs

**Expected:**
- [ ] No visual glitches
- [ ] Correct view is shown
- [ ] No JavaScript errors (check console)

### Test 8.3: Multiple Undos
1. Complete multiple tasks quickly
2. Try to undo

**Expected:**
- [ ] Only most recent action can be undone
- [ ] Undo works correctly for that action

---

## Notes & Issues Found

| Test | Issue Description | Date |
|------|------------------|------|
|      |                  |      |
|      |                  |      |

---

## Version History

| Date | Tester | Pass Rate | Notes |
|------|--------|-----------|-------|
|      |        |           |       |

