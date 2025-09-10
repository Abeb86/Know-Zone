from openai import OpenAI
import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

DEFAULT_QUESTIONS: List[Dict[str, str]] = [
    {"question": "Would you rather...", "option1": "Copy someone else's homework the morning it's due", "option2": "Pay someone to write your final paper"},
    {"question": "Would you rather...", "option1": "Take an exam you didn't study for honestly", "option2": "Cheat but risk getting caught and failing the course"},
    {"question": "Would you rather...", "option1": "Work with a friend on an assignment meant to be individual", "option2": "Turn in an assignment late and lose points"},
    {"question": "Would you rather...", "option1": "Use AI to write your entire essay", "option2": "Submit a poorly written essay you actually wrote"},
    {"question": "Would you rather...", "option1": "Let a classmate copy your work knowing they'll keep doing it", "option2": "Refuse to share and risk the friendship"},
    {"question": "Would you rather...", "option1": "Take credit for a group project you barely contributed to", "option2": "Tell the professor you didn't do your fair share"},
    {"question": "Would you rather...", "option1": "Use a fake excuse to get an extension", "option2": "Submit incomplete work on time"},
    {"question": "Would you rather...", "option1": "Have your professor discover you plagiarized", "option2": "Never get caught but always know you cheated"},
    {"question": "Would you rather...", "option1": "Share test questions with friends after taking an exam", "option2": "Keep them to yourself knowing others might fail"},
    {"question": "Would you rather...", "option1": "Get an A by cheating in one important course", "option2": "Get a B by being honest in all your courses"}
]


def _parse_json_response(text: str) -> Optional[List[Dict[str, str]]]:
    try:
        return json.loads(text)
    except Exception:
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
        return DEFAULT_QUESTIONS[:count]

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    topic_fragment = f" Focus on {topic}." if topic else ""
    names_fragment = f" between {student1_name} and {student2_name}" if student2_name else f" for {student1_name}"

    system_prompt = (
        "You generate JSON only. Return an array of objects with keys 'question', 'option1', 'option2'. "
        "Keep content school-friendly."
    )

    user_prompt = (
        f"Create {count} 'Would you rather' questions{names_fragment}.{topic_fragment} "
        "Example of a single item: {\n  \"question\": \"Would you rather...\",\n  \"option1\": \"Option A\",\n  \"option2\": \"Option B\"\n}. "
        "Return JSON only, no prose."
    )

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content or ""
        parsed = _parse_json_response(content)
        if not parsed:
            return DEFAULT_QUESTIONS[:count]
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


