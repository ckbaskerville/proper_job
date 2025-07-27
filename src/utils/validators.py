"""Input validation utilities."""

from typing import Optional, Union, List, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class Validator:
    """Collection of validation methods."""

    @staticmethod
    def validate_positive_number(
            value: Union[int, float, str],
            field_name: str
    ) -> float:
        """Validate that a value is a positive number.

        Args:
            value: Value to validate
            field_name: Name of field for error messages

        Returns:
            Validated number as float

        Raises:
            ValidationError: If validation fails
        """
        try:
            num = float(value)
            if num <= 0:
                raise ValidationError(
                    f"{field_name} must be greater than 0"
                )
            return num
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a valid number"
            )

    @staticmethod
    def validate_non_negative_number(
            value: Union[int, float, str],
            field_name: str
    ) -> float:
        """Validate that a value is non-negative.

        Args:
            value: Value to validate
            field_name: Name of field for error messages

        Returns:
            Validated number as float

        Raises:
            ValidationError: If validation fails
        """
        try:
            num = float(value)
            if num < 0:
                raise ValidationError(
                    f"{field_name} cannot be negative"
                )
            return num
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a valid number"
            )

    @staticmethod
    def validate_integer(
            value: Union[int, str],
            field_name: str,
            min_value: Optional[int] = None,
            max_value: Optional[int] = None
    ) -> int:
        """Validate that a value is an integer within range.

        Args:
            value: Value to validate
            field_name: Name of field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Validated integer

        Raises:
            ValidationError: If validation fails
        """
        try:
            num = int(value)

            if min_value is not None and num < min_value:
                raise ValidationError(
                    f"{field_name} must be at least {min_value}"
                )

            if max_value is not None and num > max_value:
                raise ValidationError(
                    f"{field_name} must be at most {max_value}"
                )

            return num
        except (ValueError, TypeError):
            raise ValidationError(
                f"{field_name} must be a valid integer"
            )

    @staticmethod
    def validate_string(
            value: str,
            field_name: str,
            min_length: Optional[int] = None,
            max_length: Optional[int] = None,
            required: bool = True
    ) -> str:
        """Validate a string value.

        Args:
            value: String to validate
            field_name: Name of field for error messages
            min_length: Minimum string length
            max_length: Maximum string length
            required: Whether the field is required

        Returns:
            Validated string (stripped)

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"{field_name} must be a string"
            )

        stripped = value.strip()

        if required and not stripped:
            raise ValidationError(
                f"{field_name} is required"
            )

        if min_length is not None and len(stripped) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters"
            )

        if max_length is not None and len(stripped) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters"
            )

        return stripped

    @staticmethod
    def validate_dimensions(
            height: Union[float, str],
            width: Union[float, str],
            depth: Union[float, str]
    ) -> Tuple[float, float, float]:
        """Validate cabinet dimensions.

        Args:
            height: Height value
            width: Width value
            depth: Depth value

        Returns:
            Tuple of validated dimensions

        Raises:
            ValidationError: If any dimension is invalid
        """
        from src.config.constants import MIN_DIMENSION, MAX_DIMENSION

        validated_height = Validator.validate_positive_number(
            height, "Height"
        )
        validated_width = Validator.validate_positive_number(
            width, "Width"
        )
        validated_depth = Validator.validate_positive_number(
            depth, "Depth"
        )

        # Check reasonable limits
        for value, name in [
            (validated_height, "Height"),
            (validated_width, "Width"),
            (validated_depth, "Depth")
        ]:
            if value < MIN_DIMENSION or value > MAX_DIMENSION:
                raise ValidationError(
                    f"{name} must be between {MIN_DIMENSION} and "
                    f"{MAX_DIMENSION} mm"
                )

        return validated_height, validated_width, validated_depth

    @staticmethod
    def validate_choice(
            value: str,
            choices: List[str],
            field_name: str
    ) -> str:
        """Validate that a value is one of allowed choices.

        Args:
            value: Value to validate
            choices: List of valid choices
            field_name: Name of field for error messages

        Returns:
            Validated choice

        Raises:
            ValidationError: If value not in choices
        """
        if value not in choices:
            raise ValidationError(
                f"{field_name} must be one of: {', '.join(choices)}"
            )
        return value
