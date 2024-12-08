"""Optiland Physical Apertures Module

This module provides classes to define physical apertures on optical surfaces.

Kramer Harrison, 2024
"""
from abc import ABC, abstractmethod


class BaseAperture(ABC):
    """
    Base class for physical apertures.

    Methods:
        clip(RealRays): Clips the given rays based on the aperture's shape.
    """
    _registry = {}

    def __init_subclass__(cls, **kwargs):
        """Automatically register subclasses."""
        super().__init_subclass__(**kwargs)
        BaseAperture._registry[cls.__name__] = cls

    def clip(self, rays):
        """
        Clips the given rays based on the aperture's shape.

        Parameters:
            rays (RealRays): List of rays to be clipped.

        Returns:
            list: List of clipped rays.
        """
        return rays  # pragma: no cover

    @abstractmethod
    def scale(self, scale_factor):
        """
        Scales the aperture by the given factor.

        Parameters:
            scale_factor (float): The factor by which to scale the aperture.
        """
        pass  # pragma: no cover

    def to_dict(self):
        """
        Convert the aperture to a dictionary.

        Returns:
            dict: The dictionary representation of the aperture.
        """
        return {
            'type': self.__class__.__name__
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create an aperture from a dictionary representation.

        Parameters:
            data (dict): The dictionary representation of the aperture.

        Returns:
            BaseAperture: The aperture object.
        """
        aperture_type = data['type']
        return cls._registry[aperture_type].from_dict(data)


class RadialAperture(BaseAperture):
    """
    Represents a radial aperture that clips rays based on their distance from
    the origin.

    Attributes:
        r_max (float): The maximum radius allowed for the rays.
        r_min (float): The minimum radius allowed for the rays. Defaults to 0.
    """

    def __init__(self, r_max, r_min=0):
        super().__init__()
        self.r_max = r_max
        self.r_min = r_min

    def clip(self, rays):
        """
        Clips the given rays based on their distance from the origin.

        Args:
            rays (Rays): The rays to be clipped.
        """
        radius2 = rays.x**2 + rays.y**2
        condition = (radius2 > self.r_max**2) | (radius2 < self.r_min**2)
        rays.clip(condition)

    def scale(self, scale_factor):
        """
        Scales the aperture by the given factor.

        Args:
            scale_factor (float): The factor by which to scale the aperture.
        """
        self.r_max *= scale_factor
        self.r_min *= scale_factor

    def to_dict(self):
        """
        Convert the aperture to a dictionary.

        Returns:
            dict: The dictionary representation of the aperture.
        """
        aperture_dict = super().to_dict()
        aperture_dict['r_max'] = self.r_max
        aperture_dict['r_min'] = self.r_min
        return aperture_dict

    @classmethod
    def from_dict(cls, data):
        """
        Create an aperture from a dictionary representation.

        Args:
            data (dict): The dictionary representation of the aperture.

        Returns:
            RadialAperture: The aperture object.
        """
        return cls(data['r_max'], data['r_min'])
