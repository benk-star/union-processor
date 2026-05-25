import streamlit as st
import pandas as pd
import numpy as np

# -----------------
# 1. CORE LOGIC
# -----------------
def process_union_data(df):
    # Ensure column names match exactly what is in your file. 
    # Adjust these string variables if your Excel headers are slightly different (e.g. "Paid_CC1_Code")
    cc1_col = 'Paid CC1 Code'
    union_col = 'Union Deduction'
    hours_col = 'Hours'
    last_name_col = 'Last Name'
    first_name_col = 'First Name'

    # 1. Remove rows with Paid CC1 Code = 100 or 300
    df = df[~df[cc1_col].isin([100, 300])].copy()

    # 2. Separate Error Records
    # Condition: Union Deduction = 0 and Hours > 0
    error_mask = (df[union_col] == 0) & (df[hours_col] > 0)
    error_df = df[error_mask].copy()

    # 3. Main processing file (everyone not in the error file)
    main_df = df[~error_mask].copy()

    # 4. Calculate new Union Deduction based on Hours for the main file
    def calculate_deduction(hours):
        if pd.isna(hours):
            return 0
        if hours <= 21:
            return 0
        elif 21 < hours <= 80:
            return 18
        elif 81 <= hours <= 120:
            return 23
        elif hours >= 121:
            return 28
        return 0

    main_df[union_col] = main_df[hours_col].apply(calculate_deduction)

    # 5. Sort by Last Name and First Name
    sort_columns = []
    if last_name_col in main_df.columns: sort_columns.append(last_name_col)
    if first_name_col in main_df.columns: sort_columns.append(first_name_col)
    
    if sort_columns:
        main_df = main_df.sort_values(by=sort_columns)
        error_df = error_df.sort_values(by=sort_columns)

    # 6. Sum Union Deduction column at the end
    total_deduction = main_df[union_col].sum()

    # 7. Remove Paid CC1 Code and Hours from MAIN output file
    cols_to_drop = [cc1_col, hours_col]
    main_df = main_df.drop(columns=[c for c in cols_to_drop if c in main_df.columns])

    # Append the sum to the bottom of the main file
    sum_row = {col: '' for col in main_df.columns} # Create a blank row
    sum_row[union_col] = total_deduction
    # Put the word "TOTAL" in the very first column so you know what the row is
    sum_row[main_df.columns[0]] = 'TOTAL' 
    
    # Add the total row to the dataframe
    main_df = pd.concat([main_df, pd.DataFrame([sum_row])], ignore_index=True)

    return main_df, error_df

# -----------------
# 2. STREAMLIT UI
# -----------------
st.set_page_config(page_title="Union Deduction Processor", page_icon="🏢")
st.title("🏢 Union Deduction Processor")
st.markdown("Upload your raw data. The system will filter CC1 codes, calculate union dues based on hours, and separate errors.")

uploaded_file = st.file_uploader("Upload your raw CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # Check if CSV or Excel
        if uploaded_file.name.endswith('.csv'):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
            
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        with st.spinner("Applying business rules..."):
            main_processed, error_processed = process_union_data(raw_df)
            
        st.success("✅ Processing Complete!")
        
        st.subheader("📥 Download Your Files")
        
        col1, col2 = st.columns(2)
        
        # Main File Download Button
        main_csv = main_processed.to_csv(index=False).encode('utf-8')
        col1.download_button(
            label="⬇️ Download Main File",
            data=main_csv,
            file_name=f"Processed_Main_{uploaded_file.name.replace('.xlsx', '.csv')}",
            mime="text/csv",
        )
        
        # Error File Download Button (Only shows if errors exist!)
        if len(error_processed) > 0:
            st.warning(f"⚠️ {len(error_processed)} records found with Union Deduction = 0 but Hours > 0.")
            error_csv = error_processed.to_csv(index=False).encode('utf-8')
            col2.download_button(
                label="⬇️ Download Error File",
                data=error_csv,
                file_name=f"Errors_{uploaded_file.name.replace('.xlsx', '.csv')}",
                mime="text/csv",
            )
        else:
            st.info("🎉 No error records found in this batch!")
            
    except KeyError as e:
        st.error(f"Missing Column Error: Could not find the column {e} in your file. Please check your spelling!")
    except Exception as e:
        st.error(f"An error occurred: {e}")