#!/usr/bin/env python3
"""
=============================================================================
  PPE Report Generator — Supervised Personal Project (المشروع الشخصي المؤطر)
  CRMEF Casablanca-Settat | Computer Science Department
  Author: Mohamed HOUSNI
=============================================================================

  A simple Python CLI tool that takes a student's project data (from a JSON
  file or interactive prompts) and sends it to any OpenAI-compatible API
  (OpenAI, OpenRouter, Google AI Studio, local models, etc.) to generate
  a complete 30-page defense-ready final report.

  Usage:
    1. Install dependency:   pip install openai
    2. Set your API key:     export API_KEY="sk-..."
    3. Run interactively:    python generate_report.py
    4. Run from JSON file:   python generate_report.py --input student_data.json
    5. Run with provider:    python generate_report.py --provider openrouter --model google/gemini-2.5-flash

  Supported providers:
    - openai       (default, api.openai.com)
    - openrouter   (openrouter.ai)
    - aistudio     (generativelanguage.googleapis.com)
    - custom       (set --base-url manually)
=============================================================================
"""

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed.")
    print("Run:  pip install openai")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# PROVIDER CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "google/gemini-3.1-flash-lite-preview",
        "env_key": "OPENROUTER_API_KEY",
    },
    "aistudio": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-3.1-flash-lite-preview",
        "env_key": "GOOGLE_API_KEY",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — THE MASTER PROMPT
# ═══════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = textwrap.dedent("""\
You are an expert academic writer and educational project consultant specializing
in Moroccan teacher-training programs. You will generate a complete, defense-ready
Supervised Personal Project (المشروع الشخصي المؤطر) final report for a trainee at
the Centre Regional des Metiers de l'Education et de la Formation (CRMEF) —
Casablanca-Settat Region, Computer Science Department.

This project is governed by the Management Guide for Qualifying Training 2025-2026.
It is NOT Action Research — it must focus strictly on practical innovation, renewal,
and the delivery of actionable solutions to real educational/pedagogical problems.

OUTPUT SPECIFICATIONS:
- Maximum 30 pages (excluding cover page, table of contents, references, appendices)
- Professional academic language suitable for a CRMEF defense
- Include tables, figures, and charts where they strengthen the presentation
- Every claim must be grounded in the data provided or properly referenced
- Write in the language specified by the user (Arabic or French ONLY)

MANDATORY REPORT STRUCTURE (exactly in this order):

1. Cover Page (صفحة الغلاف / Page de Couverture)
   - المركز الجهوي لمهن التربية والتكوين — جهة الدار البيضاء سطات
   - المملكة المغربية — وزارة التربية الوطنية والتعليم الأولي والرياضة
   - مسلك تأهيل أطر هيئة التدريس
   - Specialization, Project title, Trainee name, Supervisor, Committee, Season

2. Table of Contents (فهرس المحتويات / Table des Matières)

3. General Introduction (مقدمة عامة / Introduction Générale)
   - Educational context, project title, general idea, objectives, scope
   - Objective motives (field observations, institutional needs)
   - Subjective motives (personal conviction, professional interest)
   - Report structure outline

4. Topic Definition & Importance (تحديد الموضوع وأهميته / Détermination du Sujet)
   - Precise definition of the educational problem
   - Scientific and educational significance
   - Operational definitions of key terms

5. Methodology & Implementation Plan (المنهجية وخطة العمل / Méthodologie)
   5.1 Theoretical/institutional references
   5.2 Tools and instruments used
   5.3 Implementation stages mapped to the 8 official stages:
       1) Diagnosis & topic selection
       2) Data collection
       3) Drafting the project plan
       4) Interim implementation & developmental evaluation
       5) Drafting results
       6) Reading & analyzing results
       7) Recommendations & limitations
       8) Writing the final report
   5.4 Detailed action plan table with columns:
       Stage | Activities | Target group | Stakeholders | Resources | Timeline | Expected results

6. Results (النتائج / Résultats)
   - Actual data, tables, charts, before/after comparisons
   - Factual and objective — no interpretation

7. Analysis & Interpretation (تحليل النتائج / Analyse et Interprétation)
   - Detailed breakdown, patterns, link to objectives

8. Discussion (مناقشة النتائج / Discussion des Résultats)
   - Achieved vs. initial objectives
   - Obstacles and how they were overcome
   - Suggestions for improvement

9. Conclusions & Recommendations (الخلاصات والتوصيات / Conclusions)
   - Final deductions, actionable recommendations

10. Summary & Lessons Learned (الحصيلة / Bilan)
    - Main goals and results review
    - Personal and professional growth
    - Future perspectives

11. References (المصادر والمراجع / Sources et Références)
    - Full bibliographic documentation, APA style

12. Appendices (الملاحق / Annexes)
    - Supplementary materials, numbered and titled

QUALITY STANDARDS:
- PRACTICAL INNOVATION FOCUS: What was BUILT, TESTED, DELIVERED
- COHERENCE: Seamless problem→objectives→methodology→results→conclusions thread
- EVIDENCE-BASED: No fabricated data. Use [DONNÉES À COMPLÉTER] for missing data
- PAGE DISCIPLINE: Core content (sections 3-10) within 25-28 pages
- DEFENSE-READY: Supports a 15-20 minute oral presentation

Generate the COMPLETE report in one pass. Use [DONNÉES À COMPLÉTER: ...] for missing info.
""")


# ═══════════════════════════════════════════════════════════════════════════
# INTERACTIVE DATA COLLECTION
# ═══════════════════════════════════════════════════════════════════════════

def collect_data_interactive() -> dict:
    """Collect project data from the user interactively."""

    print("\n" + "=" * 70)
    print("  PPE REPORT GENERATOR — Data Collection")
    print("  المشروع الشخصي المؤطر — جمع المعطيات")
    print("=" * 70)

    def ask(prompt: str, required: bool = True) -> str:
        while True:
            value = input(f"\n  {prompt}\n  > ").strip()
            if value or not required:
                return value
            print("  ⚠ This field is required. Please provide a value.")

    def ask_long(prompt: str, required: bool = True) -> str:
        print(f"\n  {prompt}")
        print("  (Type your text. Enter an empty line to finish.)")
        lines = []
        while True:
            line = input("  > ")
            if line == "":
                break
            lines.append(line)
        value = "\n".join(lines).strip()
        if required and not value:
            print("  ⚠ This field is required.")
            return ask_long(prompt, required)
        return value

    data = {}

    # --- Section 1: Identification ---
    print("\n" + "-" * 50)
    print("  SECTION 1: Project Identification")
    print("-" * 50)

    data["language"] = ask("Report language (french / arabic):")
    data["full_name"] = ask("Full name (الإسم والنسب):")
    data["specialization"] = ask("Specialization (التخصص):")
    data["project_title"] = ask("Project title (عنوان المشروع):")
    data["target_group"] = ask("Target group (الفئة المستهدفة):")
    data["supervisor"] = ask("Supervisor name (الأستاذ المؤطر):")
    data["committee"] = ask("Committee members (لجنة المناقشة):", required=False)
    data["season"] = ask("Training season (الموسم التكويني) [default: 2025-2026]:", required=False) or "2025-2026"

    # --- Section 2: Description ---
    print("\n" + "-" * 50)
    print("  SECTION 2: Project Description")
    print("-" * 50)

    data["general_context"] = ask_long("General context (السياق العام):")
    data["objective_motives"] = ask_long("Objective motives (الدوافع الموضوعية):")
    data["subjective_motives"] = ask_long("Subjective motives (الدوافع الذاتية):")
    data["educational_importance"] = ask_long("Educational importance (الأهمية التربوية):")
    data["scope_dimensions"] = ask_long("Scope & dimensions (مجال وأبعاد المشروع):")
    data["objectives"] = ask_long("Project objectives (أهداف المشروع):")

    # --- Section 3: Methodology ---
    print("\n" + "-" * 50)
    print("  SECTION 3: Methodological Plan")
    print("-" * 50)

    data["methodology_stages"] = ask_long("Methodological stages (المراحل المنهجية):")
    data["expected_results"] = ask_long("Expected results (النتائج المنتظرة):")
    data["expected_product"] = ask_long("Expected product (المنتوج المنتظر):")

    # --- Section 4: Implementation ---
    print("\n" + "-" * 50)
    print("  SECTION 4: Implementation & Results")
    print("-" * 50)

    data["tools_used"] = ask_long("Tools & instruments used:", required=False)
    data["activities_conducted"] = ask_long("Actual activities conducted:", required=False)
    data["raw_results"] = ask_long("Raw results / data:", required=False)
    data["challenges"] = ask_long("Challenges & obstacles:", required=False)
    data["lessons_learned"] = ask_long("Personal & professional lessons learned:", required=False)
    data["references"] = ask_long("Sources & references:", required=False)
    data["appendices"] = ask_long("Appendices content description:", required=False)

    return data


def load_data_from_json(filepath: str) -> dict:
    """Load project data from a JSON file."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Loaded project data from: {filepath}")
    return data


# ═══════════════════════════════════════════════════════════════════════════
# BUILD THE USER MESSAGE FROM COLLECTED DATA
# ═══════════════════════════════════════════════════════════════════════════

def build_user_message(data: dict) -> str:
    """Build the user message containing all project data."""

    lang = data.get("language", "french").lower()
    lang_instruction = "Write the entire report in FRENCH." if "fr" in lang else "Write the entire report in ARABIC."

    msg = f"""{lang_instruction}

PROJECT DATA — ALL INFORMATION PROVIDED BELOW:

=== PROJECT IDENTIFICATION ===
Full Name: {data.get('full_name', '[A COMPLETER]')}
Specialization: {data.get('specialization', '[A COMPLETER]')}
Project Title: {data.get('project_title', '[A COMPLETER]')}
Target Group: {data.get('target_group', '[A COMPLETER]')}
Supervisor: {data.get('supervisor', '[A COMPLETER]')}
Committee Members: {data.get('committee', '[A COMPLETER]')}
Training Season: {data.get('season', '2025-2026')}

=== PROJECT DESCRIPTION ===
General Context:
{data.get('general_context', '[A COMPLETER]')}

Objective Motives:
{data.get('objective_motives', '[A COMPLETER]')}

Subjective Motives:
{data.get('subjective_motives', '[A COMPLETER]')}

Educational Importance:
{data.get('educational_importance', '[A COMPLETER]')}

Scope & Dimensions:
{data.get('scope_dimensions', '[A COMPLETER]')}

Project Objectives:
{data.get('objectives', '[A COMPLETER]')}

=== METHODOLOGICAL PLAN ===
Methodological Stages:
{data.get('methodology_stages', '[A COMPLETER]')}

Expected Results:
{data.get('expected_results', '[A COMPLETER]')}

Expected Product:
{data.get('expected_product', '[A COMPLETER]')}

=== IMPLEMENTATION & RESULTS DATA ===
Tools & Instruments Used:
{data.get('tools_used', '[A COMPLETER]')}

Actual Activities Conducted:
{data.get('activities_conducted', '[A COMPLETER]')}

Raw Results / Data:
{data.get('raw_results', '[A COMPLETER]')}

Challenges & Obstacles:
{data.get('challenges', '[A COMPLETER]')}

Personal & Professional Lessons Learned:
{data.get('lessons_learned', '[A COMPLETER]')}

Sources & References:
{data.get('references', '[A COMPLETER]')}

Appendices Content:
{data.get('appendices', '[A COMPLETER]')}

---

NOW GENERATE THE COMPLETE REPORT following all specifications from your instructions.
Start with the Cover Page and proceed through all 12 sections in order.
For any missing data, insert clearly marked [DONNEES A COMPLETER: ...] placeholders.
Make sure the total core content (Sections 3-10) stays within 25-28 pages.
The report must be defense-ready and demonstrate practical innovation.
"""
    return msg


# ═══════════════════════════════════════════════════════════════════════════
# API CALL
# ═══════════════════════════════════════════════════════════════════════════

def generate_report(client: OpenAI, model: str, data: dict) -> str:
    """Send the prompt to the API and return the generated report."""

    user_message = build_user_message(data)

    print("\n" + "=" * 70)
    print(f"  Sending to model: {model}")
    print(f"  System prompt: {len(SYSTEM_PROMPT)} chars")
    print(f"  User message:  {len(user_message)} chars")
    print("  Generating report... (this may take 2-5 minutes)")
    print("=" * 70 + "\n")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=16000,
    )

    return response.choices[0].message.content


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="PPE Report Generator — Generate a complete Supervised Personal Project report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python generate_report.py
          python generate_report.py --input student_data.json
          python generate_report.py --provider openrouter --model google/gemini-2.5-flash
          python generate_report.py --provider aistudio --model gemini-2.5-flash
          python generate_report.py --provider custom --base-url http://localhost:1234/v1
        """)
    )

    parser.add_argument(
        "--input", "-i",
        help="Path to a JSON file containing project data (skips interactive mode)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: report_YYYYMMDD_HHMMSS.md)"
    )
    parser.add_argument(
        "--provider", "-p",
        choices=["openai", "openrouter", "aistudio", "custom"],
        default="openai",
        help="API provider (default: openai)"
    )
    parser.add_argument(
        "--model", "-m",
        help="Model name (default depends on provider)"
    )
    parser.add_argument(
        "--base-url",
        help="Custom base URL (only used with --provider custom)"
    )
    parser.add_argument(
        "--api-key",
        help="API key (or set via environment variable API_KEY or provider-specific key)"
    )

    args = parser.parse_args()

    # --- Resolve provider settings ---
    if args.provider == "custom":
        if not args.base_url:
            print("ERROR: --base-url is required when using --provider custom")
            sys.exit(1)
        base_url = args.base_url
        default_model = "default"
        env_key = "API_KEY"
    else:
        provider_config = PROVIDERS[args.provider]
        base_url = provider_config["base_url"]
        default_model = provider_config["default_model"]
        env_key = provider_config["env_key"]

    model = args.model or default_model

    # --- Resolve API key ---
    api_key = (
        args.api_key
        or os.environ.get("API_KEY")
        or os.environ.get(env_key)
    )

    if not api_key:
        print(f"ERROR: No API key found.")
        print(f"Set it via:")
        print(f"  --api-key YOUR_KEY")
        print(f"  export API_KEY=YOUR_KEY")
        print(f"  export {env_key}=YOUR_KEY")
        sys.exit(1)

    # --- Initialize client ---
    client = OpenAI(base_url=base_url, api_key=api_key)

    print("\n" + "=" * 70)
    print("  PPE REPORT GENERATOR")
    print("  المشروع الشخصي المؤطر — مولد التقرير")
    print(f"  Provider: {args.provider} | Model: {model}")
    print("  Author: Mohamed HOUSNI | CRMEF Casablanca-Settat")
    print("=" * 70)

    # --- Collect data ---
    if args.input:
        data = load_data_from_json(args.input)
    else:
        data = collect_data_interactive()

        # Save collected data for reuse
        save_path = f"project_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n  Project data saved to: {save_path}")

    # --- Generate report ---
    report = generate_report(client, model, data)

    # --- Save output ---
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = data.get("full_name", "report").replace(" ", "_")[:30]
        output_path = f"report_{safe_name}_{timestamp}.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 70)
    print(f"  REPORT GENERATED SUCCESSFULLY")
    print(f"  Output: {output_path}")
    print(f"  Length: {len(report)} characters")
    print("=" * 70)
    print("\n  Next steps:")
    print("  1. Open the .md file and review all sections")
    print("  2. Search for [DONNEES A COMPLETER] and fill in missing data")
    print("  3. Copy into Microsoft Word and apply formatting")
    print("  4. Submit digital + physical copies 15 days before defense")
    print("  5. Prepare your 15-20 minute oral presentation")
    print("\n  Good luck! بالتوفيق والنجاح\n")


if __name__ == "__main__":
    main()
