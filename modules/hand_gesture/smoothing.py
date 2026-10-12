"""
Smoothing utilities for hand tracking.
"""


class EMASmoother:
    """
    Exponential Moving Average smoother.

    Higher alpha:
        Faster response, less smoothing.

    Lower alpha:
        More smoothing, slower response.
    """

    def __init__(self, alpha: float = 0.35) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1.")

        self.alpha = alpha
        self.value = None

    def update(self, new_value: float) -> float:
        """Update and return the smoothed value."""

        if self.value is None:
            self.value = float(new_value)
        else:
            self.value = (
                self.alpha * float(new_value)
                + (1.0 - self.alpha) * self.value
            )

        return self.value

    def reset(self) -> None:
        """Clear the stored value."""

        self.value = None


class PointSmoother:
    """EMA smoother for x/y coordinates."""

    def __init__(self, alpha: float = 0.35) -> None:
        self.x = EMASmoother(alpha)
        self.y = EMASmoother(alpha)

    def update(self, x: float, y: float) -> tuple[float, float]:
        """Return smoothed x/y coordinates."""

        return (
            self.x.update(x),
            self.y.update(y),
        )

    def reset(self) -> None:
        self.x.reset()
        self.y.reset()