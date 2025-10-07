import streamlit as st
import pandas as pd
import io
import zipfile
from genai_data import parse_ddl_to_schema, generate_multi_table_data, nl_to_sql, edit_dataframe_with_prompt
from database_utils import get_db_schema_for_llm, run_sql_query, setup_db_with_data


if 'menu_selection' not in st.session_state:
    st.session_state.menu_selection = "Data Generation"
if 'generated_tables' not in st.session_state:
    st.session_state['generated_tables'] = {}
if 'selected_table_name' not in st.session_state:
    st.session_state['selected_table_name'] = None

st.set_page_config(layout="wide")

with st.sidebar:
    st.subheader("Data Assistant")
    st.markdown("")

    if st.button("Data Generation", use_container_width=True, key='btn_data_gen'):
        st.session_state.menu_selection = "Data Generation"

    if st.button("Talk to your data", use_container_width=True, key='btn_talk_data'):
        st.session_state.menu_selection = "Talk to your data"


if st.session_state.menu_selection == "Data Generation":

    with st.container(border=True):

        prompt = st.text_area(
            "Prompt",
            height=64,
            placeholder="Enter your prompt here...",
            key='llm_prompt'
        )
        
        col_btn, col_txt = st.columns([1, 4])
        uploaded_file = col_btn.file_uploader(
            "Upload DDL Schema",
            type=["sql", "ddl", "txt"],
            label_visibility="collapsed"
        )
        col_txt.markdown("Supported formats: SQL, JSON")

        st.markdown("---")
        
        col_temp, col_rows, col_max_token = st.columns(3)
        
        with col_temp:
            st.text("Temperature (Creativity)")
            temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.5, step=0.01, label_visibility="collapsed")
            
        with col_max_token:
            st.text("Max Tokens")
            max_tokens = st.number_input("Max Tokens", min_value=1, value=2048, label_visibility="collapsed")
            
        
        if st.button("Generate", use_container_width=True):
            
            if uploaded_file is not None:
                with st.spinner('1. Parsing DDL, 2. Generating data with Gemini, and 3. Inserting into PostgreSQL...'):
                    
                    ddl_string = uploaded_file.read().decode('utf-8')
                    schemas = parse_ddl_to_schema(ddl_string)
                    
                    if not schemas:
                        st.error("No CREATE TABLE commands were found in the DDL file. Please check the format.")
                    else:
                        model_name = 'gemini-2.5-flash'
                        st.session_state['generated_tables'] = generate_multi_table_data(
                            schemas=schemas,
                            temp=temperature,
                            model=model_name,
                            extra_prompt=prompt,
                            max_tokens=max_tokens
                        )
                        
                        setup_result = setup_db_with_data(st.session_state['generated_tables'])
                        
                        if "Error" in setup_result:
                            st.error(f"Error configuring database: {setup_result}. Check the application log.")
                        else:
                            st.session_state['selected_table_name'] = list(schemas.keys())[0]
                            st.success(f"Generation completed for {len(schemas)} table(s) and **data inserted into PostgreSQL**.")
            
            else:
                st.error("Please upload a DDL file.")


    with st.container(border=True):
        
        table_names = list(st.session_state['generated_tables'].keys())
        
        col_title, col_table_select, col_download = st.columns([3, 1, 1])

        col_title.markdown("### Data Preview")
        
        if table_names:
            selected_name = col_table_select.selectbox(
                "Select Table",
                table_names,
                key='table_selector',
                label_visibility="collapsed",
                index=table_names.index(st.session_state['selected_table_name']) if st.session_state['selected_table_name'] in table_names else 0
            )
            st.session_state['selected_table_name'] = selected_name

            @st.cache_data
            def create_zip_archive(tables_dict):
                zip_io = io.BytesIO()
                with zipfile.ZipFile(zip_io, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for name, df in tables_dict.items():
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        zipf.writestr(f"{name}_data.csv", csv_data)
                zip_io.seek(0)
                return zip_io

            zip_bytes = create_zip_archive(st.session_state['generated_tables'])
            
            col_download.download_button(
                label="Download ZIP",
                data=zip_bytes,
                file_name="generated_data.zip",
                mime="application/zip",
                use_container_width=True
            )

            current_df = st.session_state['generated_tables'][selected_name]
            
            edited_df = st.data_editor(current_df, use_container_width=True, num_rows="dynamic", key="data_editor")

            st.markdown("#### Quick Modifications")
            col_instructions, col_btn_subtmit = st.columns([5,1])

            instructions = col_instructions.text_input(
                "Editing Instructions",
                label_visibility="collapsed",
                placeholder=f"Ex: Change the price of the 3 most expensive products in the table {selected_name} to 99.99"
            )
            
            if col_btn_subtmit.button("Submit Edit", use_container_width=True):
                if instructions:
                    with st.spinner("Modifying data..."):
                        current_df = edited_df

                        modified_df = edit_dataframe_with_prompt(current_df, instructions)

                        if 'Error' in modified_df.columns:
                            st.error(modified_df['Error'].iloc[0])
                        else:
                            st.session_state['generated_tables'][selected_name] = modified_df
                            setup_db_with_data({selected_name: modified_df})
                            st.toast("Updated data!")
                            st.rerun()

                else:
                    st.session_state['generated_tables'][selected_name] = edited_df
                    setup_db_with_data({selected_name: edited_df})
                    st.toast("Data updated manually.")
        
        else:
            st.info("Upload a DDL file and click 'Generate' to view the data.")
            st.dataframe(pd.DataFrame({'ID': [], 'Name': []}), use_container_width=True, hide_index=True)


if st.session_state.menu_selection == "Talk to your data":
    
    st.subheader("Generate your query")

    if not st.session_state.get('generated_tables'):
        st.warning("You must first generate data in the 'Data Generation' tab to query.")
    else:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if isinstance(message["content"], pd.DataFrame):
                    st.dataframe(message["content"], use_container_width=True)
                else:
                    st.markdown(message["content"])

        if question := st.chat_input("Ex: What is the name and price of the most expensive product?"):
            
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Translating to SQL and querying PostgreSQL..."):
                    
                    db_schema_ddl = get_db_schema_for_llm(st.session_state['generated_tables'])
                    
                    sql_query = nl_to_sql(question, db_schema_ddl, temp=0.0)
                    
                    response_container = st.container()

                    if not sql_query.startswith("Error"):
                        response_container.success("Successful SQL translation:")
                        response_container.code(sql_query, language='sql')
                        
                        result_df = run_sql_query(sql_query)
                        
                        if 'Error' in result_df.columns:
                            error_message = result_df['Error'].iloc[0]
                            response_container.error(error_message)
                            st.session_state.messages.append({"role": "assistant", "content": error_message})
                        else:
                            response_container.markdown("---")
                            response_container.subheader("Query Result")
                            response_container.dataframe(result_df, use_container_width=True, hide_index=True)
                            st.session_state.messages.append({"role": "assistant", "content": result_df})
                    else:
                        response_container.error(f"Error in translation: {sql_query}")
                        st.session_state.messages.append({"role": "assistant", "content": sql_query})