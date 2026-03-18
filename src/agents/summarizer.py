from typing import List
from src.agents.base import BaseAgent
from openai.types.chat import ChatCompletionMessageParam


class SummarizerAgent(BaseAgent):
    def __init__(self):
        # We give it a very 'Administrative' persona.
        # No jokes, no samurai talk, just data.
        super().__init__(
            role_name="Scribe",
            persona=(
                "You are a professional administrative assistant. "
                "Your task is to condense information while preserving all core facts, "
                "entities, and data points. Do not add your own opinions."
            ),
        )

    def summarize(self, topic: str, content: str) -> str:
        """Mode 1: Summarizing a specific piece of web research"""
        # Truncate to save tokens
        truncated_content = content[:10000]

        user_instructions = f"""
        Extract only necessary points related to '{topic}' from the following text.
        
        Rules:
        - Use bullet points.
        - If the text is irrelevant, just say 'No relevant information found.'
        - Keep factual tone and avoid speculation.
        
        Text:
        {truncated_content} 
        """

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.persona},
            {"role": "user", "content": user_instructions},
        ]

        # Standard non-streaming call (summaries should be fast/internal)
        return self.generate_reply(messages, is_streaming=False)

    def summarize_history(self, history: List[ChatCompletionMessageParam]) -> str:
        """Mode 2: Summarizing the conversation so far (Context Management)."""
        history_text = "\n".join([f"{m['role']}: {m.get('content')}" for m in history])

        user_instruction = f"""
        Provide a 1-paragraph summary of the progress made in this conversation. 
        What was the user's goal, and what has been accomplished so far?
        
        HISTORY:
        {history_text}
        """

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.persona},
            {"role": "user", "content": user_instruction},
        ]

        return self.generate_reply(messages, is_streaming=False)
