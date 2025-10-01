import sys
import re
import json
import requests


def stream_chat(url: str, question: str, model: str = "mistral") -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question}
        ]
    }
    with requests.post(url, json=payload, stream=True, timeout=300) as r:
        r.raise_for_status()
        chunks = []
        for line in r.iter_lines():
            if not line:
                continue
            try:
                text = line.decode("utf-8")
            except Exception:
                continue
            chunks.append(text)
        return "".join(chunks)


def run_checks(answer: str) -> int:
    failures = 0
    def check(cond: bool, name: str):
        nonlocal failures
        if cond:
            print(f"[PASS] {name}")
        else:
            print(f"[FAIL] {name}")
            failures += 1

    # 1) Contains Sources footer
    check("Sources:" in answer, "Contains Sources footer")

    # 2) Brevity: ~<= 120 words before Sources
    main = answer.split("Sources:", 1)[0]
    words = re.findall(r"\b\w+\b", main)
    check(len(words) <= 140, "Concise main answer (<= 140 words)")

    # 3) Markdown present (heading or bullets). Be lenient about spacing.
    has_md = bool(
        re.search(r"#{2,6}\s", main) or  # any heading markers
        re.search(r"(^|\n)\s*[-*]\s", main)  # bullet at line start
    )
    check(has_md, "Uses Markdown formatting (heading/bullets)")

    # 4) Roman Nepali phrases count (at most 2 common ones)
    np_words = ["thik cha", "bujhnu bhayo", "sankshipta"]
    count = sum(main.lower().count(w) for w in np_words)
    check(count <= 2, "At most 1–2 Roman Nepali phrases")

    # 5) Grounding hint: contains bracket citations like [1]
    check(bool(re.search(r"\[\d+\]", main)), "Contains inline citations like [1]")

    return failures


def main():
    url = "http://localhost:8000/api/rag-chat"
    question = "Explain SN1 vs SN2 briefly."
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    print(f"Query: {question}")
    print("Requesting...\n")
    answer = stream_chat(url, question)
    print("--- Answer ---\n")
    # Print safely on Windows consoles
    try:
        print(answer)
    except UnicodeEncodeError:
        print(answer.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore"))
    print("\n--- Checks ---")
    failures = run_checks(answer)
    if failures == 0:
        print("\nRESULT: PASS")
        sys.exit(0)
    else:
        print(f"\nRESULT: FAIL ({failures} failing checks)")
        sys.exit(1)


if __name__ == "__main__":
    main()


