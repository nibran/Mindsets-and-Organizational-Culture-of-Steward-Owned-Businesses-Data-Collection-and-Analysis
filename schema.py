Schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "company_results",
        "schema": {
            "type": "object",
            "properties": {
                "organizational_culture": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "mindsets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "mindset": {
                                "type": "string"
                            },
                            "core_attribute": {
                                "type": "string"
                            },
                            "quote": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "mindset",
                            "core_attribute",
                            "quote"
                        ]
                    }
                }
            },
            "required": [
                "organizational_culture",
                "mindsets"
            ]
        }
    }
}
