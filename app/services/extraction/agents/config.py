EXTRACTION_SCHEMA = {
    "info": {
        "store_name": "",
        "store_location": "",
        "store_contacts": [
            {"type": "", "value": ""}
        ],
        "tax_id": "",
        "receipt_id": "",
        "payment_date": "",
        "payment_time": "",
        "time_unit": ""
    },
    "items": [
        {
            "item_name": "",
            "quantity": "",
            "unit_price": "",
            "discount_label": "",
            "discount_price": "",
            "tax_label": "",
            "total_price": ""
        }
    ],
    "payment": {
        "total_items": "",
        "currency": "",
        "subtotal_price": "",
        "discounts": [
            {"discount_name": "", "amount": ""}
        ],
        "taxes": [
            {"tax_name": "", "amount": ""}
        ],
        "additional_charges": [
            {"charge_name": "", "amount": ""}
        ],
        "grand_total": "",
        "rounding": "",
        "payment_method": "",
        "tendered": "",
        "change": ""
    }
}


def get_default_extraction() -> dict:
    """Return a deep copy of the extraction schema with default values."""
    import copy
    return copy.deepcopy(EXTRACTION_SCHEMA)
