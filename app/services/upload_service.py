from dataclasses import dataclass

import pandas as pd

from app.services.data_loader import load_dataset
from app.services.data_validator import (
    ValidationResult,
    validate_dataset,
)


@dataclass
class UploadResult:
    """Result of processing an uploaded dataset."""

    dataframe: pd.DataFrame | None
    validation: ValidationResult | None
    error: str | None = None

    @property
    def is_successful(self) -> bool:
        """Return whether the uploaded dataset passed validation."""

        return (
            self.dataframe is not None
            and self.validation is not None
            and self.validation.is_valid
            and self.error is None
        )


def process_uploaded_dataset(file) -> UploadResult:
    """
    Load and validate an uploaded dataset.

    File-loading errors are returned as an error message.
    Validation failures return the validation details.
    """

    try:
        dataframe = load_dataset(file)

    except Exception as error:
        return UploadResult(
            dataframe=None,
            validation=None,
            error=str(error),
        )

    validation = validate_dataset(dataframe)

    return UploadResult(
        dataframe=dataframe if validation.is_valid else None,
        validation=validation,
    )