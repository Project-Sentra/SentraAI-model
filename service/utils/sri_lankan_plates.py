"""
Sri Lankan License Plate Validation and Formatting
Supports multiple Sri Lankan plate formats.
"""
import re
import string

# Sri Lankan province codes
SL_PROVINCE_CODES = {
    'WP': 'Western Province',
    'CP': 'Central Province',
    'SP': 'Southern Province',
    'NW': 'North Western Province',
    'NC': 'North Central Province',
    'UP': 'Uva Province',
    'SG': 'Sabaragamuwa Province',
    'EP': 'Eastern Province',
    'NP': 'Northern Province',
}

# Common letter/number misrecognitions for OCR correction
CHAR_TO_INT = {
    'O': '0', 'Q': '0', 'D': '0',
    'I': '1', 'L': '1',
    'Z': '2',
    'J': '3',
    'A': '4',
    'S': '5',
    'G': '6', 'B': '8',
    'T': '7',
    'B': '8',
}

INT_TO_CHAR = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '3': 'J',
    '4': 'A',
    '5': 'S',
    '6': 'G',
    '7': 'T',
    '8': 'B',
}


def normalize_text(text: str) -> str:
    """Remove spaces and convert to uppercase"""
    return text.upper().replace(' ', '').replace('-', '')


def validate_modern_format(text: str) -> tuple[bool, str | None]:
    """
    Validate modern Sri Lankan plate format: WP CA-1234 or WP CAB-1234
    Format: [Province 2 chars][Letters 2-3][Numbers 4]
    """
    normalized = normalize_text(text)

    # Pattern: 2 province chars + 2-3 letters + 4 numbers
    pattern = r'^([A-Z]{2})([A-Z]{2,3})(\d{4})$'
    match = re.match(pattern, normalized)

    if match:
        province, letters, numbers = match.groups()
        if province in SL_PROVINCE_CODES:
            formatted = f"{province} {letters}-{numbers}"
            return True, formatted

    return False, None


def validate_provincial_numeric(text: str) -> tuple[bool, str | None]:
    """
    Validate provincial numeric format: WP 1234
    Format: [Province 2 chars][Numbers 4]
    """
    normalized = normalize_text(text)

    pattern = r'^([A-Z]{2})(\d{4})$'
    match = re.match(pattern, normalized)

    if match:
        province, numbers = match.groups()
        if province in SL_PROVINCE_CODES:
            formatted = f"{province} {numbers}"
            return True, formatted

    return False, None


def validate_old_format(text: str) -> tuple[bool, str | None]:
    """
    Validate old Sri Lankan format: 12-3456 or 123-4567
    Format: [Numbers 2-3]-[Numbers 4]
    """
    normalized = normalize_text(text)

    # Pattern: 2-3 numbers + 4 numbers
    pattern = r'^(\d{2,3})(\d{4})$'
    match = re.match(pattern, normalized)

    if match:
        prefix, numbers = match.groups()
        formatted = f"{prefix}-{numbers}"
        return True, formatted

    return False, None


def validate_special_format(text: str) -> tuple[bool, str | None]:
    """
    Validate special vehicle format: CAR 1234, GOV 1234
    Format: [Letters 3][Numbers 4]
    """
    normalized = normalize_text(text)

    pattern = r'^([A-Z]{3})(\d{4})$'
    match = re.match(pattern, normalized)

    if match:
        prefix, numbers = match.groups()
        formatted = f"{prefix} {numbers}"
        return True, formatted

    return False, None


def correct_ocr_errors(text: str, expected_positions: dict) -> str:
    """
    Correct common OCR misrecognitions based on expected character types.
    expected_positions: dict mapping position index to 'letter' or 'digit'
    """
    corrected = list(text)

    for pos, expected_type in expected_positions.items():
        if pos >= len(corrected):
            continue

        char = corrected[pos]

        if expected_type == 'digit' and char in CHAR_TO_INT:
            corrected[pos] = CHAR_TO_INT[char]
        elif expected_type == 'letter' and char in INT_TO_CHAR:
            corrected[pos] = INT_TO_CHAR[char]

    return ''.join(corrected)


def validate_sri_lankan_plate(text: str) -> tuple[bool, str | None, str]:
    """
    Validate and format a Sri Lankan license plate.

    Returns:
        tuple: (is_valid, formatted_plate, plate_type)
    """
    if not text:
        return False, None, "empty"

    normalized = normalize_text(text)

    # Try each format in order of likelihood
    validators = [
        (validate_modern_format, "modern"),
        (validate_provincial_numeric, "provincial"),
        (validate_old_format, "old"),
        (validate_special_format, "special"),
    ]

    for validator, plate_type in validators:
        is_valid, formatted = validator(normalized)
        if is_valid:
            return True, formatted, plate_type

    return False, None, "unknown"


def smart_format_plate(raw_text: str) -> tuple[str | None, float]:
    """
    Attempt to intelligently format a raw OCR result into a valid plate.
    Returns the formatted plate and a confidence modifier.
    """
    if not raw_text:
        return None, 0.0

    normalized = normalize_text(raw_text)

    # Remove common noise characters
    cleaned = re.sub(r'[^A-Z0-9]', '', normalized)

    if len(cleaned) < 4:
        return None, 0.0

    # Try validation first
    is_valid, formatted, plate_type = validate_sri_lankan_plate(cleaned)

    if is_valid:
        return formatted, 1.0

    # Try to infer format based on length and character patterns
    if len(cleaned) >= 8:
        # Likely modern format: WPCAB1234
        province = cleaned[:2]
        letters = cleaned[2:-4]
        numbers = cleaned[-4:]

        # Correct OCR errors
        expected = {i: 'letter' for i in range(len(province) + len(letters))}
        expected.update({i: 'digit' for i in range(len(province) + len(letters), len(cleaned))})
        corrected = correct_ocr_errors(cleaned, expected)

        is_valid, formatted = validate_modern_format(corrected)
        if is_valid:
            return formatted, 0.9

    elif len(cleaned) >= 6:
        # Could be WP1234 or 12-3456 or CAR1234

        # Try provincial numeric
        expected = {0: 'letter', 1: 'letter'}
        expected.update({i: 'digit' for i in range(2, 6)})
        corrected = correct_ocr_errors(cleaned[:6], expected)
        is_valid, formatted = validate_provincial_numeric(corrected)
        if is_valid:
            return formatted, 0.85

        # Try old format
        expected = {i: 'digit' for i in range(len(cleaned))}
        corrected = correct_ocr_errors(cleaned, expected)
        is_valid, formatted = validate_old_format(corrected)
        if is_valid:
            return formatted, 0.85

        # Try special format
        if len(cleaned) >= 7:
            expected = {0: 'letter', 1: 'letter', 2: 'letter'}
            expected.update({i: 'digit' for i in range(3, 7)})
            corrected = correct_ocr_errors(cleaned[:7], expected)
            is_valid, formatted = validate_special_format(corrected)
            if is_valid:
                return formatted, 0.85

    # Return cleaned but unformatted if nothing else works
    return cleaned, 0.5


# Utility functions for testing
def is_valid_plate(text: str) -> bool:
    """Quick check if text is a valid Sri Lankan plate"""
    is_valid, _, _ = validate_sri_lankan_plate(text)
    return is_valid


def get_province_name(plate: str) -> str | None:
    """Get province name from a plate number"""
    normalized = normalize_text(plate)
    if len(normalized) >= 2:
        code = normalized[:2]
        return SL_PROVINCE_CODES.get(code)
    return None
