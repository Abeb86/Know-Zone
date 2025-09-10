from openai import OpenAI
import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

DEFAULT_QUESTIONS: List[Dict[str, str]] = [
    {"question": "Would you rather...", "option1": "Read a new book", "option2": "Re-read your favorite book"},
    {"question": "Would you rather...", "option1": "Do a science project", "option2": "Write a short story"},
    {"question": "Would you rather...", "option1": "Have extra art class", "option2": "Have extra music class"},
    {"question": "Would you rather...", "option1": "Study with a friend", "option2": "Study by yourself"},
    {"question": "Would you rather...", "option1": "Present to the class", "option2": "Make a poster"},
    {"question": "Would you rather...", "option1": "Join the chess club", "option2": "Join the robotics club"},
    {"question": "Would you rather...", "option1": "Do math puzzles", "option2": "Do word puzzles"},
    {"question": "Would you rather...", "option1": "Have a field trip to a museum", "option2": "Have a field trip to a zoo"},
    {"question": "Would you rather...", "option1": "Write with a pen", "option2": "Write with a pencil"},
    {"question": "Would you rather...", "option1": "Learn a new language", "option2": "Learn to code"},
    {"question": "Would you rather...", "option1": "Do a group project", "option2": "Do an individual project"},
    {"question": "Would you rather...", "option1": "Have homework on weekdays only", "option2": "Have a small assignment every day"},
    {"question": "Would you rather...", "option1": "Create a comic", "option2": "Create a slideshow"},
    {"question": "Would you rather...", "option1": "Learn about space", "option2": "Learn about oceans"},
    {"question": "Would you rather...", "option1": "Do a science experiment", "option2": "Build a model"},
    {"question": "Would you rather...", "option1": "Have a quiet reading time", "option2": "Have a fun quiz game"},
    {"question": "Would you rather...", "option1": "Practice typing", "option2": "Practice handwriting"},
    {"question": "Would you rather...", "option1": "Draw a picture", "option2": "Take a photo"},
    {"question": "Would you rather...", "option1": "Do a history timeline", "option2": "Build a geography map"},
    {"question": "Would you rather...", "option1": "Watch an educational video", "option2": "Listen to a podcast"},
    {"question": "Would you rather...", "option1": "Practice multiplication", "option2": "Practice fractions"},
    {"question": "Would you rather...", "option1": "Have a class debate", "option2": "Have a class survey"},
    {"question": "Would you rather...", "option1": "Read fiction", "option2": "Read non-fiction"},
    {"question": "Would you rather...", "option1": "Write a poem", "option2": "Write a letter"},
    {"question": "Would you rather...", "option1": "Do a nature walk", "option2": "Do a science lab"}
]


def _parse_json_response(text: str) -> Optional[List[Dict[str, str]]]:
    try:
        return json.loads(text)
    except Exception:
        # Try extracting from a fenced code block
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                part_stripped = part.strip()
                if part_stripped.startswith("[") and part_stripped.endswith("]"):
                    try:
                        return json.loads(part_stripped)
                    except Exception:
                        continue
        return None


def generate_questions(student1_name: str, student2_name: Optional[str] = None, count: int = 10, topic: Optional[str] = None) -> List[Dict[str, str]]:
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    if not api_key:
        try:
            import random as _random
            return _random.sample(DEFAULT_QUESTIONS, k=min(count, len(DEFAULT_QUESTIONS)))
        except Exception:
            return DEFAULT_QUESTIONS[:count]

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    topic_fragment = f" Focus on {topic}." if topic else ""
    names_fragment = f" between {student1_name} and {student2_name}" if student2_name else f" for {student1_name}"

    system_prompt = (
        "You are an assistant that outputs JSON only. Return exactly the requested number of items. "
        "Each item is an object with keys 'question', 'option1', 'option2'. "
        "Content must be school-friendly (K-12), positive, inclusive, and age-appropriate. Avoid sensitive or adult themes, "
        "bullying, cheating, academic dishonesty, violence, politics, religion, or anything that could make students uncomfortable. "
        "Vary topics (arts, science, reading, sports, hobbies, class activities) and keep options parallel and comparable. "
        "Do not include numbering, explanations, or any text outside the JSON array."
    )

    user_prompt = (
        f"Create {count} distinct 'Would you rather' questions{names_fragment}.{topic_fragment} "
        "Ensure no duplicates and keep them light, fun, and educational. "
        "Example of one item: {\n  \"question\": \"Would you rather...\",\n  \"option1\": \"Option A\",\n  \"option2\": \"Option B\"\n}. "
        "Return JSON array only."
    )

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.9,
            top_p=0.95,
        )
        content = completion.choices[0].message.content or ""
        parsed = _parse_json_response(content)
        if not parsed:
            return DEFAULT_QUESTIONS[:count]
        # Validate shape minimally
        cleaned: List[Dict[str, str]] = []
        for item in parsed:
            q = {
                "question": str(item.get("question", "Would you rather...")),
                "option1": str(item.get("option1", "Option 1")),
                "option2": str(item.get("option2", "Option 2")),
            }
            cleaned.append(q)
            if len(cleaned) >= count:
                break
        if not cleaned:
            return DEFAULT_QUESTIONS[:count]
        return cleaned
    except Exception:
        return DEFAULT_QUESTIONS[:count]

__all__ = ["generate_questions"]