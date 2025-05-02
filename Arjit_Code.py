import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Function to load and preprocess dynamic emission data
@st.cache_data
def load_dynamic_data():
    file_path = r"D:\Arjit Academics\DDP\Data\Combine Data.xlsx"  # Replace with your file path
    data = pd.ExcelFile(file_path)
    df = data.parse(sheet_name=0).fillna(method='ffill')
    df.columns = df.columns.str.strip()  # Strip any whitespace from column names
    return df

# Function to load electricity and fuel data
@st.cache_data
def load_machine_data():
    electricity_file = r"D:\Arjit Academics\DDP\Months\November\Electricity.xlsx"
    fuel_file = r"D:\Arjit Academics\DDP\Months\November\Natural Fuel.xlsx"
    electricity_df = pd.read_excel(electricity_file)
    fuel_df = pd.read_excel(fuel_file)
    return electricity_df, fuel_df

# Function to filter dynamic options
def get_filtered_options(df, material, product_at_gate=None, primary_input=None):
    filtered_df = df[df['Material'] == material]
    if product_at_gate:
        filtered_df = filtered_df[filtered_df['Product at gate'] == product_at_gate]
    if primary_input:
        filtered_df = filtered_df[filtered_df['Primary input'] == primary_input]
    return filtered_df

# Streamlit UI
st.title("Enhanced CO2 Emission Calculator")

# Load data
dynamic_data = load_dynamic_data()
electricity_df, fuel_df = load_machine_data()

# Tabs for functionalities
tab1, tab2, tab3 = st.tabs(["Dynamic Material Emissions", "Machine-Based Emissions", "Visualizations & Insights"])

# ====================== Dynamic Material Emissions ============================
with tab1:
    st.header("Dynamic CO2 Emissions Based on Material Selection")
    materials = dynamic_data['Material'].unique()
    material_table_rows = []
    
    for material in materials:
        with st.expander(f"Configure Emissions for {material}", expanded=False):
            material_data = dynamic_data[dynamic_data['Material'] == material]
            col1, col2, col3 = st.columns(3)
            
            # Product at Gate selection
            with col1:
                product_at_gate = st.selectbox(
                    f"Product at Gate for {material}",
                    material_data['Product at gate'].unique(),
                    key=f"product_{material}"
                )
            
            # Primary Input selection
            filtered_data = get_filtered_options(dynamic_data, material, product_at_gate)
            with col2:
                if not filtered_data.empty:
                    primary_input = st.selectbox(
                        f"Primary Input for {material}",
                        filtered_data['Primary input'].unique(),
                        key=f"primary_{material}"
                    )
            
            # Location selection
            with col3:
                if not filtered_data.empty:
                    location = st.selectbox(
                        f"Location for {material}",
                        get_filtered_options(dynamic_data, material, product_at_gate, primary_input)['Location'].unique(),
                        key=f"location_{material}"
                    )
            
            # Emission calculation
            if not filtered_data.empty:
                emission_factor = filtered_data[filtered_data['Location'] == location]['kg CO2-eq/kg material'].values[0]
                amount = st.number_input(f"Enter Amount (kg) for {material}", min_value=0.0, step=1.0, key=f"amount_{material}")
                total_emissions = amount * emission_factor
                
                st.metric(label=f"Total Emissions for {material}", value=f"{total_emissions:.2f} kg CO2-eq")
                material_table_rows.append({
                    "Material": material,
                    "Total Emissions (kg CO2-eq)": total_emissions
                })

    material_table = pd.DataFrame(material_table_rows)
    st.markdown("## Emission Summary for Materials")
    if not material_table.empty:
        st.dataframe(material_table)
        st.metric("Total Emissions from Materials", f"{material_table['Total Emissions (kg CO2-eq)'].sum():.2f} kg CO2-eq")
    else:
        st.warning("No emissions data available for materials.")

# ===================== Machine-Based Emissions ================================
with tab2:
    st.header("Machine-Based CO2 Emissions")
    country = st.selectbox("Select Country", electricity_df['country'].tolist())
    electricity_emission_factor = electricity_df[electricity_df['country'] == country]['co2kg/kwh'].values[0]
    
    num_machines = st.number_input("Number of Machines", min_value=1, max_value=10, value=1)
    machine_rows = []
    
    for i in range(num_machines):
        st.subheader(f"Machine {i + 1}")
        machine_name = st.text_input(f"Machine {i + 1} Name", key=f"name_{i}")
        electricity_usage = st.number_input(f"Electricity Usage (kWh) for {machine_name}", min_value=0.0, key=f"electricity_{i}")
        fuel_type = st.selectbox(f"Select Fuel for {machine_name}", fuel_df['fuel type'].tolist(), key=f"fuel_{i}")
        fuel_usage = st.number_input(f"Amount of {fuel_type} used (kg or liters)", min_value=0.0, key=f"fuel_usage_{i}")
        
        electricity_emission = electricity_usage * electricity_emission_factor
        fuel_emission_factor = fuel_df[fuel_df['fuel type'] == fuel_type]['kg of co2/kg or litre'].values[0]
        fuel_emission = fuel_usage * fuel_emission_factor
        
        machine_rows.append([machine_name, electricity_emission, fuel_emission])

    machines_df = pd.DataFrame(machine_rows, columns=['Machine Name', 'Electricity Emission (kg)', 'Fuel Emission (kg)'])
    machines_df['Total Emission (kg CO2-eq)'] = machines_df['Electricity Emission (kg)'] + machines_df['Fuel Emission (kg)']
    st.dataframe(machines_df)
    st.metric("Total Emissions from Machines", f"{machines_df['Total Emission (kg CO2-eq)'].sum():.2f} kg CO2-eq")

# ===================== Visualizations & Insights ==============================
with tab3:
    st.header("Visualizations & Emissions Insights")
    
    material_total = material_table['Total Emissions (kg CO2-eq)'].sum() if not material_table.empty else 0
    machine_total = machines_df['Total Emission (kg CO2-eq)'].sum() if not machines_df.empty else 0
    total_emissions = material_total + machine_total
    
    num_cells = st.number_input("Enter Number of Cells Made", min_value=1, step=1)
    emissions_per_cell = total_emissions / num_cells
    
    # Display Key Metrics
    st.metric("Total Emissions (All Sources)", f"{total_emissions:.2f} kg CO2-eq")
    st.metric("Emissions Per Cell", f"{emissions_per_cell:.2f} kg CO2-eq")
    
    # Bar Chart: Emissions by Source
    st.subheader("Bar Chart: Emissions by Source")
    fig1, ax1 = plt.subplots()
    ax1.bar(["Materials", "Machines"], [material_total, machine_total], color=['blue', 'green'])
    ax1.set_title("Total Emissions by Source")
    ax1.set_ylabel("Emissions (kg CO2-eq)")
    st.pyplot(fig1)

    # Pie Chart: Contribution Percentage
    st.subheader("Pie Chart: Contribution Percentage")
    fig2, ax2 = plt.subplots()
    ax2.pie([material_total, machine_total], labels=["Materials", "Machines"], autopct='%1.1f%%', startangle=90, colors=['blue', 'green'])
    ax2.set_title("Contribution to Total Emissions")
    st.pyplot(fig2)
    
    # Bar Chart: Emissions Per Cell
    st.subheader("Bar Chart: Emissions Per Cell")
    fig3, ax3 = plt.subplots()
    ax3.bar(["Materials", "Machines"], [material_total / num_cells, machine_total / num_cells], color=['blue', 'green'])
    ax3.set_title("Emissions Per Cell by Source")
    ax3.set_ylabel("Emissions (kg CO2-eq per cell)")
    st.pyplot(fig3)
