import streamlit as st
import pandas as pd
import tempfile 
import plotly.express as px
import uuid

# Reusable function for Plotly charts with unique IDs
def plot_interactive_line_chart(data, x_column, y_columns, title, x_label, y_label, legend_title):
    """
    Creates and displays an interactive Plotly line chart in Streamlit with a unique ID.

    Parameters:
        data (pd.DataFrame): The DataFrame containing the data.
        x_column (str): The column name for the x-axis.
        y_columns (list): A list of column names for the y-axis.
        title (str): The title of the chart.
        x_label (str): The label for the x-axis.
        y_label (str): The label for the y-axis.
        legend_title (str): The title for the legend.
    """
    # Generate a unique ID for the plot
    unique_id = str(uuid.uuid4())

    # Create the Plotly line chart
    fig = px.line(
        data,
        x=x_column,
        y=y_columns,
        markers=True,
        labels={"value": y_label, "variable": legend_title},
        title=f"{title}"  # Append the unique ID to the title
    )
    # Remove space around the chart and configure the x-axis to start from the edge
    fig.update_layout(
        xaxis=dict(
            title=x_label,
            autorange=False,
            range=[0, data[x_column].max()],  # Start from 0 to the max of your x-axis column
            zeroline=False,  # Remove any zero line
            showline=True,  # Show the main line on the x-axis
            showgrid=False,  # Remove grid lines for a cleaner look
        ),
        yaxis=dict(
            title=y_label
        ),
        legend=dict(
            title=legend_title,
            orientation="h",  # Horizontal legend
            y=-0.2,  # Adjust position to place it below the chart
            x=0.5,
            xanchor="center",
        ),
        title_x=0.5,  # Center-align the title
        margin=dict(l=0, r=0, t=50, b=0),  # Remove all margins
        template="plotly_white"
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig)

# Function to split Timestamp into Date and Time columns and sort by both
def split_and_sort_timestamp(df, timestamp_col):
    # Split the timestamp into Date and Time
    df['Date'] = df[timestamp_col].str.split('T').str[0]
    df['Time'] = df[timestamp_col].str.split('T').str[1].str.split('.').str[0]

    # Drop the original Timestamp column
    df = df.drop(columns=[timestamp_col])

    # Sort by Date and Time
    df = df.sort_values(by=['Date', 'Time']).reset_index(drop=True)

    return df

def process_measurements(file):
    # Read the input file into a DataFrame
    data = []
    
    for line in file.getvalue().decode("utf-8").splitlines():  # Decode file bytes and split lines
        if "Exception while processing environment." in line or "ProcessingTime;TimeStamp;Iteration;R20_Height_Left;R21_Height_Right;R30_Distance_Distance;R31_DistanceNEW;R_Current_CartNum;RadiusX;ExtractedResults" in line:
            continue  # Skip lines containing the specified pattern

        parts = line.strip().split(';')

        # Ensure the row has enough columns
        if len(parts) < 10:  # Adjusted to 10 based on your columns
            continue

        try:
            carrier = int(parts[3].split('.')[0])  # Remove .000 from the carrier if it's valid
            R20_Height_Left = float(parts[4]) if parts[4] else 0
            R21_Height_Right = float(parts[5]) if parts[5] else 0
            R30_Distance = float(parts[6]) if parts[6] else 0
            R31_Distance = float(parts[7]) if parts[7] else 0
            R32_Diameter_LEFT = float(parts[8]) if parts[8] else 0
            R33_Diameter_RIGHT = float(parts[9]) if parts[9] else 0
            timestamp = parts[1]  # Extract timestamp

            data.append([timestamp, carrier, R20_Height_Left, R21_Height_Right, R30_Distance, R31_Distance, R32_Diameter_LEFT, R33_Diameter_RIGHT])

        except ValueError:
            continue  # Skip invalid rows

    # Create DataFrame
    df = pd.DataFrame(data, columns=['Timestamp', 'Carrier', 'R20_Height_Left', 'R21_Height_Right', 'R30_Distance', 'R31_Distance', 'R32_Diameter_LEFT', "R33_Diameter_RIGHT"])
    return df

st.set_page_config(layout='wide')
# Streamlit App
st.title("Measurement Data Processor")

# File uploader
uploaded_file = st.file_uploader("Upload a Text File", type="txt")
if st.button('Process Data'):
    if uploaded_file is not None:
        with st.spinner('Please wait processing your data...'):
            try:
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file.flush()
                    temp_file_path = temp_file.name
                    df = process_measurements(uploaded_file)
                    # Split and sort by Date and Time
                    dataset = split_and_sort_timestamp(df, 'Timestamp')
                    dataset = dataset.fillna(0)
                    # Filter carriers greater than 667
                    dataset = dataset[dataset['Carrier'] <= 667]
                    dataset = dataset[dataset['Carrier'] != 0]
                    dataset['R32_R33_Diameter_AVG'] = (dataset['R32_Diameter_LEFT'] + dataset['R33_Diameter_RIGHT'])/2
                    # Assuming your original DataFrame is named 'df'
                    columns_to_average = [
                        'R20_Height_Left', 'R21_Height_Right', 'R30_Distance', 
                        'R31_Distance', 'R32_Diameter_LEFT', 'R33_Diameter_RIGHT', 
                        'R32_R33_Diameter_AVG'
                    ]

                    # Group by 'Carrier' and calculate the mean for the specified columns
                    grouped_df = dataset.groupby('Carrier')[columns_to_average].mean().reset_index()
                    
                    ploter = grouped_df[~(grouped_df['R31_Distance'] > 8)]
                    
                    
                    tab_1, tab_2 = st.tabs(['Main data','Graphs'])
                    with tab_1:
                        st.dataframe(dataset,use_container_width=True)
                        st.dataframe(grouped_df,use_container_width=True)
                        st.dataframe(ploter, use_container_width=True)
                        
                        
                    with tab_2:
                        # Plot the first graph
                        plot_interactive_line_chart(
                            data=ploter,
                            x_column="Carrier",
                            y_columns=["R30_Distance"],
                            title="Interactive Line Chart: Carrier vs. R30_Distance",
                            x_label="Carrier",
                            y_label="Distance",
                            legend_title="Measurements"
                        )

                        # Plot the second graph
                        plot_interactive_line_chart(
                            data=ploter,
                            x_column="Carrier",
                            y_columns=["R32_R33_Diameter_AVG"],
                            title="Interactive Line Chart: Carrier vs. R32_R33_Diameter_AVG",
                            x_label="Carrier",
                            y_label="Value",
                            legend_title="Metrics"
                        )
                        # Plot the third graph
                        plot_interactive_line_chart(
                            data=ploter,
                            x_column="Carrier",
                            y_columns=["R32_Diameter_LEFT"],
                            title="Interactive Line Chart: Carrier vs. R32_Diameter_LEFT",
                            x_label="Carrier",
                            y_label="Value",
                            legend_title="Metrics"
                        )
                        # Plot the fourth graph
                        plot_interactive_line_chart(
                            data=ploter,
                            x_column="Carrier",
                            y_columns=["R33_Diameter_RIGHT"],
                            title="Interactive Line Chart: Carrier vs. R33_Diameter_RIGHT",
                            x_label="Carrier",
                            y_label="Value",
                            legend_title="Metrics"
                        )
                        

            except Exception as e:
                    st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a text file to get started.")
