import time
import os
from typing import List, Optional
from openai import OpenAI
from rich.console import Console
from dotenv import load_dotenv
from openai.types.chat import ChatCompletionMessageParam
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown

load_dotenv()


class BaseAgent:
    def __init__(self, role_name: str, persona: str) -> None:
        self.client = OpenAI(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",
        )
        self.model = os.getenv("MODEL_NAME")
        self.role_name = role_name
        self.persona = persona
        self.console = Console()

    def generate_reply(
        self, messages: List[ChatCompletionMessageParam], is_streaming: bool = True
    ) -> str:
        model = self.model
        if not model:
            return "Model not configured."

        full_response = ""
        token_count = 0
        start_time: Optional[float] = None

        # --- PATH A: NON-STREAMING (For internal agents like the Scribe) ---
        if not is_streaming:
            with self.console.status(
                f"[bold yellow]Waking up {model}...[/bold yellow]", spinner="dots"
            ):
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=False,
                    )
                except Exception as e:
                    return f"Connection error: {e}"

            return response.choices[0].message.content or ""

        with self.console.status(
            f"[bold yellow]Waking up {model}...[/bold yellow]", spinner="dots"
        ):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                )
            except Exception as e:
                return f"Connection error: {e}"

        # --- PATH B: STREAMING (For the Samurai UI) ---
        # In streaming mode, 'response' is an Iterable Stream.
        # We must iterate to find the choices inside each chunk.
        with Live(console=self.console, auto_refresh=False) as live:
            for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        if start_time is None:
                            start_time = time.time()

                        content = delta.content
                        full_response += content
                        token_count += 1

                        elapsed = time.time() - start_time
                        tps = token_count / elapsed if elapsed > 0 else 0

                        live.update(
                            Panel(
                                Markdown(full_response),
                                title=f"[bold blue]{self.role_name} BRAIN: {model}[/bold blue]",
                                border_style="bright_blue",
                                subtitle=f"[bold cyan]{tps:.1f} t/s[/bold cyan] | [white]{token_count} tokens[/white]",
                            ),
                            refresh=True,
                        )

        return full_response
