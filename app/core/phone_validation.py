import phonenumbers

def normalize_phone(phone: str, default_region="KE") -> str:
    """
    Converts any valid local or international number to E.164 format.
    Examples:
        +254712345678 -> +254712345678
        0712345678   -> +254712345678
        0112345678   -> +254112345678
    """
    try:
        # Parse the number
        parsed = phonenumbers.parse(phone, default_region)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number")
        # Return in E.164 format
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        raise ValueError("Invalid phone number")
