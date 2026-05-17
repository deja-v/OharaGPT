# RAG Evaluation Questions

These 10 questions were chosen because a plain LLM (no retrieval) either hallucinates
the answer or gives a vague/incorrect response. Run each twice:

```
# Without RAG (comment out the retrieve node temporarily)
python backend/main.py "<question>"

# With RAG (normal run)
python backend/main.py "<question>"
```

Score each RAG answer: ✅ correct + cited  |  ⚠️ partially correct  |  ❌ wrong/uncited

Target: ≥ 7/10 answers correct and cited before moving on.

---

## Questions

### Q1 — Specific bounty (minor character)
**Question:** What is Dorry's exact bounty?

**Why LLM hallucinates:** Dorry is a giant from Little Garden. His exact bounty
(100,000,000 Berries) is rarely in LLM training data at this precision.

**Expected answer with RAG:** 100,000,000 Berries (cited from the bounty or Dorry wiki page)

---

### Q2 — Exact bounty after timeskip
**Question:** What was Roronoa Zoro's bounty after the Wano arc?

**Why LLM hallucinates:** Post-Wano bounties were set in recent chapters (1058).
LLMs often give pre-Wano or wrong values.

**Expected answer with RAG:** 1,111,000,000 Berries (cited from zoro page)

---

### Q3 — Specific devil fruit model
**Question:** What is the official name of Luffy's devil fruit?

**Why LLM hallucinates:** For years it was believed to be Gomu Gomu no Mi; the reveal
of its true name (Hito Hito no Mi, Model: Nika) is recent and often confused.

**Expected answer with RAG:** Hito Hito no Mi, Model: Nika (cited from nika_fruit or luffy page)

---

### Q4 — Void Century detail
**Question:** What happened during the Void Century?

**Why LLM hallucinates:** The Void Century is intentionally mysterious in canon;
LLMs often fabricate specifics. A RAG answer should note what IS confirmed
(it was 100 years of erased history, roughly 800–900 years ago) vs. what is unconfirmed.

**Expected answer with RAG:** Confirmed facts from void_century page with explicit uncertainty where canon is silent.

---

### Q5 — Ancient Weapon
**Question:** What are the three Ancient Weapons and who is Poseidon?

**Why LLM hallucinates:** LLMs often misattribute which character is Poseidon or confuse the weapons.

**Expected answer with RAG:** Pluton, Poseidon, Uranus; Poseidon is Shirahoshi (cited from ancient_weapons page)

---

### Q6 — Specific chapter event
**Question:** What promise did Shanks make when he gave Luffy his hat?

**Why LLM hallucinates:** The exact wording and context ("Return it to me when you've become a great pirate")
are often paraphrased incorrectly.

**Expected answer with RAG:** Cited from luffy or shanks page.

---

### Q7 — Haki detail
**Question:** What is the advanced form of Conqueror's Haki introduced in Wano?

**Why LLM hallucinates:** "Coating" weapons with Conqueror's Haki is a recent Wano reveal;
LLMs often omit it or describe it incorrectly.

**Expected answer with RAG:** Coating one's body/weapons with Conqueror's Haki (cited from conquerors_haki page)

---

### Q8 — World Government structure
**Question:** Who are the Five Elders and what is their role?

**Why LLM hallucinates:** Their individual names and their recent reveal as having
devil fruits are frequently hallucinated or conflated.

**Expected answer with RAG:** Cited from five_elders page with their roles and any confirmed names.

---

### Q9 — Law's devil fruit ability
**Question:** What is the "immortality operation" that Trafalgar Law's devil fruit can perform?

**Why LLM hallucinates:** The Perennial Youth Operation is a specific technique with
specific conditions (requires the user's lifespan as payment); details are often wrong.

**Expected answer with RAG:** Cited from ope_ope or law page.

---

### Q10 — Joy Boy / Nika connection
**Question:** What is the relationship between Joy Boy, the Sun God Nika, and Luffy?

**Why LLM hallucinates:** This is a Final Saga reveal; LLMs frequently muddle the
timeline or overstate what is confirmed canon.

**Expected answer with RAG:** Cited from joy_boy and nika_fruit pages, distinguishing
confirmed facts from interpretation.

---

## Scoring log

| # | Without RAG | With RAG | Notes |
|---|-------------|----------|-------|
| Q1 | | | |
| Q2 | | | |
| Q3 | | | |
| Q4 | | | |
| Q5 | | | |
| Q6 | | | |
| Q7 | | | |
| Q8 | | | |
| Q9 | | | |
| Q10 | | | |
| **Total** | **/10** | **/10** | |
