"""Rewrite stiff phrases in every `say` line into the way a teacher actually talks (contractions). Only touches `say` fields."""
import re, json, glob, sys
RULES = [
 (r"\bLet us\b", "Let's"), (r"\blet us\b", "let's"), (r"\bdo not\b", "don't"), (r"\bDo not\b", "Don't"), (r"\bdoes not\b", "doesn't"), (r"\bDoes not\b", "Doesn't"),
 (r"\bis not\b", "isn't"), (r"\bIs not\b", "Isn't"), (r"\bare not\b", "aren't"), (r"\bcannot\b", "can't"), (r"\bCannot\b", "Can't"), (r"\bwill not\b", "won't"), (r"\bwould not\b", "wouldn't"),
 (r"\bdid not\b", "didn't"), (r"\bhave not\b", "haven't"), (r"\bwas not\b", "wasn't"), (r"\bwere not\b", "weren't"), (r"\bshould not\b", "shouldn't"),
 (r"\bit is\b", "it's"), (r"\bIt is\b", "It's"), (r"\bthat is\b", "that's"), (r"\bThat is\b", "That's"), (r"\bwe will\b", "we'll"), (r"\bWe will\b", "We'll"),
 (r"\bwe are\b", "we're"), (r"\bWe are\b", "We're"), (r"\bthey are\b", "they're"), (r"\bThey are\b", "They're"), (r"\bthere is\b", "there's"), (r"\bThere is\b", "There's"),
 (r"\bwhat is\b", "what's"), (r"\bWhat is\b", "What's"), (r"\bhere is\b", "here's"), (r"\bHere is\b", "Here's"), (r"\byou will\b", "you'll"), (r"\bYou will\b", "You'll"), (r"\bI will\b", "I'll"),
 (r"\bThat gives us\b", "That gives us"),
]
n = 0
for p in sorted(glob.glob("scripts/*.json")):
    s = open(p, encoding="utf-8").read(); js = json.loads(s)
    for sc in js["scenes"]:
        for b in sc["beats"]:
            t = b["say"]
            for a, r in RULES: t = re.sub(a, r, t)
            if t != b["say"]: n += 1; b["say"] = t
    open(p, "w", encoding="utf-8").write(json.dumps(js, ensure_ascii=False, indent=1))
print("lines changed:", n)
