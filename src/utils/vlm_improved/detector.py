"""
Improved VLM dynamics detector: (1) enhanced prompt with per-class descriptions,
(2) 5 frames (start, 25%, 50%, 75%, end) for better temporal signal.
Set OPENROUTER_API_KEY in the environment.
"""

import os
import base64
import re
import numpy as np

DYNAMICS_CHOICES = [
    "pendulum",
    "sliding_block",
    "dropped_ball",
    "free_fall",
    "led",
    "torricelli",
]

# Per-class one-line descriptions to reduce confusion (especially free_fall vs dropped_ball vs pendulum)
DYNAMICS_DESCRIPTIONS = """
- pendulum: An object or ball swinging back and forth (oscillating motion).
- sliding_block: A block or object sliding down a ramp or slope.
- dropped_ball: A ball falling downward in the frame (e.g. side view; ball is dropped and falls).
- free_fall: A ball filmed from above; the ball's apparent size shrinks as it falls (scale/distance change).
- led: The brightness or intensity of a light source changing over time.
- torricelli: Water draining from a container; water level or a floating object going down.
"""

DEFAULT_MODEL = "openai/gpt-4o"
DEFAULT_NUM_FRAMES = 5


def _frames_from_npy_to_base64(npy_path: str, num_frames: int = 5) -> list[str]:
    """Load .npy, take num_frames spread across time (start, 25%, 50%, 75%, end), return base64 PNG URLs."""
    data = np.load(npy_path, allow_pickle=True)
    if getattr(data, "ndim", 0) == 0 and getattr(data.dtype, "name", "") == "object":
        data = data.item()
    if not isinstance(data, np.ndarray):
        data = np.array(data)
    if data.ndim == 5:
        n_samples, nf, _, h, w = data.shape
        indices = np.linspace(0, nf - 1, num=min(num_frames, nf), dtype=int)
        frames = [data[0, i, 0, :, :] for i in indices]
    elif data.ndim == 4:
        nf, _, h, w = data.shape
        indices = np.linspace(0, nf - 1, num=min(num_frames, nf), dtype=int)
        frames = [data[i, 0, :, :] for i in indices]
    else:
        raise ValueError(f"Unexpected .npy shape {data.shape}")

    import cv2
    out = []
    for frame in frames:
        if frame.max() <= 1.0:
            frame = (np.clip(frame, 0, 1) * 255).astype(np.uint8)
        else:
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        _, buf = cv2.imencode(".png", frame)
        b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
        out.append(f"data:image/png;base64,{b64}")
    return out


def detect_dynamics_from_npy(
    npy_path: str,
    *,
    model: str = DEFAULT_MODEL,
    num_frames: int = DEFAULT_NUM_FRAMES,
    api_key: str | None = None,
) -> str | None:
    """
    Improved VLM dynamics classification: enhanced prompt + more frames (default 5).
    Same return values as baseline (pendulum, sliding_block, dropped_ball, free_fall, led, torricelli).
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("VLM improved: OPENROUTER_API_KEY not set; skipping.")
        return None

    try:
        image_urls = _frames_from_npy_to_base64(npy_path, num_frames=num_frames)
    except Exception as e:
        print(f"VLM improved: failed to load frames from {npy_path}: {e}")
        return None

    prompt = (
        "These images are sample frames from a single physics experiment video (in time order). "
        "Classify the type of physical dynamics into exactly one of the following. "
        "Use the descriptions to tell similar cases apart:\n"
        + DYNAMICS_DESCRIPTIONS
        + "\nReply with only one word: the dynamics type (e.g. pendulum or free_fall). No other text."
    )

    content = [{"type": "text", "text": prompt}]
    for url in image_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})

    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            max_tokens=32,
        )
        raw = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        print(f"VLM improved: API error: {e}")
        return None

    raw_lower = raw.lower().strip()
    first_word = raw_lower.split()[0] if raw_lower else ""
    first_word = re.sub(r"[^a-z_]", "", first_word)
    for choice in DYNAMICS_CHOICES:
        if choice == first_word or choice.replace("_", "") == first_word.replace("_", ""):
            return choice
    if "dropped" in raw_lower and "ball" in raw_lower:
        return "dropped_ball"
    if "free" in raw_lower and "fall" in raw_lower:
        return "free_fall"
    if "sliding" in raw_lower and "block" in raw_lower:
        return "sliding_block"
    if "pendulum" in raw_lower:
        return "pendulum"
    if "led" in raw_lower or "light" in raw_lower:
        return "led"
    if "torricelli" in raw_lower or ("water" in raw_lower and "drain" in raw_lower):
        return "torricelli"
    print(f"VLM improved: could not parse dynamics from: {raw!r}")
    return None
