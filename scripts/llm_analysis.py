import json
import tiktoken
import config
import time
from openai import OpenAI
from utils import FileUtils
from collections import deque

class LLMAnalysis:
    def __init__(self, model_name):
        if model_name not in ['OpenAI', 'Deepseek']:
            raise ValueError("Model must be 'OpenAI' or 'Deepseek'")
        else:
            self.model_config = config.OpenAI if model_name == 'OpenAI' else config.DeepSeek
        self.model = model_name
        self.client = OpenAI(api_key=self.model_config.API_KEY)
        self.role = "developer"
        self.rate_limiter = RateLimiter(
            tokens_per_minute=self.model_config.TPM,
            requests_per_minute=self.model_config.RPM,
            model_name=self.model_config.MODEL
        )
    
    def analyze_samples(self):
      lib_dir = config.MANUAL_ANALYSIS_PATH
      for samples_path in FileUtils.traverse_directory(lib_dir):
        
        print(f"Analyzing {samples_path}...")
        samples = FileUtils.load_json_file(samples_path)
        modified = False
        
        for sample in samples:
          prompt = analysis.generate_prompt(sample)
          response_str = analysis.query_model(prompt)
          
          try:
            parsed_response = json.loads(response_str)
            sample["llm_analysis"] = {
                "correct_mapping?": parsed_response.get("correct_mapping", False),
                "decreases_severity?": parsed_response.get("decreases_severity", False),
                "reason?": parsed_response.get("reason", "")
            }
            modified = True
          except json.JSONDecodeError:
            print(f"Error parsing response: {response_str}")
            sample["llm_analysis"] = {
                "correct_mapping?": False,
                "decreases_severity?": False,
                "reason?": "Error parsing response"
            }
            modified = False
          
        if modified:
          FileUtils.save_json_file(samples_path, samples)

        
    def generate_prompt(self, SI):
        """
        Generates a structured prompt for the model to analyze whether the 
        detected code smell and applied refactoring correctly correspond to the code changes.
        """
        smell_kind = SI["smell_versions"][-1]["smell_kind"]
        smell_type = SI["smell_versions"][-1]["smell_name"]
        smell_file_name = self._get_file_name(SI["smell_versions"][-1]["package_name"], SI["smell_versions"][-1]["type_name"])
        smell_method = SI["smell_versions"][-1]["method_name"]
        smell_method_range = (SI['smell_versions'][-1]['method_start_ln'], SI['smell_versions'][-1]['method_end_ln'])
        smell_cause = SI["smell_versions"][-1]["cause"]
        
        ref = SI["removed_by_refactorings"][0]
        ref_type = ref["type_name"]
        ref_description = ref["description"]
        ref_left_changes = ref["left_changes"]
        ref_right_changes = ref["right_changes"]
        
        # Generate a structured prompt
        prompt = f"""
        You are an expert software developer that understand code smells and refactoring with very good grasp and practical knowledge in Java programming.
        Instructions:
        - correct_mapping: Respond with `true` if the refactoring effectively removes the code smell; respond with `false` if it does not, and provide a brief explanation.
        - decreases_severity: Respond with `true` if the refactoring reduces the severity of the code smell without completely eliminating it; respond with `false` if it does not reduce or increases the severity.
        - Output Format: The answer must be in the format: `{{"correct_mapping": <true/false>, "decreases_severity": <true/false>, "reason": "<brief explanation>"}}`
        
        Context:
        A code smell was removed at a commit in the following file:
        - File: {smell_file_name}
        {f"- Method: {smell_method} (Lines {smell_method_range[0]} - {smell_method_range[1]})" if smell_method else ""}
        - Smell Kind: {smell_kind}
        - Smell Type: {smell_type}
        - Smell Cause: {smell_cause}

        In the same commit, a refactoring was applied:
        - Refactoring Type: {ref_type}
        - Description: {ref_description}
        - Code changes in a commit because of refactoring:
          - Before: {ref_left_changes}
          - After: {ref_right_changes}
        """.strip()
        
        return prompt
    
    def _get_file_name(self, package, type):
        if package == "<All packages>":
            return package
        slash_pkg_path = package.replace('.', '/') if package else ''
        extension = f"{type}.java" if type else ''
        return f"{slash_pkg_path}/{extension}" if slash_pkg_path and extension else ''
        
    def query_model(self, prompt):
        """
        Query the model with the generated prompt.
        """
        messages = [{"role": self.role, "content": prompt}]
        token_count = self.rate_limiter.count_tokens(messages)
        self.rate_limiter.wait_if_needed(token_count)
        
        completion = self.client.chat.completions.create(
            model=self.model_config.MODEL,
            messages=messages,
            temperature=0.3
        )
        return completion.choices[0].message.content.strip()

# ---- Rate Limiter Helper ----
class RateLimiter:
    def __init__(self, tokens_per_minute=300000, requests_per_minute=200, model_name="gpt-4o-mini"):
        self.tokens_per_minute = tokens_per_minute
        self.requests_per_minute = requests_per_minute
        self.token_history = deque()
        self.request_history = deque()
        self.model = model_name
        self.encoding = tiktoken.encoding_for_model(model_name)

    def _cleanup(self):
        now = time.time()
        while self.token_history and now - self.token_history[0][0] > 60:
            self.token_history.popleft()
        while self.request_history and now - self.request_history[0] > 60:
            self.request_history.popleft()

    def count_tokens(self, messages):
        tokens_per_message = 3  # rough for gpt-4o-mini
        tokens = 0
        for message in messages:
            tokens += tokens_per_message
            for key, value in message.items():
                tokens += len(self.encoding.encode(value))
        tokens += 3  # for assistant priming
        return tokens

    def wait_if_needed(self, token_count):
        self._cleanup()
        current_tokens = sum(t for _, t in self.token_history)
        current_requests = len(self.request_history)

        if current_tokens + token_count > self.tokens_per_minute or current_requests >= self.requests_per_minute:
            sleep_time = max(
                60 - (time.time() - self.token_history[0][0]) if self.token_history else 0,
                60 - (time.time() - self.request_history[0]) if self.request_history else 0
            )
            print(f"[RateLimiter] Sleeping for {sleep_time:.2f} seconds to respect rate limits...")
            time.sleep(sleep_time)
            self._cleanup()

        self.token_history.append((time.time(), token_count))
        self.request_history.append(time.time())


if __name__ == "__main__":
    analysis = LLMAnalysis(model_name="OpenAI")
    analysis.analyze_samples()
    