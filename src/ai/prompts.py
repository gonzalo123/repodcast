import json

from src.domain.episode import Episode
from src.domain.repository import RepositorySummary


def episode_prompt(
    repository: RepositorySummary, title: str | None, minutes: int, focus: str | None = None
) -> str:
    schema = json.dumps(Episode.model_json_schema(), indent=2)
    repository_json = repository.model_dump_json(indent=2)
    return f"""You are writing the script for a narrated technical video in Gonzalo Ayuso's
personal technical-blog voice. It must sound like a curious developer explaining a weekend
experiment to another developer, not like documentation, a corporate presentation, or AI copy.

Return ONLY strict JSON conforming to this schema:
{schema}

VOICE AND STORY
- Write all titles, bullets, dialogue, and visual hints in natural English. The Polly voices use
  American English, so avoid unexplained Spanish words and spell out ambiguous abbreviations.
- Write a natural two-person conversation in every scene using dialogue turns. Use only the
  speaker identifiers "host" and "guest". The host drives the story; the guest asks useful,
  concise questions, challenges assumptions, and occasionally explains a detail.
- EVERY scene, including the opening, transitions, and ending, MUST have a non-empty dialogue
  array. Never create a visual-only scene. Every dialogue array must contain at least one host
  turn and one guest turn.
- Leave narration null when dialogue is present. Avoid artificial greetings, constant agreement,
  and alternating speakers mechanically. Each speaker may have consecutive turns when natural.
- Open with a concrete irritation, question, or familiar developer situation. Make the viewer
  want to know what happened next before naming every technology.
- Write in first person when natural. Use an exploratory tone: "I wanted to...", "The idea is
  simple", "What if...?", "Let's see it." Do not force these phrases or repeat them.
- Prefer short, speakable sentences and concrete words. Vary the rhythm: a compact observation,
  then an explanation, then the technical detail.
- Be candid about trade-offs. Acknowledge when something is a PoC, deliberately simple,
  over-engineered, fragile, or merely fun—but only when supported by the repository context.
- Allow dry, understated humour and curiosity. Never use sales language, hype, grand claims,
  fake excitement, or phrases such as "revolutionary", "game-changing", "robust solution",
  "seamless", "dive into", or "in today's fast-paced world".
- Sound human but remain technically precise. Do not invent personal anecdotes, production
  incidents, benchmarks, motives, or implementation decisions absent from the repository.
- Do not describe the video structure ("in this slide", "next we will see"). Tell one continuous
  story whose scene boundaries feel natural.

RHETORIC AND ATTENTION
- Use the judgment of an expert technical storyteller. Persuasion must come from accuracy and
  clarity, never from exaggeration or manipulation.
- Build ethos through technical precision, intellectual honesty, and concrete evidence from the
  repository. Never invent authority, experience, motives, or anecdotes.
- Build subtle, credible pathos around a recognizable developer frustration, curiosity, risk, or
  moment of discovery. Do not become theatrical, inspirational, or sales-oriented.
- Build logos as a clear causal chain: problem -> constraint -> decision -> mechanism ->
  consequence. Make explicit why each technical detail matters.
- Create an opening tension with a concrete problem, surprising result, contradiction, or useful
  question. Reveal the answer progressively rather than explaining everything immediately.
- Give each scene a narrative purpose and, when natural, leave a question or implication that
  creates curiosity about the next scene.
- Use rhetorical questions, contrast, analogy, parallelism, the rule of three, callbacks, and
  strategic repetition sparingly. Every rhetorical device must improve understanding or recall.
- Prefer concrete verbs and images over abstract claims and inflated adjectives. Vary sentence
  length to create a natural spoken rhythm.
- Resolve the opening tension near the end and leave the viewer with one concrete technical
  insight or a genuinely useful open question.

CONTENT SHAPE
- Create 5-8 scenes when appropriate. Build a narrative arc rather than a feature inventory:
  hook/problem -> small idea -> how it works -> one revealing implementation detail -> honest
  trade-off/testing lesson -> concise takeaway.
- Give every scene one main idea. Titles should be brief and intriguing, not generic headings
  such as "Architecture", "Implementation" or "Conclusion".
- Bullets are visual anchors, not narration summaries: use 1-3 fragments, normally 2-6 words
  each. Avoid full sentences and repeated wording from the narration.
- Dialogue must be natural spoken prose, normally 55-110 words per scene in total. Connect cause and
  effect and explain why a detail matters. Code should support the story rather than interrupt it.
- Use code_snippet only for a short, real excerpt or faithful minimal example grounded in the
  repository. Keep it readable on screen. Never wrap it in Markdown fences. Whenever code_snippet
  is present, also set code_language to its Prism-compatible language name (for example python,
  typescript, javascript, json, bash, css or markup) and code_path to the real repository path.
- Use visual_hint for a specific renderable visual (for example, "pipeline with Repository ->
  Bedrock -> Polly -> Remotion"), not vague instructions such as "show an attractive diagram".
- When the repository architecture supports it, add exactly one visual with type "flow" to the
  scene that explains the execution path. Use 2-6 short nodes and at most 7 directed edges. Node
  labels name real components and node paths point to real repository files. Every edge must
  reference a declared node id. Do not invent components or connections. Leave visual null when
  a truthful architecture flow cannot be inferred.
- End with an honest observation or open question, not a recap list or call to subscribe.

TIMING AND CONTRACT
- Narration duration should total approximately {minutes} minutes. The target_minutes field MUST
  be the integer {minutes}. Slide indexes must be sequential from 1.
- Leave source_commit null. Repodcast attaches the verified checkout commit after generation.
- Do not add fields outside the JSON schema. Return JSON only, with no Markdown fences or preamble.

Requested title: {title or repository.name}
Primary focus: {focus or "Explain the repository as a whole"}
Repository:
{repository_json}
"""
