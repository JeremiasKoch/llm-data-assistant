import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import pandas as pd
import json
import re
import llm_setup
import langfuse

def parse_ddl_to_schema(ddl_string):
    """
    Parses a SQL DDL string (CREATE TABLE) into a dictionary of table schemas.
    """
    schemas = {}
    table_pattern = re.compile(r'CREATE(?:\s+OR\s+REPLACE)?\s+TABLE\s+`?(\w+)`?\s*\((.*?)\);', re.IGNORECASE | re.DOTALL)
    table_matches = table_pattern.finditer(ddl_string)

    for match in table_matches:
        table_name = match.group(1).lower()
        columns_part = match.group(2).strip()

        schema = {'table_name': table_name, 'columns': [], 'constraints': []}
        column_definitions = [col.strip() for col in columns_part.split(',') if col.strip()]

        for col_def in column_definitions:
            col_def_upper = col_def.upper()

            if col_def_upper.startswith(('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CONSTRAINT')):
                schema['constraints'].append(col_def.strip())
                continue

            col_def_parts = col_def.split()
            if len(col_def_parts) >= 2:
                col_name = col_def_parts[0].strip('`"').lower()
                col_type = col_def_parts[1].strip(',').upper()
                col_type_simplified = re.sub(r'\(.*\)', '', col_type).split()[0]
                is_nullable = 'NOT NULL' not in col_def_upper

                schema['columns'].append({
                    'name': col_name,
                    'type': col_type_simplified,
                    'nullable': is_nullable
                })

        schemas[table_name] = schema
    return schemas


def generate_multi_table_data(schemas, num_rows=5, temp=0.5, model='gemini-2.5-flash', extra_prompt="", max_tokens=2048):
    generated_data = {}
    for table_name, schema in schemas.items():
        column_descriptions = [f"{c['name']} ({c['type']}, Nullable: {c['nullable']})" for c in schema['columns']]
        constraints_text = "Constraints: " + "; ".join(schema['constraints'])
        context_data = ""

        prompt_text = f"""
        Generate {num_rows} rows of realistic data for the table "{table_name}".
        Schema:
        Columns: {'; '.join(column_descriptions)}.
        {constraints_text}.
        {context_data}
        
        Additional Instructions: {extra_prompt}
        
        IMPORTANT: Return the data ONLY as a valid JSON array of objects, where keys match column names.
        """
        
        llm_response = None
        llm_output_text = ""
        
        try:
            model_client = genai.GenerativeModel(model)
            config = genai.types.GenerationConfig(
                temperature=temp,
                max_output_tokens=max_tokens,
                response_mime_type="application/json"
            )

            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            llm_response = model_client.generate_content(
                contents=prompt_text,
                generation_config=config,
                safety_settings=safety_settings
            )

            if not llm_response.candidates:
                raise ValueError("The API response does not contain valid content. It may have been blocked for an unspecified reason.")

            finish_reason = llm_response.candidates[0].finish_reason.name

            if finish_reason == "MAX_TOKENS":
                error_message = f"The model reached the 'Max Tokens' limit ({max_tokens}) and could not complete the response. Please increase the limit in the interface."
                raise ValueError(error_message)
            
            if finish_reason == "SAFETY":
                error_message = f"The response for the table '{table_name}' was blocked by the API's safety filters."
                raise ValueError(error_message)

            if finish_reason != "STOP":
                error_message = f"Data generation stopped for an unexpected reason: {finish_reason}"
                raise ValueError(error_message)
            
            llm_output_text = llm_response.text
            
            json_match = re.search(r'\[.*\]', llm_output_text, re.DOTALL)
            if not json_match:
                raise json.JSONDecodeError("A valid JSON array was not found in the response.", llm_output_text, 0)

            json_string = json_match.group(0)
            df = pd.DataFrame(json.loads(json_string))
            generated_data[table_name] = df

        except (ValueError, json.JSONDecodeError) as e:
            generated_data[table_name] = pd.DataFrame({'Error': [str(e)]})
        
        except Exception as e:
            generated_data[table_name] = pd.DataFrame({'Error': [f"Unexpected API failure for {table_name}: {e}"]})

    return generated_data


def nl_to_sql(natural_language_question, schema_ddl, temp=0.0):
    system_prompt = f"""
    You are an expert Natural Language to SQL translator. Your only task is to translate the user's
    question into a valid SQL query based strictly on the following DDL schema:

    {schema_ddl}

    STRICT Rules:
    1. The only output must be the SQL query. Do not include explanations, code blocks, or comments.
    2. The SQL query must be executable against the provided schema.
    3. Use SELECT statements for all questions.
    4. Use the exact table and column names from the DDL schema.
    """

    prompt_text = f"User question: {natural_language_question}"

    if llm_setup.langfuse_client is None:
        raise ValueError("Langfuse is not initialized. Check your environment variables.")

    trace = llm_setup.langfuse_client.trace(name="NL-to-SQL-Trace")

    span = trace.span(
        name="Gemini-SQL-Call",
        input={"question": natural_language_question, "schema": schema_ddl}
    )

    try:
        model_client = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_prompt
        )

        config = genai.types.GenerationConfig(
            temperature=temp,
        )

        llm_response = model_client.generate_content(
            contents=prompt_text,
            generation_config=config
        )

        sql_query = llm_response.text.strip()
        if sql_query.startswith('```sql'):
            sql_query = sql_query.strip('```sql').strip('```').strip()
        span.end(output={"sql": sql_query})

        if sql_query.upper().startswith("SELECT"):
            return sql_query
        else:
            span.end(status="ERROR", output={"reason": "No SELECT statement"}, level="ERROR")
            return "Error: The LLM response does not appear to be a SELECT command..."

    except Exception as e:
        span.end(status="ERROR", output={"error": str(e)}, level="ERROR")
        return f"Error: Could not generate SQL. {e}"


def edit_dataframe_with_prompt(dataframe, instructions):
    """
    Takes a DataFrame and natural language instructions, and uses an LLM
    to return a new DataFrame with the modifications applied.
    """
    try:
        data_json = dataframe.to_json(orient='records')
    except Exception as e:
        return pd.DataFrame({'Error': [f"Could not convert DataFrame to JSON: {e}"]})

    system_prompt = """
    Your only task is to act as a JSON data editor. You will receive a JSON array of data and an instruction.
    You must apply the instruction to the JSON and return ONLY the modified JSON array.
    Do not add explanations, comments, or additional text. The output must be valid JSON.
    """
    
    prompt_text = f"""
    JSON data to modify:
    {data_json}

    User instruction:
    "{instructions}"

    Modified JSON:
    """

    try:
        model_client = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_prompt)
        config = genai.types.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )

        llm_response = model_client.generate_content(
            contents=prompt_text,
            generation_config=config
        )

        llm_output_text = llm_response.text.strip()
        
        json_match = re.search(r'\[.*\]', llm_output_text, re.DOTALL)
        
        if json_match:
            json_string = json_match.group(0)
            modified_data = json.loads(json_string)
            return pd.DataFrame(modified_data)
        else:
            raise json.JSONDecodeError("The LLM response did not contain valid JSON.", llm_output_text, 0)

    except Exception as e:
        return pd.DataFrame({'Error': [f"Could not modify with AI: {e}"]})