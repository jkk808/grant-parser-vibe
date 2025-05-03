"""
Functions to parse the response from Google Document AI into a more usable format.
"""

from google.cloud import documentai_v1 as documentai
import os

# --- Mapping from expected Document AI entity types to user-friendly keys ---
# NOTE: These entity type names (e.g., 'grant_fain_number', 'award_date') are GUESSES
# based on the user's example output. You may need to ADJUST these based on the
# actual 'Type=' values printed in the debug output when you run the code.
ENTITY_TYPE_MAP = {
    "grant_fain_number": "GRANT NUMBER (FAIN)",
    "award_date": "DATE OF AWARD",
    "modification_number": "MODIFICATION NUMBER",
    "program_code": "PROGRAM CODE",
    "mailing_date": "MAILING DATE",
    "action_type": "TYPE OF ACTION",
    "ach_number": "ACH#",
    "payment_method": "PAYMENT METHOD",
    "recipient_type": "RECIPIENT TYPE",
    "recipient_name_address": "RECIPIENT",  # Might be multiple entities (name, address)
    "payee_name_address": "PAYEE",  # Might be multiple entities
    "employer_identification_number": "EIN",  # Common DocAI type name
    "recipient_contact_name": "RECIPIENT CONTACT",  # Guessing based on James Maughan
    "recipient_contact_email": "RECIPIENT EMAIL",  # Guessing
    "recipient_contact_phone": "RECIPIENT PHONE",  # Guessing
    "epa_grant_specialist_name": "EPA GRANT SPECIALIST",  # Guessing
    "epa_grant_specialist_email": "EPA GRANT SPECIALIST EMAIL",  # Guessing
    "epa_grant_specialist_phone": "EPA GRANT SPECIALIST PHONE",  # Guessing
    "epa_project_officer_name": "EPA PROJECT OFFICER",  # Guessing
    "epa_project_officer_address": "EPA PROJECT OFFICER ADDRESS",  # Guessing
    "epa_project_officer_email": "EPA PROJECT OFFICER EMAIL",  # Guessing
    "epa_project_officer_phone": "EPA PROJECT OFFICER PHONE",  # Guessing
    "total_budget_period_cost": "TOTAL BUDGET PERIOD COST",
    "total_project_period_cost": "TOTAL PROJECT PERIOD COST",
    "project_period_start_date": "PROJECT PERIOD START",  # Split from range
    "project_period_end_date": "PROJECT PERIOD END",  # Split from range
    "project_period": "PROJECT PERIOD",  # May capture full range
    "budget_period_start_date": "BUDGET PERIOD START",  # Split from range
    "budget_period_end_date": "BUDGET PERIOD END",  # Split from range
    "budget_period": "BUDGET PERIOD",  # May capture full range
    "epa_issuing_office_org_address": "ISSUING OFFICE ORGANIZATION / ADDRESS",  # Guessing
    "epa_admin_office_org_address": "ADMIN OFFICE ORGANIZATION / ADDRESS",  # Guessing
    "award_agreement_date": "AWARD AGREEMENT DATE"  # Guessing based on "DATE" field
    # Add more mappings as needed based on processor output
}


def parse_doc_ai_response(doc_ai_document: documentai.Document) -> dict:
    """Parses the Document AI proto response to extract specific grant information.

    This function looks for specific entity types expected from a grant processor
    and maps them to user-friendly keys based on the ENTITY_TYPE_MAP.

    Args:
        doc_ai_document: The Document object returned by the Document AI API.

    Returns:
        A dictionary where keys are user-friendly field names (e.g., "GRANT NUMBER (FAIN)")
        and values are the extracted text. It prioritizes normalized values for dates/numbers
        where available and potentially useful.
    """
    processed_entity_ids = set()  # Keep track of entities already mapped
    output_log_file = 'output.txt'  # Define filename

    print(
        f"Attempting to parse {len(doc_ai_document.entities)} entities from Document AI response."
    )
    print(
        f"Detailed entity processing logs will be written to: {output_log_file}"
    )  # Inform user

    if not doc_ai_document.entities:
        print("Warning: The Document AI response contained no entities.")
        return parsed_data

    # --- Open log file once before the loop (overwrite existing) ---
    try:
        with open(output_log_file, 'w', encoding='utf-8') as log_f:
            log_f.write(
                "--- Document AI Entity Processing Log ---\\n\\n"
            )  # Write header

            # --- Prioritize mapping specific known entity types ---
            for entity in doc_ai_document.entities:
                entity_type = entity.type_ or "NO_TYPE"
                value = entity.mention_text.strip() if entity.mention_text else ""
                # Use normalized value if it exists, otherwise use mention text
                output_value = (
                    entity.normalized_value.text
                    if entity.normalized_value and entity.normalized_value.text
                    else value
                )
                confidence = entity.confidence
                entity_id = entity.id  # Use ID to track processed entities

                # Format the debug content
                log_content = (
                    f"Processing entity: ID='{entity_id}', Type='{entity_type}', "
                    f"Value='{value}', Confidence={confidence:.4f}\\n"
                )
                # Also include normalized value if present
                if entity.normalized_value and entity.normalized_value.text:
                    log_content += (
                        f"  Normalized Value: '{entity.normalized_value.text}'\\n"
                    )

                # Print truncated version to console
                console_content = (
                    f"  Processing entity: ID='{entity_id}', Type='{entity_type}', "
                    f"Value='{value[:70].strip()}...', Confidence={confidence:.3f}"
                )
                # print(console_content)

                # --- Append the full details to the log file ---
                log_f.write(log_content)

                # Check if this entity type is in our specific map
                # if entity_type in ENTITY_TYPE_MAP:
                #     output_key = ENTITY_TYPE_MAP[entity_type]
                #     map_log = ""  # Log mapping action to file as well

                #     #  Handle multiple values for the same key
                #     if output_key not in parsed_data:
                #         parsed_data[output_key] = [output_value]  # Store as a list
                #         map_log = (
                #             f"    -> Mapping Type='{entity_type}' to Key='{output_key}' "
                #             f"with Value='{output_value}'\\n"
                #         )
                #         print(
                #             f"    -> Mapping Type='{entity_type}' to Key='{output_key}' with Value='{output_value}'"
                #         )  # Keep console output
                #         processed_entity_ids.add(entity_id)
                #     else:
                #         parsed_data[output_key].append(
                #             output_value
                #         )  # Append to the list
                #         map_log = (
                #             f"    -> Type='{entity_type}' maps to Key='{output_key}'. "
                #             f"Adding value '{output_value}' to existing list.\\n"
                #         )
                #         print(
                #             f"    -> Type='{entity_type}' maps to Key='{output_key}'. "
                #             f"Adding value '{output_value}' to existing list."
                #         )
                #     log_f.write(map_log)  # Write mapping info to file
                # else:
                #     log_f.write(
                #         "    -> Type not in ENTITY_TYPE_MAP.\\n"
                #     )  # Indicate if not mapped

            # --- Capture any remaining unmapped entities ---
            unmapped_entities = {}
            # log_f.write("\\n--- Unmapped Entities ---\\n")  # Section in log file
            # for entity in doc_ai_document.entities:
            #     if entity.id not in processed_entity_ids:
            #         entity_type = entity.type_ or "NO_TYPE"
            #         value = entity.mention_text or ""
            #         normalized_value = (
            #             entity.normalized_value.text if entity.normalized_value else None
            #         )
            #         confidence = entity.confidence

            #         # Log unmapped entity details to file
            #         unmapped_log = (
            #             f"Unmapped: Type='{entity_type}', Value='{value}', "
            #             f"Confidence={confidence:.4f}\\n"
            #         )
            #         if normalized_value:
            #             unmapped_log += f"  Normalized Value: '{normalized_value}'\\n"
            #         log_f.write(unmapped_log)

            #         entity_info = {
            #             "text": value,
            #             "normalized_text": normalized_value,
            #             "confidence": round(confidence, 4),
            #         }
            #         if entity_type not in unmapped_entities:
            #             unmapped_entities[entity_type] = []
            #         unmapped_entities[entity_type].append(entity_info)

            # if unmapped_entities:
            #     print(
            #         f"\\nFound {sum(len(v) for v in unmapped_entities.values())} unmapped "
            #         f"entities (see {output_log_file} for details)."
            #     )
            #     parsed_data["_unmapped_entities"] = (
            #         unmapped_entities  # Include for inspection
            #     )
            # else:
            #     log_f.write("(None)\\n")
        if doc_ai_document and doc_ai_document.text:
            parsed_data = doc_ai_document.text[:300]
            print(parsed_data)

    except IOError as e:
        print(f"Error writing to log file {output_log_file}: {e}")

    print(f"\\nParsing complete. Mapped data: {parsed_data}")
    return parsed_data

