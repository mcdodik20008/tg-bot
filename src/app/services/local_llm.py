from __future__ import annotations
import asyncio
import re
from functools import lru_cache
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from ..settings import settings

_SPECIAL_TAGS_RE = re.compile(r"<\|[^>]*\|>")


def _make_prompt(user_text: str, system: str) -> str:
    tok = _build_pipe().tokenizer
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]
    prompt = tok.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    print(prompt)
    return prompt


def _postprocess(text: str) -> str:
    text = _SPECIAL_TAGS_RE.sub("", text)
    text = text.strip()
    if len(text) > 4000:
        text = text[:3990].rstrip() + "…"
    return text


@lru_cache(maxsize=1)
def _build_pipe():
    tok = AutoTokenizer.from_pretrained(settings.model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        settings.model_id,
        dtype=torch.float32,
        device_map="auto",
        trust_remote_code=True,
    )
    return pipeline(
        "text-generation",
        model=model,
        tokenizer=tok,
        device_map="auto",
    )


async def generate_reply(
        user_text: str,
        system: str,
) -> str:
    pipe = _build_pipe()
    prompt = _make_prompt(user_text, system)
    out = pipe(
        prompt,
        max_new_tokens=settings.llm_max_new_tokens,
        temperature=settings.llm_temperature,
        top_p=settings.llm_top_p,
        return_full_text=False,
    )[0]["generated_text"]
    return _postprocess(out)
