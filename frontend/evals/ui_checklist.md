# Phase 5 UI Checklist

## Core Chat
- [ ] Enter submits question
- [ ] User message appears immediately (before response starts)
- [ ] Tokens stream in real-time character by character
- [ ] Streaming cursor dot visible during streaming
- [ ] Input disabled while streaming
- [ ] Input re-enables after streaming completes

## Design (Non-Generic)
- [ ] Assistant bubbles have NO left blue border stripe
- [ ] Assistant bubbles show gold L-bracket in top-left corner
- [ ] Logo renders as SVG skull only — no □□ glyph
- [ ] Background is near-black (#080E18), not teal-blue
- [ ] Source chip borders are dashed at rest

## Sources
- [ ] Source chips appear after streaming completes (staggered)
- [ ] Each chip: `⚓ {source} — {heading}`
- [ ] Chip border becomes solid gold on hover

## Theory Mode
- [ ] "Theory: Shanks is a spy" routes to theory mode
- [ ] "⚡ Theory" tag appears inside user bubble
- [ ] Verdict stamp appears on assistant bubble (octagon, rotated)
- [ ] SUPPORTED = green, CONTRADICTED = red, INSUFFICIENT = gray
- [ ] Stamp animates in with spring bounce

## Multi-Turn
- [ ] Follow-up question returns contextually relevant answer
- [ ] Refresh does NOT clear conversation (sessionStorage thread_id)
- [ ] "NEW LOG" button clears messages and starts fresh thread

## Error States
- [ ] Stop backend → connection error banner slides in from top
- [ ] Banner has dismiss ✕ button
- [ ] Restart backend → new messages work again

All checkboxes must be ticked before Phase 6.
Date completed: ___________
