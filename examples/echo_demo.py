"""Simple echo demonstration using the MAS configuration."""
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from tools.llm_config import load_llm_tiers


def main() -> None:
    tiers = load_llm_tiers()
    print(f"Loaded LLM tiers: {list(tiers.keys()) if tiers else 'None'}")
    text = input("Say something: ")
    print("Assistant:", text)


if __name__ == "__main__":
    main()

