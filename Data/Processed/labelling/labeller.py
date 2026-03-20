import pandas as pd
import json
import os
import time
from groq import Groq
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Load API key from .env file
load_dotenv(dotenv_path=r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\.env")

class QueryLabeller:
    def __init__(self, library_path, api_key=None):
        with open(library_path, 'r') as f:
            self.library = json.load(f)
        
        self.api_key = api_key or os.getenv("GORQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            print("Warning: GORQ_API_KEY not found in .env. LLM fallback will be disabled.")
            self.client = None
        
        # Define strict allowed intents
        self.allowed_intents = ["informational", "commercial", "transactional", "local"]

    def rule_based_label(self, query):
        query = str(query).lower()
        
        # 1. Intent Classification
        intent = "unknown"
        for label, keywords in self.library['intents'].items():
            if any(keyword in query for keyword in keywords):
                intent = label
                break
        
        # 2. Entity Extraction
        brand = "none"
        for b in self.library['entities']['brands']:
            if b in query:
                brand = b
                break
                
        category = "none"
        for c in self.library['entities']['categories']:
            if c in query:
                category = c
                break
                
        attributes = []
        for a in self.library['entities']['attributes']:
            if a in query:
                attributes.append(a)
                
        return intent, {"brand": brand, "category": category, "attributes": attributes}

    @retry(
        retry=retry_if_exception_type(Exception), 
        wait=wait_exponential(multiplier=2, min=5, max=120), 
        stop=stop_after_attempt(10)
    )
    def call_llm(self, query):
        # Strict prompt to ensure only allowed intents
        prompt = f"""
        Analyze this search query: "{query}"
        Choose EXACTLY ONE intent from this list: {self.allowed_intents}
        
        Return ONLY a JSON object:
        {{
          "intent": "one of the four above",
          "brand": "string or none",
          "category": "string or none",
          "attributes": ["list of strings"]
        }}
        """
        completion = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)

    def llm_fallback(self, query):
        if not self.client:
            return "informational", {"brand": "none", "category": "none", "attributes": []}
            
        try:
            data = self.call_llm(query)
            
            # Extract and validate intent
            intent = str(data.get("intent", "informational")).lower().strip()
            if intent not in self.allowed_intents:
                # Basic mapping if it tried to be clever
                if "buying" in intent or "shop" in intent: intent = "transactional"
                elif "where" in intent or "near" in intent: intent = "local"
                elif "how" in intent or "what" in intent: intent = "informational"
                else: intent = "informational" # Default fallback
            
            return intent, {
                "brand": str(data.get("brand", "none")),
                "category": str(data.get("category", "none")),
                "attributes": data.get("attributes", [])
            }
        except Exception as e:
            print(f"LLM Error for '{query}': {e}")
            return "informational", {"brand": "none", "category": "none", "attributes": []}

    def process_csv(self, input_path, output_path, limit=1000):
        # Read the cleaned data
        df = pd.read_csv(input_path)
        if limit and limit < len(df):
            df = df.head(limit)
            
        # Storage for new columns
        new_cols = {
            "intent": [],
            "brand": [],
            "category": [],
            "attributes": [],
            "labelling_method": []
        }

        print(f"Starting Linear Labelling: {len(df)} rows.")
        for i, row in df.iterrows():
            query = row['query']
            
            # Try Rule-based first
            intent, entities = self.rule_based_label(query)
            
            # If unable to classify or missing category, use LLM
            if (intent == "unknown") or (entities['category'] == "none") or (entities['brand'] == "none"):
                intent, entities = self.llm_fallback(query)
                method = "LLM"
            else:
                method = "Rule-based"

            # Final check to ensure intent is NEVER "unknown" for the final list
            if intent not in self.allowed_intents:
                intent = "informational"

            # Clean and join attributes
            raw_attrs = entities.get('attributes', [])
            if not isinstance(raw_attrs, list): raw_attrs = []
            clean_attrs = [str(a) for a in raw_attrs if not isinstance(a, dict)]
            
            new_cols["intent"].append(intent)
            new_cols["brand"].append(entities['brand'])
            new_cols["category"].append(entities['category'])
            new_cols["attributes"].append(", ".join(clean_attrs))
            new_cols["labelling_method"].append(method)
            
            # Progress tracking
            if (i+1) % 10 == 0:
                print(f"Processed {i+1}/{len(df)} rows...", flush=True)
            
            # Save progress every 100 rows to avoid loss
            if (i+1) % 100 == 0:
                temp_df = df.iloc[:i+1].copy()
                for key, val in new_cols.items():
                    temp_df[key] = val
                temp_df.to_csv(output_path, index=False)
                print(f"  --> [Checkpointed] Progress saved to {os.path.basename(output_path)}", flush=True)

        # Final save
        for key, val in new_cols.items():
            df[key] = val
            
        df.to_csv(output_path, index=False)
        print(f"\nSUCCESS: Processing Complete.")
        print(f"File Saved: {output_path}")

    def fix_multi_intents(self, file_path):
        """
        Identifies and fixes rows with multiple intents (e.g., 'transactional/commercial').
        """
        if not os.path.exists(file_path):
            print(f"File not found for fix: {file_path}")
            return
            
        print(f"Checking for multi-intents in {os.path.basename(file_path)}...")
        try:
            df = pd.read_csv(file_path)
            
            # Helper to detect if intent is multi-categorical
            def needs_fix(intent):
                if pd.isna(intent): return False
                intent_clean = str(intent).lower().strip()
                # If contains separators or isn't in allow-list
                if any(sep in intent_clean for sep in ["/", ",", " and "]): return True
                if intent_clean not in self.allowed_intents and intent_clean != "": return True
                return False

            mask = df['intent'].apply(needs_fix)
            multi_rows = df[mask].index.tolist()
            
            if not multi_rows:
                print(f"  --> No multi-intents found.")
                return
                
            print(f"  --> Found {len(multi_rows)} multi-intent rows to fix.")
            for idx in multi_rows:
                query = df.at[idx, 'query']
                original = str(df.at[idx, 'intent'])
                
                # Use existing call_llm logic but simplified
                try:
                    data = self.call_llm(query)
                    fixed = str(data.get("intent", "informational")).lower().strip()
                    if fixed not in self.allowed_intents: fixed = "informational"
                    df.at[idx, 'intent'] = fixed
                    print(f"      [Fixed] '{query}': {original} -> {fixed}")
                except Exception as e:
                    print(f"      [Error] Could not fix '{query}': {e}")
            
            # Safe save
            temp_path = file_path + ".tmp"
            df.to_csv(temp_path, index=False)
            os.replace(temp_path, file_path)
            print(f"  --> {os.path.basename(file_path)} successfully cleaned of multi-intents.")
        except Exception as e:
            print(f"Error during multi-intent fix: {e}")

if __name__ == "__main__":
    LIB_PATH = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\Data\Processed\labelling\keyword_library.json"
    INPUT_FILE = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\Data\Processed\Cleanup\sample_cleaned.csv"
    OUTPUT_FILE = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\Data\Processed\labelling\sample_labelled.csv"
    
    labeller = QueryLabeller(LIB_PATH)
    
    # 1. Run main labelling if needed (checking if input exists)
    if os.path.exists(INPUT_FILE):
        labeller.process_csv(INPUT_FILE, OUTPUT_FILE, limit=1000)
    
    # 2. Final check & fix for any multi-intents (always run this to be safe)
    labeller.fix_multi_intents(OUTPUT_FILE)
    
    # Also fix sample.csv if it exists
    SAMPLE_FILE = r"C:\Users\SOLEKTA\Desktop\Intern\Month3\Proj\geo_seo_scoring\Data\Processed\sample.csv"
    if os.path.exists(SAMPLE_FILE):
        labeller.fix_multi_intents(SAMPLE_FILE)

