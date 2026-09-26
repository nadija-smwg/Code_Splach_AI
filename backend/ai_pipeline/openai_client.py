import os
import json
import logging
import base64
from io import BytesIO
from pydantic import BaseModel
from openai import OpenAI
from PIL import Image

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. OpenAI calls will fail.")
            self._client = None
        else:
            self._client = OpenAI(api_key=api_key, base_url=base_url)
        
        self.fast_model = os.getenv("OPENAI_FAST_MODEL", "gpt-4o-mini")
        self.vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    def _resize_image(self, pil_img: Image.Image) -> str:
        max_width = 1600
        if pil_img.width > max_width:
            ratio = max_width / pil_img.width
            new_size = (max_width, int(pil_img.height * ratio))
            pil_img = pil_img.resize(new_size, Image.LANCZOS)
            
        buffered = BytesIO()
        if pil_img.mode in ("RGBA", "P"):
            pil_img = pil_img.convert("RGB")
        pil_img.save(buffered, format="JPEG", quality=80)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def get_vision_completion(self, prompt: str, image: Image.Image, schema: type[BaseModel] | None = None, model: str | None = None) -> dict | str:
        if not self._client:
            return {} if schema else ""
            
        b64_image = self._resize_image(image)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}"
                        }
                    }
                ]
            }
        ]
        
        target_model = model or self.fast_model
        
        try:
            if schema:
                response = self._client.beta.chat.completions.parse(
                    model=target_model,
                    messages=messages,
                    response_format=schema,
                    temperature=0.0
                )
                return json.loads(response.choices[0].message.content)
            else:
                response = self._client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=0.0
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI vision completion failed: {e}")
            return {} if schema else ""

    def get_completion(self, prompt: str, system: str = "", schema: type[BaseModel] | None = None, model: str | None = None, json_mode: bool = False) -> dict | str:
        if not self._client:
            return {} if (schema or json_mode) else ""
            
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        target_model = model or self.fast_model
        
        try:
            if schema:
                response = self._client.beta.chat.completions.parse(
                    model=target_model,
                    messages=messages,
                    response_format=schema,
                    temperature=0.0
                )
                return json.loads(response.choices[0].message.content)
            else:
                kwargs = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": 0.0
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                    
                response = self._client.chat.completions.create(**kwargs)
                res = response.choices[0].message.content
                if json_mode:
                    try:
                        return json.loads(res)
                    except:
                        return {}
                return res
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            return {} if (schema or json_mode) else ""

    def get_embedding(self, text: str) -> list[float]:
        if not self._client:
            return []
        try:
            response = self._client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return []
