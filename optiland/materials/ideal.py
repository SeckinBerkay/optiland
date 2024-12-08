from optiland.materials.base import BaseMaterial


class IdealMaterial(BaseMaterial):
    """
    Represents an ideal material with a fixed refractive index and absorption
    coefficient for all wavelengths.

    Attributes:
        index (float): The refractive index of the material.
        absorp (float): The absorption coefficient of the material.
    """

    def __init__(self, n, k=0):
        self.index = n
        self.absorp = k

    def n(self, wavelength):
        """
        Returns the refractive index of the material.

        Args:
            wavelength (float): The wavelength of light in microns.

        Returns:
            float: The refractive index of the material.
        """
        return self.index

    def k(self, wavelength):
        """
        Returns the absorption coefficient of the material.

        Args:
            wavelength (float): The wavelength of light in microns.

        Returns:
            float: The absorption coefficient of the material.
        """
        return self.absorp

    def to_dict(self):
        """
        Returns a dictionary representation of the material.

        Returns:
            dict: A dictionary representation of the material.
        """
        material_dict = super().to_dict()
        material_dict.update({
            'index': self.index,
            'absorp': self.absorp
        })
        return material_dict

    @classmethod
    def from_dict(cls, data):
        """
        Creates a material from a dictionary representation.

        Args:
            data (dict): The dictionary representation of the material.

        Returns:
            Material: The material.
        """
        return cls(data['index'], data.get('absorp', 0))
