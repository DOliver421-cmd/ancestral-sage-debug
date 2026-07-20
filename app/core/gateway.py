import os
import openai
from huggingface_hub import InferenceClient

class DynamicGatewayShield:
    def __init__(self):
        # Environmental variable links for your 8 exact requirements
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.together_key = os.getenv("TOGETHER_API_KEY")
        self.cohere_key = os.getenv("COHERE_API_KEY")
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        self.hf_token = os.getenv("HF_TOKEN")

    def execute_safe_generation(self, prompt_text: str, system_instruction: str = "You are a helpful assistant.") -> str:
        """
        Runs user queries through your 8-Tier Cardless Fallback Matrix.
        If a provider rate-limits or errors, it drops down instantly.
        """
        providers = [
            {"name": "Groq Cloud", "url": "https://groq.com", "key": self.groq_key, "model": "llama-3.3-70b-specdec", "type": "openai"},
            {"name": "Google AI Studio", "url": "https://googleapis.com", "key": self.gemini_key, "model": "gemini-1.5-flash", "type": "openai"},
            {"name": "OpenRouter Free", "url": "https://openrouter.ai", "key": self.openrouter_key, "model": "meta-llama/llama-3-8b-instruct:free", "type": "openai"},
            {"name": "OpenAI Account", "url": "https://openai.com", "key": self.openai_key, "model": "gpt-4o-mini", "type": "openai"},
            {"name": "Together AI", "url": "https://together.xyz", "key": self.together_key, "model": "meta-llama/Llama-3-8b-chat-hf", "type": "openai"},
            {"name": "Cohere AI", "url": "https://cohere.com", "key": self.cohere_key, "model": "command-r", "type": "openai"},
            {"name": "Mistral AI", "url": "https://mistral.ai", "key": self.mistral_key, "model": "codestral-latest", "type": "openai"},
            {"name": "Hugging Face Basement", "url": None, "key": self.hf_token, "model": "meta-llama/Meta-Llama-3-8B-Instruct", "type": "huggingface"}
        ]

        for provider in providers:
            if not provider["key"]:
                continue

            try:
                if provider["type"] == "openai":
                    client = openai.OpenAI(base_url=provider["url"], api_key=provider["key"])
                    response = client.chat.completions.create(
                        model=provider["model"],
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt_text}
                        ],
                        timeout=8.0  # 8-second safety cutoff
                    )
                    return response.choices.message.content

                elif provider["type"] == "huggingface":
                    hf_client = InferenceClient(model=provider["model"], token=provider["key"])
                    combined_prompt = f"{system_instruction}\n\nUser: {prompt_text}\nAssistant:"
                    response = hf_client.text_generation(combined_prompt, max_new_tokens=512)
                    return response

            except Exception as e:
                print(f"[SHIELD CASCADING] {provider['name']} failed. Dropping down.")
                continue

        return "System is currently optimizing processing queues. Please resubmit your command in 60 seconds."

gateway_shield = DynamicGatewayShield()
