#!/usr/bin/env python3
import math
from typing import Optional

import torch
from captum.module.stochastic_gates_base import StochasticGatesBase
from torch import nn, Tensor


def _torch_empty(batch_size: int, n_gates: int, device: torch.device) -> Tensor:
    return torch.empty(batch_size, n_gates, device=device)


# torch.fx is introduced in 1.8.0
if hasattr(torch, "fx"):
    torch.fx.wrap(_torch_empty)


def _logit(inp):
    # torch.logit is introduced in 1.7.0
    if hasattr(torch, "logit"):
        return torch.logit(inp)
    else:
        return torch.log(inp) - torch.log(1 - inp)


class BinaryConcreteStochasticGates(StochasticGatesBase):
    """
    Stochastic Gates with binary concrete distribution.

    Stochastic Gates is a practical solution to add L0 norm regularization for neural
    networks. L0 regularization, which explicitly penalizes any present (non-zero)
    parameters, can help network pruning and feature selection, but directly optimizing
    L0 is a non-differentiable combinatorial problem. To surrogate L0, Stochastic Gate
    uses certain continuous probability distributions (e.g., Concrete, Gaussian) with
    hard-sigmoid rectification as a continuous smoothed Bernoulli distribution
    determining the weight of a parameter, i.e., gate. Then L0 is equal to the gates's
    non-zero probability represented by the parameters of the continuous probability
    distribution. The gate value can also be reparameterized to the distribution
    parameters with a noise. So the expected L0 can be optimized through learning
    the distribution parameters via stochastic gradients.

    BinaryConcreteStochasticGates adopts a "stretched" binary concrete distribution as
    the smoothed Bernoulli distribution of gate. The binary concrete distribution does
    not include its lower and upper boundaries, 0 and 1, which are required by a
    Bernoulli distribution, so it needs to be linearly stretched beyond both boundaries.
    Then use hard-sigmoid rectification to "fold" the parts smaller than 0 or larger
    than 1 back to 0 and 1.

    More details can be found in the
    `original paper <https://arxiv.org/abs/1712.01312>`.
    """

    def __init__(
        self,
        n_gates: int,
        mask: Optional[Tensor] = None,
        reg_weight: float = 1.0,
        temperature: float = 2.0 / 3,
        lower_bound: float = -0.1,
        upper_bound: float = 1.1,
        eps: float = 1e-8,
    ):
        """
        Args:
            n_gates (int): number of gates.

            mask (Optional[Tensor]): If provided, this allows grouping multiple
                input tensor elements to share the same stochastic gate.
                This tensor should be broadcastable to match the input shape
                and contain integers in the range 0 to n_gates - 1.
                Indices grouped to the same stochastic gate should have the same value.
                If not provided, each element in the input tensor
                (on dimensions other than dim 0 - batch dim) is gated separately.
                Default: None

            reg_weight (Optional[float]): rescaling weight for L0 regularization term.
                Default: 1.0

            temperature (float): temperature of the concrete distribution, controls
                the degree of approximation, as 0 means the original Bernoulli
                without relaxation. The value should be between 0 and 1.
                Default: 2/3

            lower_bound (float): the lower bound to "stretch" the binary concrete
                distribution
                Default: -0.1

            upper_bound (float): the upper bound to "stretch" the binary concrete
                distribution
                Default: 1.1

            eps (float): term to improve numerical stability in binary concerete
                sampling
                Default: 1e-8
        """
        super().__init__(n_gates, mask=mask, reg_weight=reg_weight)

        # avoid changing the tensor's variable name
        # when the module is used after compilation,
        # users may directly access this tensor by name
        log_alpha_param = torch.empty(n_gates)
        nn.init.normal_(log_alpha_param, mean=0.0, std=0.01)
        self.log_alpha_param = nn.Parameter(log_alpha_param)

        assert (
            0 < temperature < 1
        ), f"the temperature should be bwteen 0 and 1, received {temperature}"
        self.temperature = temperature

        assert (
            lower_bound < 0
        ), f"the stretch lower bound should smaller than 0, received {lower_bound}"
        self.lower_bound = lower_bound
        assert (
            upper_bound > 1
        ), f"the stretch upper bound should larger than 1, received {upper_bound}"
        self.upper_bound = upper_bound

        self.eps = eps

        # pre-calculate the fixed term used in active prob
        self.active_prob_offset = temperature * math.log(-lower_bound / upper_bound)

    def forward(self, *args, **kwargs):
        """
        Args:
            input_tensor (Tensor): Tensor to be gated with stochastic gates


        Outputs:
            gated_input (Tensor): Tensor of the same shape weighted by the sampled
                gate values

            l0_reg (Tensor): L0 regularization term to be optimized together with
                model loss,
                e.g. loss(model_out, target) + l0_reg
        """
        return super().forward(*args, **kwargs)

    def _sample_gate_values(self, batch_size: int) -> Tensor:
        """
        Sample gate values for each example in the batch from the binary concrete
        distributions

        Args:
            batch_size (int): input batch size

        Returns:
            gate_values (Tensor): gate value tensor of shape(batch_size, n_gates)
        """
        if self.training:
            u = _torch_empty(
                batch_size, self.n_gates, device=self.log_alpha_param.device
            )
            u.uniform_(self.eps, 1 - self.eps)
            s = torch.sigmoid((_logit(u) + self.log_alpha_param) / self.temperature)

        else:
            s = torch.sigmoid(self.log_alpha_param)
            s = s.expand(batch_size, self.n_gates)

        s_bar = s * (self.upper_bound - self.lower_bound) + self.lower_bound

        return s_bar

    def _get_gate_values(self) -> Tensor:
        """
        Get the gate values derived from learned log_alpha_param after model is trained

        Returns:
            gate_values (Tensor): value of each gate after model is trained
        """
        gate_values = (
            torch.sigmoid(self.log_alpha_param) * (self.upper_bound - self.lower_bound)
            + self.lower_bound
        )
        return torch.clamp(gate_values, min=0, max=1)

    def _get_gate_active_probs(self) -> Tensor:
        """
        Get the active probability of each gate, i.e, gate value > 0, in the binary
        concrete distributions

        Returns:
            probs (Tensor): probabilities tensor of the gates are active
                in shape(n_gates)
        """
        return torch.sigmoid(self.log_alpha_param - self.active_prob_offset)
