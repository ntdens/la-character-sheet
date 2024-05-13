import pandas as pd
from pandas.api.types import is_numeric_dtype
import streamlit as st


APP_PATH = 'http://localhost:8501'

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()
    df['Spell'] = df['Spell'].astype(str)
    df = df.fillna('None')
    modification_container = st.container()

    with modification_container:
        for column in df.columns:
            left, right = st.columns((1, 20))
            if is_numeric_dtype(df[column]):
                _min = df[column].min()
                _max = df[column].max()
                if _min != _max:
                    if not df.empty:
                        user_num_input = right.slider(
                            f"{column}",
                            min_value=_min,
                            max_value=_max,
                            value=(_min, _max),
                            step=1,
                        )
                        df = df[df[column].between(*user_num_input, inclusive='both')]
            # Treat columns with < 10 unique values as categorical
            elif isinstance(df[column], pd.CategoricalDtype) or df[column].nunique() < 10:
                if column == 'Spell':
                    user_spell_input = right.selectbox(
                        'Spell?',
                        ['', 'Yes', 'No'],
                    )
                    if user_spell_input == 'Yes':
                        df = df[df['Spell'] == 'True']
                    elif user_spell_input == 'No':
                        df = df[df['Spell'] == 'False']
                else:
                    user_cat_input = right.multiselect(
                        f"{column}",
                        df[column].unique(),
                        default=list(df[column].unique()),
                    )
                    df = df[df[column].isin(user_cat_input)]
            else:
                user_text_input = right.text_input(
                    f"Search in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.lower().str.contains(user_text_input.lower())]
        return df