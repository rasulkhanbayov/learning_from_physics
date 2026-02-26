"""
Unified physics loss. Works identically for N=1 and N>1.
For N=1: exactly the original paper's Eq. 13 (MSE + KL).
"""

import torch


def physics_loss(
    Z_encoded: torch.Tensor,
    Z_predicted: torch.Tensor,
    prior_mu: float = 0.0,
    prior_sigma: float = 1.0,
) -> torch.Tensor:
    """
    Unified loss. No branching on N.

    Args:
        Z_encoded: [batch, N, d]
        Z_predicted: [batch, N, d]
        prior_mu, prior_sigma: target N(prior_mu, prior_sigma^2)

    Returns:
        scalar: L1 + L2
    """
    # L1: prediction error
    L1 = torch.mean((Z_encoded - Z_predicted) ** 2)

    # L2: KL over batch (flatten N and d)
    z_flat = Z_encoded.reshape(Z_encoded.shape[0], -1)  # [batch, N*d]
    total_dim = z_flat.shape[1]

    mu_z = z_flat.mean(dim=0)
    var_z = z_flat.var(dim=0) + 1e-8

    prior_var = prior_sigma ** 2
    # KL(N(mu_z, var_z) || N(prior_mu, prior_var)); paper Eq. 12-13 when prior N(0,1)
    L2 = -0.5 * torch.mean(
        1
        + torch.log(var_z.clamp(min=1e-8))
        - ((mu_z - prior_mu) ** 2) / prior_var
        - var_z / prior_var
    )

    return L1 + L2
