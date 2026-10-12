"""
WhisperDeepfakeMLPHead Reference Module (piotrkawa Interspeech 2023).
Exports the exact PyTorch neural architecture for extracting acoustic spoofing
representations from Whisper encoder hidden states.
"""

import torch
import torch.nn as nn


class WhisperDeepfakeMLPHead(nn.Module):
    """
    Consumes Whisper encoder hidden representations (dim 768 for small)
    extracted during a single forward pass, performing temporal pooling
    and multi-layer perceptron projection to compute the spoof anomaly score.
    """

    def __init__(
        self,
        hidden_dim: int = 768,
        bottleneck_dim: int = 256,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.layer_norm = nn.LayerNorm(hidden_dim)
        self.pooling = nn.AdaptiveAvgPool1d(1)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, bottleneck_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(bottleneck_dim, 64),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, encoder_hidden_states: torch.Tensor, is_pre_pooled: bool = False) -> torch.Tensor:
        if is_pre_pooled and encoder_hidden_states.dim() == 2:
            normed = self.layer_norm(encoder_hidden_states)
            return self.mlp(normed)
        if encoder_hidden_states.dim() == 2:
            encoder_hidden_states = encoder_hidden_states.unsqueeze(0)
        normed = self.layer_norm(encoder_hidden_states)
        transposed = normed.transpose(1, 2)
        pooled = self.pooling(transposed).squeeze(-1)
        return self.mlp(pooled)
