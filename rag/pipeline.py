# rag/pipeline.py
from typing import List, Tuple
from embed.vectorizer import VectorStore
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import gc
import config

class RAGPipeline:
    def __init__(self, vector_store: VectorStore, generator_model: str = config.GENERATOR_MODEL):
        self.vs = vector_store
        print("[RAG] Loading generator model (4-bit quantized).")

        self.tokenizer = AutoTokenizer.from_pretrained(generator_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            generator_model,
            quantization_config=quant,
            device_map="auto",
            offload_folder="offload",
            offload_state_dict=True
        )
        self.model.eval()
        
        try:
            self.device = list(self.model.hf_device_map.values())[0]
        except Exception:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("[RAG] Model devices:", getattr(self.model, "hf_device_map", "unknown"))

    def build_prompt(self, query: str, retrieved: List[Tuple[str, float]]) -> str:
        # take top 5 high relevance chunks and compress them by truncating to 200 chars
        caps = []
        for chunk, score in retrieved[:5]:
            snippet = chunk.strip()[:200]
            caps.append(f"- {snippet} (score={score:.3f})")

        context = "\n".join(caps)
        prompt = f"""You are a concise assistant. Use ONLY the context to answer the question. Do NOT invent facts.

### Context
{context}

### Question
{query}

### Answer:"""
        return prompt

    def generate(self, prompt: str, max_tokens: int = config.MAX_GENERATION_TOKENS) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1600).to(self.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                num_beams=2,
                pad_token_id=self.tokenizer.eos_token_id
            )
        decoded = self.tokenizer.decode(out[0], skip_special_tokens=True)
        if "### Answer" in decoded:
            decoded = decoded.split("### Answer", 1)[-1].strip()

        # cleanup
        lines = [l.strip() for l in decoded.splitlines() if l.strip()]
        answer = " ".join(dict.fromkeys(lines))  # preserve order
        # free memory
        del inputs, out
        torch.cuda.empty_cache()
        gc.collect()
        return answer

    def query(self, user_query: str, top_k: int = 10) -> str:
        retrieved = self.vs.search(user_query, top_k=top_k)
        # filter by reasonable relevance (lower distance -> more similar; adjust if using L2)
        # here we keep first top_k and trust faiss ordering; if distances are large, return fallback
        if not retrieved:
            return "I don't have enough information to answer that."

        prompt = self.build_prompt(user_query, retrieved)
        return self.generate(prompt)
