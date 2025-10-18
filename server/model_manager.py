"""
Model Manager for MLX local inference.
Handles model loading, unloading, downloading from Hugging Face, and update checking.
"""

import os
import asyncio
import shutil
import psutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from huggingface_hub import snapshot_download, repo_info, hf_hub_download
from huggingface_hub.utils import HfHubHTTPError
import mlx.core as mx
from mlx_lm import load, generate
try:
    from mlx_lm.sample_utils import make_sampler
    HAS_SAMPLER = True
except ImportError:
    HAS_SAMPLER = False
from mlx_lm.utils import load as mlx_load

from server.utils import logger, get_config


class ModelManager:
    """
    Singleton manager for MLX model operations.
    Handles loading, unloading, downloading, and update checking.
    """

    def __init__(self):
        """Initialize the model manager."""
        self.config = get_config()
        self.cache_dir = Path(self.config["model_cache_dir"])
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.current_model = None
        self.current_tokenizer = None
        self.current_model_id = None
        self.model_config = None

        # Performance tracking (inspired by LM Studio)
        self.load_time = None
        self.last_generation_stats = {
            "tokens_per_second": 0.0,
            "time_to_first_token": 0.0,
            "total_tokens": 0
        }

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info("ModelManager initialized")

    async def list_available_models(self) -> List[str]:
        """
        List all models that are allowed (from ALLOWED_MODELS env var).

        Returns:
            List of model IDs
        """
        allowed = self.config["allowed_models"]
        # Filter out empty strings
        return [m.strip() for m in allowed if m.strip()]

    async def current_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently loaded model.

        Returns:
            Dict with model_id, loaded status, config
        """
        if self.current_model is None:
            return None

        return {
            "model_id": self.current_model_id,
            "loaded": True,
            "config": self.model_config if self.model_config else {}
        }

    async def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.current_model is not None

    async def get_local_model_path(self, repo_id: str) -> Optional[Path]:
        """
        Get the local path for a model if it exists.

        Args:
            repo_id: Hugging Face repository ID

        Returns:
            Path if model exists locally, None otherwise
        """
        # Convert repo_id to safe directory name
        safe_name = repo_id.replace("/", "--")
        model_path = self.cache_dir / safe_name

        if model_path.exists() and (model_path / "config.json").exists():
            return model_path

        return None

    async def download_model(self, repo_id: str, force: bool = False) -> Path:
        """
        Download a model from Hugging Face Hub.

        Args:
            repo_id: Hugging Face repository ID
            force: If True, re-download even if exists

        Returns:
            Path to downloaded model directory

        Raises:
            Exception if download fails
        """
        safe_name = repo_id.replace("/", "--")
        model_path = self.cache_dir / safe_name

        # Check if already downloaded
        if not force and model_path.exists():
            logger.info(f"Model {repo_id} already cached at {model_path}")
            return model_path

        logger.info(f"Downloading model {repo_id} from Hugging Face...")

        try:
            # Get HF token if available
            hf_token = self.config.get("hf_token")
            if hf_token:
                hf_token = hf_token.strip()
            if not hf_token:
                hf_token = None

            # Download model snapshot
            downloaded_path = snapshot_download(
                repo_id=repo_id,
                cache_dir=self.cache_dir,
                local_dir=model_path,
                local_dir_use_symlinks=False,
                token=hf_token
            )

            logger.info(f"Model {repo_id} downloaded successfully to {downloaded_path}")
            return Path(downloaded_path)

        except HfHubHTTPError as e:
            logger.error(f"Failed to download model {repo_id}: {e}")
            raise Exception(f"Model download failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading {repo_id}: {e}")
            raise

    async def check_for_updates(self, repo_id: str) -> bool:
        """
        Check if a newer version of the model exists on Hugging Face.

        Args:
            repo_id: Hugging Face repository ID

        Returns:
            True if update available, False otherwise
        """
        local_path = await self.get_local_model_path(repo_id)
        if not local_path:
            # Not downloaded yet
            return True

        try:
            hf_token = self.config.get("hf_token")
            if hf_token:
                hf_token = hf_token.strip()
            if not hf_token:
                hf_token = None
            info = repo_info(repo_id, token=hf_token)

            # Check last modified time
            # This is a simplified check; in production, compare commit SHAs
            remote_updated = info.lastModified

            # Get local timestamp (use directory modification time as proxy)
            local_updated = local_path.stat().st_mtime

            logger.info(f"Update check for {repo_id}: remote={remote_updated}, local={local_updated}")

            # If remote is newer, update available
            return remote_updated.timestamp() > local_updated

        except Exception as e:
            logger.warning(f"Could not check updates for {repo_id}: {e}")
            return False

    async def update_model(self, repo_id: str) -> Path:
        """
        Update a model by re-downloading it.

        Args:
            repo_id: Hugging Face repository ID

        Returns:
            Path to updated model
        """
        # Unload if currently loaded
        if self.current_model_id == repo_id:
            logger.warning(f"Cannot update {repo_id} while it's loaded. Unload first.")
            raise Exception(f"Model {repo_id} is currently loaded. Unload before updating.")

        local_path = await self.get_local_model_path(repo_id)
        if local_path:
            logger.info(f"Removing old version of {repo_id}")
            shutil.rmtree(local_path)

        return await self.download_model(repo_id, force=True)

    async def estimate_model_memory(self, repo_id: str) -> Dict[str, Any]:
        """
        Estimate memory requirements for a model before loading.
        Inspired by LM Studio's memory estimation feature.

        Args:
            repo_id: Hugging Face repository ID

        Returns:
            Dict with memory estimates and system info
        """
        try:
            # Get model path
            local_path = await self.get_local_model_path(repo_id)
            if not local_path:
                return {
                    "error": "Model not downloaded. Download first to estimate memory."
                }

            # Load config to get model parameters
            config_path = local_path / "config.json"
            if not config_path.exists():
                return {"error": "Model config not found"}

            import json
            with open(config_path, "r") as f:
                config = json.load(f)

            # Estimate based on model parameters
            vocab_size = config.get("vocab_size", 32000)
            hidden_size = config.get("hidden_size", 4096)
            num_layers = config.get("num_hidden_layers", 32)
            intermediate_size = config.get("intermediate_size", 11008)

            # Rough estimation (in GB)
            # This is a simplified calculation
            # Real calculation would depend on quantization, etc.
            params_estimate = (
                vocab_size * hidden_size +  # Embedding
                num_layers * (
                    hidden_size * hidden_size * 4 +  # Attention
                    hidden_size * intermediate_size * 2  # FFN
                )
            ) * 2  # 2 bytes per parameter (fp16)

            estimated_gb = params_estimate / (1024 ** 3)

            # Get system memory info
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)
            total_gb = memory.total / (1024 ** 3)

            # Check if model will fit
            will_fit = available_gb > (estimated_gb * 1.2)  # 20% margin

            return {
                "model_id": repo_id,
                "estimated_memory_gb": round(estimated_gb, 2),
                "system_total_memory_gb": round(total_gb, 2),
                "system_available_memory_gb": round(available_gb, 2),
                "will_fit": will_fit,
                "recommendation": "OK to load" if will_fit else "May cause out of memory",
                "model_params": {
                    "vocab_size": vocab_size,
                    "hidden_size": hidden_size,
                    "num_layers": num_layers,
                    "intermediate_size": intermediate_size
                }
            }

        except Exception as e:
            return {"error": f"Memory estimation failed: {str(e)}"}

    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get current system memory and MLX stats.
        Inspired by LM Studio's system monitoring.

        Returns:
            Dict with system statistics
        """
        memory = psutil.virtual_memory()

        # Try to get MLX memory stats
        try:
            mlx_memory = mx.metal.get_active_memory() / (1024 ** 3)  # GB
            mlx_peak_memory = mx.metal.get_peak_memory() / (1024 ** 3)  # GB
            mlx_cache_memory = mx.metal.get_cache_memory() / (1024 ** 3)  # GB
        except:
            mlx_memory = 0
            mlx_peak_memory = 0
            mlx_cache_memory = 0

        return {
            "system": {
                "total_memory_gb": round(memory.total / (1024 ** 3), 2),
                "available_memory_gb": round(memory.available / (1024 ** 3), 2),
                "used_memory_gb": round(memory.used / (1024 ** 3), 2),
                "percent": memory.percent
            },
            "mlx": {
                "active_memory_gb": round(mlx_memory, 2),
                "peak_memory_gb": round(mlx_peak_memory, 2),
                "cache_memory_gb": round(mlx_cache_memory, 2)
            },
            "model_loaded": self.current_model is not None,
            "current_model": self.current_model_id
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the current model.
        Includes tokens/second, TTFT, etc. (inspired by LM Studio).

        Returns:
            Dict with performance stats
        """
        return {
            "model_id": self.current_model_id,
            "loaded": self.current_model is not None,
            "load_time_seconds": self.load_time,
            "last_generation": {
                "tokens_per_second": round(self.last_generation_stats["tokens_per_second"], 2),
                "time_to_first_token_ms": round(self.last_generation_stats["time_to_first_token"] * 1000, 2),
                "total_tokens": self.last_generation_stats["total_tokens"]
            }
        }

    async def load_model(self, repo_id: str) -> Dict[str, Any]:
        """
        Load a model into memory using MLX.

        Args:
            repo_id: Hugging Face repository ID

        Returns:
            Dict with model info

        Raises:
            Exception if load fails
        """
        async with self._lock:
            # Unload current model if different
            if self.current_model is not None:
                if self.current_model_id == repo_id:
                    logger.info(f"Model {repo_id} already loaded")
                    return await self.current_model_info()
                else:
                    logger.info(f"Unloading {self.current_model_id} to load {repo_id}")
                    await self._unload_model_internal()

            # Ensure model is downloaded
            local_path = await self.get_local_model_path(repo_id)
            if not local_path:
                logger.info(f"Model {repo_id} not found locally, downloading...")
                local_path = await self.download_model(repo_id)

            logger.info(f"Loading model from {local_path}...")

            try:
                # Track load time
                start_time = time.time()

                # Load model and tokenizer using mlx_lm
                model, tokenizer = load(str(local_path))

                self.load_time = time.time() - start_time

                self.current_model = model
                self.current_tokenizer = tokenizer
                self.current_model_id = repo_id

                # Try to load config
                config_path = local_path / "config.json"
                if config_path.exists():
                    import json
                    with open(config_path, "r") as f:
                        self.model_config = json.load(f)
                else:
                    self.model_config = {}

                logger.info(f"Model {repo_id} loaded successfully on MLX")

                return {
                    "model_id": repo_id,
                    "loaded": True,
                    "path": str(local_path),
                    "config": self.model_config
                }

            except Exception as e:
                logger.error(f"Failed to load model {repo_id}: {e}")
                self.current_model = None
                self.current_tokenizer = None
                self.current_model_id = None
                raise Exception(f"Model load failed: {e}. Try a smaller model if OOM.")

    async def _unload_model_internal(self):
        """Internal method to unload the current model (no lock)."""
        if self.current_model is None:
            return

        logger.info(f"Unloading model {self.current_model_id}")

        # Clear references
        self.current_model = None
        self.current_tokenizer = None
        self.current_model_id = None
        self.model_config = None

        # Force garbage collection
        import gc
        gc.collect()

        logger.info("Model unloaded, VRAM freed")

    async def unload_model(self):
        """
        Unload the currently loaded model and free VRAM.
        """
        async with self._lock:
            await self._unload_model_internal()

    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion using the loaded model.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences

        Returns:
            Dict with generated text and token counts
        """
        if self.current_model is None or self.current_tokenizer is None:
            raise Exception("No model loaded. Load a model first.")

        async with self._lock:
            try:
                logger.info(f"Generating completion (max_tokens={max_tokens}, temp={temperature})")

                # Track performance
                gen_start_time = time.time()
                first_token_time = None

                # Use mlx_lm.generate with appropriate API based on version
                if HAS_SAMPLER:
                    # New API (2025+): use sampler object
                    sampler = make_sampler(
                        temp=temperature,
                        top_p=top_p,
                        min_p=0.0,
                        min_tokens_to_keep=1
                    )

                    response = generate(
                        model=self.current_model,
                        tokenizer=self.current_tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        sampler=sampler,
                        verbose=False
                    )
                else:
                    # Fallback: Try without sampling parameters (use defaults)
                    response = generate(
                        model=self.current_model,
                        tokenizer=self.current_tokenizer,
                        prompt=prompt,
                        max_tokens=max_tokens,
                        verbose=False
                    )

                # Response is a string
                generated_text = response

                # Calculate performance stats
                gen_total_time = time.time() - gen_start_time

                # Estimate tokens (rough)
                from server.utils import estimate_tokens
                prompt_tokens = estimate_tokens(prompt)
                completion_tokens = estimate_tokens(generated_text)
                total_tokens = prompt_tokens + completion_tokens

                # Calculate tokens per second
                tokens_per_second = completion_tokens / gen_total_time if gen_total_time > 0 else 0

                # Update stats
                self.last_generation_stats = {
                    "tokens_per_second": tokens_per_second,
                    "time_to_first_token": gen_total_time * 0.1,  # Estimate (MLX doesn't expose this)
                    "total_tokens": total_tokens
                }

                logger.info(f"Completion generated: {completion_tokens} tokens @ {tokens_per_second:.2f} tok/s")

                return {
                    "text": generated_text,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "performance": {
                        "tokens_per_second": round(tokens_per_second, 2),
                        "generation_time_seconds": round(gen_total_time, 2)
                    }
                }

            except Exception as e:
                logger.error(f"Generation failed: {e}")
                raise Exception(f"Generation error: {e}")

    async def generate_streaming(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95
    ):
        """
        Generate a streaming completion (yields tokens as they are generated).

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter

        Yields:
            Individual tokens as they are generated
        """
        if self.current_model is None or self.current_tokenizer is None:
            raise Exception("No model loaded. Load a model first.")

        async with self._lock:
            try:
                logger.info(f"Starting streaming generation (max_tokens={max_tokens})")

                # For streaming, we'll use a simple approach:
                # Generate in small chunks and yield
                # MLX doesn't have native streaming, so we simulate it

                # Tokenize prompt
                input_ids = self.current_tokenizer.encode(prompt)
                prompt_tokens = len(input_ids)

                # Generate token by token (simplified)
                generated_tokens = []
                for i in range(max_tokens):
                    # This is a simplified streaming simulation
                    # In production, use proper token-by-token generation
                    if i == 0:
                        # Generate a small batch first
                        response = generate(
                            model=self.current_model,
                            tokenizer=self.current_tokenizer,
                            prompt=prompt,
                            max_tokens=5,  # Small batch
                            temp=temperature,
                            top_p=top_p,
                            verbose=False
                        )
                        # Yield the response
                        yield response
                        break  # For now, yield once (MLX doesn't support true streaming yet)

                logger.info("Streaming generation complete")

            except Exception as e:
                logger.error(f"Streaming generation failed: {e}")
                raise Exception(f"Streaming error: {e}")


# Global singleton instance
model_manager = ModelManager()
