import json
REPO = r"C:\Users\Laptop\op"
groups = [  # (section_label, parts, [(id, title)])
 ("Math · Algebra", 3, [("m-alg-lin1","Linear Equations in One Variable"),("m-alg-linfunc","Linear Functions"),("m-alg-lin2","Linear Equations in Two Variables"),("m-alg-systems","Systems of Two Linear Equations"),("m-alg-ineq","Linear Inequalities")]),
 ("Math · Advanced Math", 3, [("m-adv-equiv","Equivalent Expressions"),("m-adv-nonlin-eq","Nonlinear Equations and Systems"),("m-adv-nonlin-func","Nonlinear Functions")]),
 ("Math · Problem-Solving and Data Analysis", 3, [("m-psda-ratios","Ratios, Rates, Proportions, Units"),("m-psda-percent","Percentages"),("m-psda-onevar","One-Variable Data"),("m-psda-twovar","Two-Variable Data"),("m-psda-prob","Probability and Conditional Probability"),("m-psda-inference","Inference from Sample Statistics, Margin of Error"),("m-psda-claims","Evaluating Statistical Claims")]),
 ("Math · Geometry and Trigonometry", 3, [("m-geo-area","Area and Volume"),("m-geo-lines","Lines, Angles, and Triangles"),("m-geo-trig","Right Triangles and Trigonometry"),("m-geo-circles","Circles")]),
 ("Reading and Writing", 2, [("rw-ii-central","Central Ideas and Details"),("rw-ii-evidence","Command of Evidence"),("rw-ii-inference","Inferences"),("rw-cs-words","Words in Context"),("rw-cs-structure","Text Structure and Purpose"),("rw-cs-crosstext","Cross-Text Connections"),("rw-ei-transitions","Transitions"),("rw-ei-synthesis","Rhetorical Synthesis"),("rw-sec-boundaries","Boundaries (punctuation, sentence structure)"),("rw-sec-form","Form, Structure, and Sense (grammar)")]),
]
desmos = [("graphing-basics","Graphing basics"),("inequalities","Inequalities"),("intersections-and-systems","Intersections and systems"),("quadratics-vertex-roots","Vertex and roots of a quadratic"),("sliders-for-unknown-constants","Sliders for unknown constants"),("solving-any-equation-by-graphing","Solving any equation by graphing"),("statistics-mean-median","Mean and median"),("tables-and-regression","Tables and regression")]
items = [
 dict(id="about-the-sat_v1", skill="about-the-sat", part=1, title="How the SAT is built and scored", section_label="Getting started", lesson=REPO + r"\src\app\(app)\course\about-the-sat\page.tsx", kind="intro"),
 dict(id="about-the-sat_v2", skill="about-the-sat", part=2, title="How to study with OpenPrep", section_label="Getting started", lesson=REPO + r"\src\app\(app)\course\about-the-sat\page.tsx", kind="intro"),
]
for slug, t in desmos:
    items.append(dict(id=f"desmos-{slug}_v1", skill=f"desmos-{slug}", part=1, title=t, section_label="Desmos basics", lesson=REPO + rf"\content\desmos\{slug}.md", kind="desmos"))
for label, parts, skills in groups:
    for sid, t in skills:
        for p in range(1, parts + 1):
            items.append(dict(id=f"{sid}_v{p}", skill=sid, part=p, title=t, section_label=label, lesson=REPO + rf"\content\lessons\{sid}.md", kind="rw" if sid.startswith("rw-") else "math"))
for i, it in enumerate(items): it["next"] = items[i + 1]["title"] if i + 1 < len(items) else "this was the final topic"
json.dump(items, open("manifest.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False); print(len(items), "videos")
