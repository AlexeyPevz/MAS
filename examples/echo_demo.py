"""Simple echo demonstration using the MAS configuration."""
from pathlib import Path

from run import load_llm_tiers, pick_model


def main() -> None:
    tiers = load_llm_tiers(Path(__file__).resolve().parent.parent / "config" / "llm_tiers.yaml")
    model = pick_model(tiers)
    print(f"Selected model: {model}")
    text = input("Say something: ")
    print("Assistant:", text)


if __name__ == "__main__":
    main()

