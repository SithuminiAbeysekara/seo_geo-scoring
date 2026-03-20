import json
import os
from groq import Groq
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv(
    dotenv_path=r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\.env"
)


class LibraryGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GORQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            raise ValueError(
                "GORQ_API_KEY not found in .env. LLM required for generation."
            )

    def expand_keywords(self, seed_words, context_description):
        """
        Takes a list of seed words and expands them into a larger list of related queries/synonyms.
        """
        combined_seeds = ", ".join(seed_words)
        prompt = f"""
        You are an SEO expert. Generate an expanded list of 10-15 keywords, synonyms, and "near-keywords" for the following {context_description}:
        Seed words: {combined_seeds}

        Requirements:
        1. Focus on keywords that users actually type into search engines.
        2. Include synonyms, near-duplicates, and variations.
        3. Exclude very long phrases.
        4. Return a JSON object with a single key 'keywords' containing a list of strings.
        """

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            data = json.loads(completion.choices[0].message.content)
            return data.get("keywords", [])
        except Exception as e:
            print(f"Error expanding keywords for {combined_seeds}: {e}")
            return []

    def generate_full_library(self, output_path):
        seeds = {
            "intents": {
                "informational": ["how to", "what is", "guide", "review"],
                "commercial": ["vs", "comparison", "best rated", "cheap"],
                "transactional": ["buy", "price", "order", "discount", "sale"],
                "local": ["near me", "nearby", "store locator", "address"],
            },
            "entities": {
                "brands": [
                    "nike",
                    "apple",
                    "samsung",
                    "amazon",
                    "sony",
                    "ikea",
                    "dell",
                ],
                "categories": [
                    "shoes",
                    "phone",
                    "laptop",
                    "clothing",
                    "furniture",
                    "envelopes",
                    "fence",
                ],
                "attributes": [
                    "blue",
                    "large",
                    "small",
                    "waterproof",
                    "fast charging",
                    "self-seal",
                ],
            },
        }

        library = {
            "intents": {},
            "entities": {"brands": [], "categories": [], "attributes": []},
        }

        # Expand Intent Keywords
        print("Expanding Intents...")
        for intent, words in seeds["intents"].items():
            expanded = self.expand_keywords(words, f"SEO intent: {intent}")
            library["intents"][intent] = sorted(list(set(words + expanded)))
            print(f"  - {intent}: Found {len(library['intents'][intent])} words.")

        # Expand Entity Keywords
        print("Expanding Entities...")
        for entity_type, words in seeds["entities"].items():
            expanded = self.expand_keywords(words, f"Product {entity_type}")
            library["entities"][entity_type] = sorted(list(set(words + expanded)))
            print(
                f"  - {entity_type}: Found {len(library['entities'][entity_type])} words."
            )

        # Save to file
        with open(output_path, "w") as f:
            json.dump(library, f, indent=2)
        print(f"Library saved to {output_path}")


if __name__ == "__main__":
    output_file = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\Data\Processed\labelling\keyword_library.json"
    generator = LibraryGenerator()
    generator.generate_full_library(output_file)
